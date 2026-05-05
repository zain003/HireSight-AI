import { useEffect, useMemo, useRef, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import interviewService from '@/services/interviewService';

export default function InterviewPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState('');
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [lastScore, setLastScore] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [conversationState, setConversationState] = useState('idle'); // idle, asking, listening, processing
  const [faceRegistered, setFaceRegistered] = useState(false);

  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const recognitionRef = useRef(null);
  const ttsAudioRef = useRef(null);
  const autoStartedRef = useRef(false);
  const silenceTimerRef = useRef(null);
  const recordingStartTimeRef = useRef(null);

  const currentQuestion = useMemo(
    () => questions[currentIdx] || null,
    [questions, currentIdx]
  );

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    return () => {
      stopQuestionSpeech();
      stopListening();
      cleanupMedia();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const cleanupMedia = () => {
    if (mediaStreamRef.current) {
      mediaStreamRef.current.getTracks().forEach((track) => track.stop());
      mediaStreamRef.current = null;
    }
    if (videoRef.current) {
      videoRef.current.srcObject = null;
    }
  };

  const stopQuestionSpeech = () => {
    if (ttsAudioRef.current) {
      ttsAudioRef.current.pause();
      ttsAudioRef.current = null;
    }
    if (typeof window !== 'undefined' && window.speechSynthesis) {
      window.speechSynthesis.cancel();
    }
    setIsSpeakingQuestion(false);
  };

  const playAudioFromBase64 = (base64Data) => {
    if (!base64Data) return;
    const audio = new Audio(`data:audio/mp3;base64,${base64Data}`);
    ttsAudioRef.current = audio;
    audio.onended = () => {
      setIsSpeakingQuestion(false);
      setConversationState('listening');
      startListening();
    };
    audio.onerror = () => {
      setIsSpeakingQuestion(false);
      setConversationState('listening');
      startListening();
    };
    audio.play();
  };

  const speakQuestion = async (text) => {
    if (!text) return;
    stopQuestionSpeech();
    setIsSpeakingQuestion(true);
    setConversationState('asking');

    try {
      const tts = await interviewService.tts(text);
      if (tts?.audio_base64) {
        playAudioFromBase64(tts.audio_base64);
        return;
      }
    } catch {
      // Fallback to browser TTS
    }

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(text);
      utterance.rate = 0.96;
      utterance.pitch = 1.0;
      utterance.lang = 'en-US';
      utterance.onend = () => {
        setIsSpeakingQuestion(false);
        setConversationState('listening');
        startListening();
      };
      utterance.onerror = () => {
        setIsSpeakingQuestion(false);
        setConversationState('listening');
        startListening();
      };
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeakingQuestion(false);
      setConversationState('listening');
      startListening();
    }
  };

  const initializeMedia = async () => {
    try {
      const stream = await navigator.mediaDevices.getUserMedia({
        audio: {
          channelCount: 1,
          sampleRate: 16000,
          echoCancellation: true,
          noiseSuppression: true,
          autoGainControl: true,
        },
        video: {
          width: { ideal: 1280 },
          height: { ideal: 720 },
          facingMode: 'user'
        },
      });

      mediaStreamRef.current = stream;
      if (videoRef.current) {
        videoRef.current.srcObject = stream;
        // Wait for video to be ready
        await new Promise((resolve) => {
          videoRef.current.onloadedmetadata = () => {
            videoRef.current.play();
            resolve();
          };
        });
      }

      // Auto-register face on first frame
      if (!faceRegistered && sessionId) {
        setTimeout(() => registerFaceAutomatically(), 1500);
      }

      return true;
    } catch (err) {
      console.error('Media initialization error:', err);
      setError('Camera/microphone access denied. Please allow access to continue.');
      return false;
    }
  };

  const registerFaceAutomatically = async () => {
    if (!sessionId || faceRegistered) return;
    try {
      const frame = await captureFrame();
      if (!frame) return;
      const base64 = await blobToBase64(frame);
      const result = await interviewService.registerFace(sessionId, base64);
      if (result?.registered) {
        setFaceRegistered(true);
      }
    } catch (err) {
      console.error('Face registration failed:', err);
    }
  };

  const startListening = () => {
    if (!('webkitSpeechRecognition' in window) && !('SpeechRecognition' in window)) {
      setError('Speech recognition not supported in this browser. Please use Chrome.');
      return;
    }

    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    const recognition = new SpeechRecognition();
    
    recognition.continuous = true;
    recognition.interimResults = true;
    recognition.lang = 'en-US';

    recognition.onstart = () => {
      setIsListening(true);
      setLiveTranscript('');
      setFinalTranscript('');
      audioChunksRef.current = [];
      recordingStartTimeRef.current = Date.now();
      resetSilenceTimer();
    };

    recognition.onresult = (event) => {
      let interim = '';
      let final = '';

      for (let i = event.resultIndex; i < event.results.length; i++) {
        const transcript = event.results[i][0].transcript;
        if (event.results[i].isFinal) {
          final += transcript + ' ';
        } else {
          interim += transcript;
        }
      }

      if (final) {
        setFinalTranscript((prev) => prev + final);
        setLiveTranscript('');
        resetSilenceTimer();
      } else {
        setLiveTranscript(interim);
      }
    };

    recognition.onerror = (event) => {
      console.error('Speech recognition error:', event.error);
      if (event.error !== 'no-speech') {
        setIsListening(false);
      }
    };

    recognition.onend = () => {
      // Only auto-restart if still in listening state and not loading
      if (conversationState === 'listening' && !loading && recognitionRef.current) {
        try {
          recognition.start();
        } catch (err) {
          console.error('Failed to restart recognition:', err);
          setIsListening(false);
        }
      } else {
        setIsListening(false);
      }
    };

    recognitionRef.current = recognition;
    recognition.start();
  };

  const resetSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
    // No auto-submit - user must click submit button
  };

  const stopListening = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (recognitionRef.current) {
      recognitionRef.current.stop();
      recognitionRef.current = null;
    }
    setIsListening(false);
  };

  const captureFrame = () =>
    new Promise((resolve) => {
      const video = videoRef.current;
      if (!video || !video.videoWidth || !video.videoHeight) {
        console.error('Video not ready:', { 
          video: !!video, 
          width: video?.videoWidth, 
          height: video?.videoHeight 
        });
        resolve(null);
        return;
      }

      try {
        const canvas = document.createElement('canvas');
        canvas.width = video.videoWidth;
        canvas.height = video.videoHeight;

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          console.error('Could not get canvas context');
          resolve(null);
          return;
        }

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (blob) {
            console.log('Frame captured successfully:', blob.size, 'bytes');
            resolve(blob);
          } else {
            console.error('Failed to create blob from canvas');
            resolve(null);
          }
        }, 'image/jpeg', 0.9);
      } catch (err) {
        console.error('Error capturing frame:', err);
        resolve(null);
      }
    });

  const blobToBase64 = (blob) =>
    new Promise((resolve, reject) => {
      if (!blob) {
        resolve('');
        return;
      }
      const reader = new FileReader();
      reader.onloadend = () => {
        const result = reader.result || '';
        const base64 = typeof result === 'string' ? result.split(',')[1] || '' : '';
        resolve(base64);
      };
      reader.onerror = () => reject(new Error('Failed to read blob'));
      reader.readAsDataURL(blob);
    });

  const startInterview = async (jobPostId = null) => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        num_questions: 8,
        ...(jobPostId ? { job_post_id: jobPostId } : {}),
      };
      const data = await interviewService.startSession(payload);
      setSessionId(data.session_id);
      setQuestions(data.questions || []);
      setCurrentIdx(0);
      setLastScore(null);
      setReport(null);
      setFaceRegistered(false);

      // Initialize media and start first question
      const mediaReady = await initializeMedia();
      if (mediaReady && data.questions?.length > 0) {
        setTimeout(() => speakQuestion(data.questions[0].question_text), 500);
      }
    } catch (err) {
      setError(err.response?.data?.detail || 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!router.isReady || !authService.isAuthenticated()) return;
    if (sessionId || autoStartedRef.current) return;

    const queryJobPostId = router.query.jobPostId;
    if (!queryJobPostId || Array.isArray(queryJobPostId)) return;

    autoStartedRef.current = true;
    startInterview(queryJobPostId);
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router.isReady, router.query.jobPostId, sessionId]);

  const handleSubmitAnswer = () => {
    const transcript = finalTranscript.trim();
    if (!transcript) {
      setError('Please speak your answer before submitting.');
      return;
    }
    submitAnswer(transcript);
  };

  const submitAnswer = async (transcript) => {
    if (!sessionId || !currentQuestion || !transcript) return;

    stopListening();
    setConversationState('processing');
    setLoading(true);
    setError('');

    try {
      // Wait a moment for video to stabilize
      await new Promise(resolve => setTimeout(resolve, 100));
      
      const frame = await captureFrame();
      if (!frame) {
        setError('Could not capture video frame. Please ensure your camera is working.');
        setLoading(false);
        setConversationState('listening');
        startListening();
        return;
      }

      const frameBase64 = await blobToBase64(frame);

      // Create a dummy audio blob (since we're using transcript from speech recognition)
      const dummyAudio = new Blob([new ArrayBuffer(44)], { type: 'audio/wav' });
      const audioBase64 = await blobToBase64(dummyAudio);

      const payload = {
        question_index: currentIdx,
        audio_base64: audioBase64,
        transcript_text: transcript,
        audio_format: 'wav',
        language: 'en',
        frame_base64_list: frameBase64 ? [frameBase64] : [],
      };

      console.log('Submitting answer for question', currentIdx + 1);
      const score = await interviewService.submitAnswer(sessionId, payload);
      console.log('Answer submitted successfully, score:', score);

      setLastScore({
        ...score,
        details: {
          transcript: score.transcript,
          evaluation: score.evaluation,
        },
      });

      // Clear transcripts for next question
      setLiveTranscript('');
      setFinalTranscript('');

      // Handle follow-up questions
      let updatedQuestions = [...questions];
      if (score.follow_up_question) {
        updatedQuestions.splice(currentIdx + 1, 0, score.follow_up_question);
        setQuestions(updatedQuestions);
      }

      // Check if there are more questions
      const hasMoreQuestions = currentIdx < updatedQuestions.length - 1;
      
      if (hasMoreQuestions) {
        const nextIdx = currentIdx + 1;
        console.log('Moving to question', nextIdx + 1, 'of', updatedQuestions.length);
        setCurrentIdx(nextIdx);
        
        // Ask next question after a brief pause
        setTimeout(() => {
          const nextQ = updatedQuestions[nextIdx];
          if (nextQ) {
            console.log('Speaking next question:', nextQ.question_text);
            speakQuestion(nextQ.question_text);
          }
        }, 1500);
      } else {
        // End interview
        console.log('Interview complete, fetching final report');
        const finalReport = await interviewService.endSession(sessionId);
        setReport(finalReport);
        setConversationState('idle');
        stopListening();
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
      setError(err.response?.data?.detail || 'Failed to evaluate answer');
      setConversationState('listening');
      startListening();
    } finally {
      setLoading(false);
    }
  };

  const displayTranscript = finalTranscript + (liveTranscript ? ' ' + liveTranscript : '');

  return (
    <div className="min-h-screen bg-white">
      <main className="container mx-auto px-6 py-10 space-y-6">
        <div className="border border-deep-night/10 p-5 bg-white">
          <h1 className="text-xl font-semibold text-deep-night">Live Interview Session</h1>
          <p className="text-xs text-text-muted mt-1">
            Real-time AI interview with continuous conversation flow
          </p>
        </div>

        {!sessionId && (
          <button
            onClick={() => startInterview(router.query.jobPostId)}
            disabled={loading}
            className="neon-btn px-5 py-2 text-sm font-semibold"
          >
            {loading ? 'Starting...' : 'Start Interview'}
          </button>
        )}

        {error && (
          <div className="border border-red-300 bg-red-50 text-red-700 text-sm p-3">
            {error}
          </div>
        )}

        {sessionId && currentQuestion && !report && (
          <div className="grid gap-6 md:grid-cols-2">
            {/* Left: Video and Status */}
            <div className="space-y-4">
              <div className="border border-deep-night/10 p-4 bg-white">
                <p className="text-xs font-medium text-deep-night mb-2">Live Camera</p>
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                  className="w-full h-64 bg-black/80 object-cover border border-deep-night/20"
                />
                
                {/* Status Indicator */}
                <div className="mt-3 flex items-center gap-3">
                  <div className="flex items-center gap-2">
                    <div className={`w-3 h-3 rounded-full ${
                      conversationState === 'asking' ? 'bg-blue-500 animate-pulse' :
                      conversationState === 'listening' ? 'bg-green-500 animate-pulse' :
                      conversationState === 'processing' ? 'bg-yellow-500 animate-pulse' :
                      'bg-gray-300'
                    }`} />
                    <span className="text-xs font-medium text-deep-night">
                      {conversationState === 'asking' && 'AI is asking...'}
                      {conversationState === 'listening' && 'Listening to your answer...'}
                      {conversationState === 'processing' && 'Processing your response...'}
                      {conversationState === 'idle' && 'Ready'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Current Question */}
              <div className="border border-deep-night/10 p-4 bg-white">
                <p className="text-[11px] uppercase tracking-wider text-text-muted mb-2">
                  Question {currentIdx + 1} of {questions.length} · {currentQuestion.question_type}
                </p>
                <p className="text-base text-deep-night font-medium">
                  {currentQuestion.question_text}
                </p>
              </div>
            </div>

            {/* Right: Live Transcript */}
            <div className="space-y-4">
              <div className="border border-deep-night/10 p-4 bg-white h-full">
                <p className="text-xs font-medium text-deep-night mb-3">
                  Your Answer (Live Transcript)
                </p>
                <div className="min-h-[300px] max-h-[400px] overflow-y-auto p-3 bg-surface-subtle border border-deep-night/10">
                  {displayTranscript ? (
                    <p className="text-sm text-deep-night whitespace-pre-wrap">
                      {displayTranscript}
                      {liveTranscript && (
                        <span className="text-text-muted italic"> (speaking...)</span>
                      )}
                    </p>
                  ) : (
                    <p className="text-sm text-text-muted italic">
                      {conversationState === 'listening' 
                        ? 'Start speaking your answer...' 
                        : 'Waiting for question...'}
                    </p>
                  )}
                </div>
                
                {conversationState === 'listening' && displayTranscript && (
                  <button
                    onClick={handleSubmitAnswer}
                    disabled={loading || !displayTranscript.trim()}
                    className="neon-btn px-4 py-2 text-sm font-semibold mt-3 w-full"
                  >
                    {loading ? 'Submitting...' : 'Submit Answer'}
                  </button>
                )}
                
                {conversationState === 'listening' && (
                  <p className="text-xs text-text-muted mt-2">
                    💡 Tip: Speak your answer, then click Submit when ready
                  </p>
                )}
              </div>
            </div>
          </div>
        )}

        {lastScore && !report && (
          <div className="border border-deep-night/10 p-4 bg-surface-subtle text-sm space-y-2">
            <h3 className="font-semibold text-deep-night">Previous Answer Evaluation</h3>
            <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
              <div>
                <p className="text-xs text-text-muted">Overall Score</p>
                <p className="text-lg font-bold text-neon-violet">{lastScore.per_answer_score}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Relevance</p>
                <p className="text-lg font-bold">{lastScore.evaluation?.relevance_score}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Depth</p>
                <p className="text-lg font-bold">{lastScore.evaluation?.depth_score}</p>
              </div>
              <div>
                <p className="text-xs text-text-muted">Communication</p>
                <p className="text-lg font-bold">{lastScore.evaluation?.communication_score}</p>
              </div>
            </div>
          </div>
        )}

        {report && (
          <div className="border border-deep-night/10 p-5 bg-white space-y-4">
            <h2 className="text-xl font-semibold text-deep-night">Interview Complete! 🎉</h2>
            <div className="grid grid-cols-2 md:grid-cols-3 gap-4">
              <div className="p-3 bg-surface-subtle border border-deep-night/10">
                <p className="text-xs text-text-muted">Overall Score</p>
                <p className="text-2xl font-bold text-neon-violet">{report.aggregate_scores?.overall_score}</p>
              </div>
              <div className="p-3 bg-surface-subtle border border-deep-night/10">
                <p className="text-xs text-text-muted">Technical</p>
                <p className="text-2xl font-bold">{report.aggregate_scores?.technical_score}</p>
              </div>
              <div className="p-3 bg-surface-subtle border border-deep-night/10">
                <p className="text-xs text-text-muted">Behavioral</p>
                <p className="text-2xl font-bold">{report.aggregate_scores?.behavioral_score}</p>
              </div>
              <div className="p-3 bg-surface-subtle border border-deep-night/10">
                <p className="text-xs text-text-muted">Communication</p>
                <p className="text-2xl font-bold">{report.aggregate_scores?.communication_score}</p>
              </div>
              <div className="p-3 bg-surface-subtle border border-deep-night/10">
                <p className="text-xs text-text-muted">Video Integrity</p>
                <p className="text-2xl font-bold">{report.aggregate_scores?.video_integrity_score}</p>
              </div>
            </div>
            <div className="p-4 bg-neon-violet/5 border border-neon-violet/20">
              <p className="text-xs text-text-muted mb-1">Recommendation</p>
              <p className="text-base font-semibold text-deep-night">{report.report?.recommendation}</p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="neon-btn px-5 py-2 text-sm font-semibold"
            >
              Back to Dashboard
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
