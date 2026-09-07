import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import interviewService from '@/services/interviewService';
import { formatApiDetail } from '@/utils/formatApiDetail';
import InputModeSelector from '@/components/Interview/InputModeSelector';
import { Sparkles, FileText, CheckCircle2, ChevronDown, ChevronUp, Lightbulb, RefreshCw } from 'lucide-react';

const CodingWorkspace = dynamic(
  () => import('@/components/Interview/CodingWorkspace'),
  {
    ssr: false,
    loading: () => (
      <div className="flex min-h-[380px] items-center justify-center rounded-xl border border-white/15 bg-[#1a1b26] text-sm text-slate-400 ring-1 ring-white/5">
        Loading code editor…
      </div>
    ),
  }
);

/** Sent to the API so the session advances; backend uses transcript_text when non-empty. */
const SKIP_QUESTION_TRANSCRIPT =
  '[Skipped] Candidate chose to skip this question. No verbal answer was provided.';

export default function InterviewPage() {
  const router = useRouter();
  const [sessionId, setSessionId] = useState('');
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [liveTranscript, setLiveTranscript] = useState('');
  const [finalTranscript, setFinalTranscript] = useState('');
  const [inputMode, setInputMode] = useState('voice'); // 'voice' | 'text'
  const [textAnswer, setTextAnswer] = useState('');
  const [showStarGuidance, setShowStarGuidance] = useState(false);
  const [lastScore, setLastScore] = useState(null);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [isListening, setIsListening] = useState(false);
  const [isSpeakingQuestion, setIsSpeakingQuestion] = useState(false);
  const [conversationState, setConversationState] = useState('idle'); // idle, asking, listening, processing
  const [faceRegistered, setFaceRegistered] = useState(false);
  const [jobRoleLabel, setJobRoleLabel] = useState('Interview');
  const [elapsedSec, setElapsedSec] = useState(0);
  const [micMuted, setMicMuted] = useState(false);
  const [cameraOff, setCameraOff] = useState(false);
  const [audioLevel, setAudioLevel] = useState(0);
  const [speechNotice, setSpeechNotice] = useState(null);

  const videoRef = useRef(null);
  const mediaStreamRef = useRef(null);
  const audioChunksRef = useRef([]);
  const mediaRecorderRef = useRef(null);
  const audioContextRef = useRef(null);
  const analyserRef = useRef(null);
  const animFrameRef = useRef(null);
  const accumulatedFinalRef = useRef('');
  const finalTranscriptRef = useRef(finalTranscript);
  const liveTranscriptionIntervalRef = useRef(null);
  const isTranscribingChunkRef = useRef(false);
  const webSpeechDisabledRef = useRef(false);
  const recognitionRef = useRef(null);
  const restartListeningTimeoutRef = useRef(null);
  const ttsAudioRef = useRef(null);
  const autoStartedRef = useRef(false);
  const silenceTimerRef = useRef(null);
  const recordingStartTimeRef = useRef(null);
  const conversationStateRef = useRef(conversationState);
  const loadingRef = useRef(loading);
  const micMutedRef = useRef(micMuted);
  const inputModeRef = useRef(inputMode);
  /** When true, TTS end does not start Web Speech (so Monaco can receive keyboard input). */
  const skipSpeechListenAfterRef = useRef(false);

  const currentQuestion = useMemo(
    () => questions[currentIdx] || null,
    [questions, currentIdx]
  );

  /** Phase order: introduction → technical → deep_dive → coding → behavioral → closing */
  const stageOrder = useMemo(
    () => ['introduction', 'technical', 'deep_dive', 'coding', 'behavioral', 'closing'],
    []
  );

  const resolveStageFromQuestion = useCallback(
    (question, idx) => {
      if (!question) return 'introduction';
      const explicit = (question?.stage || '').toLowerCase().trim();
      const type = (question?.question_type || '').toLowerCase().trim();

      const normalize = (val) => {
        if (!val) return '';
        if (val === 'icebreaker' || val === 'intro' || val === 'introduction') return 'introduction';
        if (val === 'core_technical' || val === 'technical' || val === 'tech') return 'technical';
        if (val === 'behavioral' || val === 'situational' || val === 'star') return 'behavioral';
        if (val === 'deep_dive' || val === 'cv_based' || val === 'system_design' || val === 'architecture') return 'deep_dive';
        if (val === 'coding' || val === 'code_sandbox') return 'coding';
        if (val === 'closing' || val === 'wrap_up' || val === 'conclusion') return 'closing';
        return '';
      };

      const fromExplicit = normalize(explicit);
      if (fromExplicit) return fromExplicit;

      const fromType = normalize(type);
      if (fromType) return fromType;

      if (question?.coding_challenge) return 'coding';

      if ((type === 'follow_up' || explicit === 'follow_up') && idx > 0) {
        for (let i = idx - 1; i >= 0; i -= 1) {
          const prev = questions[i];
          const prevNorm = normalize(prev?.stage) || normalize(prev?.question_type);
          if (prevNorm) return prevNorm;
        }
      }

      return 'introduction';
    },
    [questions]
  );

  const stageLimits = useMemo(() => {
    const counts = {
      introduction: 0,
      technical: 0,
      behavioral: 0,
      deep_dive: 0,
      coding: 0,
      closing: 0,
    };
    questions.forEach((q, i) => {
      if ((q?.question_type || '').toLowerCase() === 'follow_up') return;
      const s = resolveStageFromQuestion(q, i);
      if (counts[s] !== undefined) counts[s] += 1;
    });
    return counts;
  }, [questions, resolveStageFromQuestion]);

  const currentStageKey = useMemo(() => {
    return resolveStageFromQuestion(currentQuestion, currentIdx);
  }, [currentQuestion, currentIdx, resolveStageFromQuestion]);

  const isCodingPhase = useMemo(
    () => currentStageKey === 'coding' || (currentQuestion?.question_type || '').toLowerCase() === 'coding' || !!currentQuestion?.coding_challenge,
    [currentStageKey, currentQuestion]
  );

  const currentStageLabel = useMemo(() => {
    const stage = currentStageKey;
    if (stage === 'introduction') return 'Introduction & Background';
    if (stage === 'technical') return 'Core Technical Competency';
    if (stage === 'behavioral') return 'Behavioral & STAR Scenario';
    if (stage === 'deep_dive') return 'System Architecture & Deep Dive';
    if (stage === 'coding') return 'Coding Sandbox Assessment';
    if (stage === 'closing') return 'Engineering Practices & Wrap-up';
    return 'Technical Interview';
  }, [currentStageKey]);

  const currentStageIndex = useMemo(
    () => Math.max(1, stageOrder.indexOf(currentStageKey) + 1),
    [currentStageKey, stageOrder]
  );

  const stageQuestionTotal = stageLimits[currentStageKey] || 1;

  const stageQuestionNumber = useMemo(() => {
    const n = questions.slice(0, currentIdx + 1).filter((q, i) => {
        const qType = (q?.question_type || '').toLowerCase();
      if (qType === 'follow_up') return false;
        return resolveStageFromQuestion(q, i) === currentStageKey;
      }).length;
    return Math.max(1, n);
  }, [questions, currentIdx, currentStageKey, resolveStageFromQuestion]);

  const overallBaseTotal = useMemo(
    () =>
      questions.filter(
        (q) => (q?.question_type || '').toLowerCase() !== 'follow_up'
      ).length,
    [questions]
  );

  const overallBaseNumber = useMemo(() => {
    const n = questions
      .slice(0, currentIdx + 1)
      .filter((q) => (q?.question_type || '').toLowerCase() !== 'follow_up').length;
    return Math.max(1, n);
  }, [questions, currentIdx]);

  const isFollowUpQuestion = useMemo(() => {
    if (!currentQuestion) return false;
    const qType = (currentQuestion.question_type || '').toLowerCase();
    const stage = (currentQuestion.stage || '').toLowerCase();
    return Boolean(
      currentQuestion.parent_question_id ||
        qType === 'follow_up' ||
        stage === 'follow_up'
    );
  }, [currentQuestion]);

  const displayTranscript = useMemo(() => {
    if (finalTranscript && liveTranscript) {
      return `${finalTranscript} ${liveTranscript}`;
    }
    return finalTranscript || liveTranscript || '';
  }, [finalTranscript, liveTranscript]);

  const clearTranscript = useCallback(() => {
    setFinalTranscript('');
    setLiveTranscript('');
  }, []);

  const handleInputModeChange = useCallback(
    (newMode) => {
      if (newMode === inputMode) return;
      if (newMode === 'text') {
        stopListening();
        const currentVoiceText = (
          finalTranscript + (liveTranscript ? ' ' + liveTranscript : '')
        ).trim();
        if (currentVoiceText && !textAnswer.trim()) {
          setTextAnswer(currentVoiceText);
        }
      } else if (newMode === 'voice') {
        if (textAnswer.trim() && !finalTranscript.trim()) {
          setFinalTranscript(textAnswer.trim());
        }
        if (conversationStateRef.current === 'listening' && !micMutedRef.current) {
          startListening();
        }
      }
      setInputMode(newMode);
    },
    [
      inputMode,
      finalTranscript,
      liveTranscript,
      textAnswer,
    ]
  );

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
    }
  }, [router]);

  useEffect(() => {
    if (!authService.isAuthenticated()) return;
    authService
      .getProfile()
      .then((p) => {
        if (p?.job_role) setJobRoleLabel(p.job_role);
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (!sessionId || !currentQuestion) return;
    setElapsedSec(0);
    const id = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [sessionId, currentIdx, currentQuestion?.question_id]);

  useEffect(() => {
    finalTranscriptRef.current = finalTranscript;
  }, [finalTranscript]);

  useEffect(() => {
    conversationStateRef.current = conversationState;
  }, [conversationState]);

  useEffect(() => {
    loadingRef.current = loading;
  }, [loading]);

  useEffect(() => {
    inputModeRef.current = inputMode;
  }, [inputMode]);

  useEffect(() => {
    accumulatedFinalRef.current = '';
    setSpeechNotice(null);
    setLiveTranscript('');
    setFinalTranscript('');
    setTextAnswer('');
    audioChunksRef.current = [];
  }, [currentIdx, sessionId]);

  useEffect(() => {
    return () => {
      stopQuestionSpeech();
      stopListening();
      cleanupMedia();
    };
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  useEffect(() => {
    if (isCodingPhase) {
      stopListening();
    }
  }, [isCodingPhase, currentIdx]);

  const cleanupMedia = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => {});
      audioContextRef.current = null;
    }
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
      if (conversationStateRef.current === 'processing') return;
      conversationStateRef.current = 'listening';
      setConversationState('listening');
      if (skipSpeechListenAfterRef.current) return;
      if (!micMutedRef.current && inputModeRef.current === 'voice') startListening();
    };
    audio.onerror = () => {
      setIsSpeakingQuestion(false);
      if (conversationStateRef.current === 'processing') return;
      conversationStateRef.current = 'listening';
      setConversationState('listening');
      if (skipSpeechListenAfterRef.current) return;
      if (!micMutedRef.current && inputModeRef.current === 'voice') startListening();
    };
    audio.play().catch((err) => {
      console.warn('Audio autoplay prevented or failed:', err);
      setIsSpeakingQuestion(false);
      if (conversationStateRef.current !== 'processing') {
        conversationStateRef.current = 'listening';
        setConversationState('listening');
        if (!skipSpeechListenAfterRef.current && !micMutedRef.current && inputModeRef.current === 'voice') {
          startListening();
        }
      }
    });
  };

  const speakQuestion = async (text, metaQuestion = null) => {
    if (!text) return;
    const isCodingQ =
      metaQuestion &&
      ((metaQuestion.question_type || '').toLowerCase() === 'coding' ||
        (metaQuestion.stage || '').toLowerCase() === 'coding');
    skipSpeechListenAfterRef.current = !!isCodingQ;

    stopQuestionSpeech();
    stopListening();
    setIsSpeakingQuestion(true);
    conversationStateRef.current = 'asking';
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
        if (conversationStateRef.current === 'processing') return;
        conversationStateRef.current = 'listening';
        setConversationState('listening');
        if (skipSpeechListenAfterRef.current) return;
        if (!micMutedRef.current && inputModeRef.current === 'voice') startListening();
      };
      utterance.onerror = () => {
        setIsSpeakingQuestion(false);
        if (conversationStateRef.current === 'processing') return;
        conversationStateRef.current = 'listening';
        setConversationState('listening');
        if (skipSpeechListenAfterRef.current) return;
        if (!micMutedRef.current && inputModeRef.current === 'voice') startListening();
      };
      window.speechSynthesis.speak(utterance);
    } else {
      setIsSpeakingQuestion(false);
      if (conversationStateRef.current !== 'processing') {
        conversationStateRef.current = 'listening';
        setConversationState('listening');
        if (!skipSpeechListenAfterRef.current && !micMutedRef.current && inputModeRef.current === 'voice') {
          startListening();
        }
      }
    }
  };

  const initializeMedia = async () => {
    try {
      let stream = null;
      try {
        stream = await navigator.mediaDevices.getUserMedia({
          audio: {
            echoCancellation: true,
            noiseSuppression: true,
            autoGainControl: true,
          },
          video: {
            width: { ideal: 1280 },
            height: { ideal: 720 },
            facingMode: 'user',
          },
        });
      } catch (combinedErr) {
        console.warn('Combined media constraints failed, attempting fallback:', combinedErr);
        // Fallback: try basic audio + video, or audio only
        try {
          const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          let videoStream = null;
          try {
            videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
          } catch {
            console.warn('Camera not available, proceeding with audio only');
          }

          if (videoStream) {
            stream = new MediaStream([
              ...audioStream.getAudioTracks(),
              ...videoStream.getVideoTracks(),
            ]);
          } else {
            stream = audioStream;
          }
        } catch (audioErr) {
          throw new Error('Microphone access is required for live voice interview.');
        }
      }

      mediaStreamRef.current = stream;
      setError('');

      if (videoRef.current && stream.getVideoTracks().length > 0) {
        videoRef.current.srcObject = stream;
        try {
          await new Promise((resolve) => {
            videoRef.current.onloadedmetadata = () => {
              videoRef.current.play().catch(() => {});
              resolve();
            };
            setTimeout(resolve, 1000);
          });
        } catch {}
      }

      // Initialize Live Audio Meter
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx && stream.getAudioTracks().length > 0) {
          if (audioContextRef.current) {
            audioContextRef.current.close().catch(() => {});
          }
          const audioCtx = new AudioCtx();
          const analyser = audioCtx.createAnalyser();
          analyser.fftSize = 128;
          analyser.smoothingTimeConstant = 0.5;
          const source = audioCtx.createMediaStreamSource(stream);
          source.connect(analyser);

          audioContextRef.current = audioCtx;
          analyserRef.current = analyser;

          const dataArray = new Uint8Array(analyser.frequencyBinCount);
          const updateMeter = () => {
            if (analyserRef.current) {
              analyserRef.current.getByteFrequencyData(dataArray);
              let sum = 0;
              for (let i = 0; i < dataArray.length; i++) {
                sum += dataArray[i];
              }
              const avg = sum / dataArray.length;
              setAudioLevel(Math.min(100, Math.round(avg * 2.5)));
            }
            animFrameRef.current = requestAnimationFrame(updateMeter);
          };
          updateMeter();
        }
      } catch (audioErr) {
        console.warn('Audio meter initialization warning:', audioErr);
      }

      // Auto-register face on first frame if video tracks exist
      if (!faceRegistered && sessionId && stream.getVideoTracks().length > 0) {
        setTimeout(() => registerFaceAutomatically(), 1500);
      }

      // If already in listening phase, start voice capture immediately
      if (
        conversationStateRef.current === 'listening' &&
        !micMutedRef.current &&
        inputModeRef.current === 'voice'
      ) {
        startListening();
      }

      return true;
    } catch (err) {
      console.error('Media initialization error:', err);
      setError('Microphone access required. Please allow microphone permissions to speak your answer.');
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

  const startListening = async () => {
    if (micMutedRef.current || inputModeRef.current !== 'voice') {
      setIsListening(false);
      return;
    }

    if (!mediaStreamRef.current) {
      const ready = await initializeMedia();
      if (!ready) return;
    }

    setIsListening(true);
    conversationStateRef.current = 'listening';
    setConversationState('listening');

    if (restartListeningTimeoutRef.current) {
      clearTimeout(restartListeningTimeoutRef.current);
      restartListeningTimeoutRef.current = null;
    }

    // 1. Start continuous MediaRecorder to capture candidate voice
    const audioTracks = mediaStreamRef.current ? mediaStreamRef.current.getAudioTracks() : [];
    if (audioTracks.length > 0) {
      try {
        audioTracks.forEach((t) => {
          t.enabled = true;
        });

        if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
          // Reset chunks for fresh WebM container header
          audioChunksRef.current = [];
          // Isolate audio tracks to prevent MediaRecorder crashing on mixed video+audio streams
          const audioOnlyStream = new MediaStream(audioTracks);
          const types = [
            'audio/webm;codecs=opus',
            'audio/webm',
            'audio/ogg;codecs=opus',
            'audio/ogg',
            'audio/mp4',
            'audio/wav',
          ];
          const mimeType = types.find((t) => typeof MediaRecorder !== 'undefined' && MediaRecorder.isTypeSupported && MediaRecorder.isTypeSupported(t)) || '';
          const mr = mimeType
            ? new MediaRecorder(audioOnlyStream, { mimeType })
            : new MediaRecorder(audioOnlyStream);

          mr.ondataavailable = (e) => {
            if (e.data && e.data.size > 0) {
              audioChunksRef.current.push(e.data);
            }
          };
          mr.start(250);
          mediaRecorderRef.current = mr;
        }
      } catch (mrErr) {
        console.warn('MediaRecorder init notice:', mrErr);
      }
    }

    // 2. Start background live Whisper transcription interval (3.5s cadence to stay safely within RPM quota)
    if (!liveTranscriptionIntervalRef.current) {
      liveTranscriptionIntervalRef.current = setInterval(async () => {
        if (
          !loadingRef.current &&
          !micMutedRef.current &&
          inputModeRef.current === 'voice' &&
          !isTranscribingChunkRef.current
        ) {
          try {
            if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
              try {
                mediaRecorderRef.current.requestData();
              } catch {}
            }

            if (audioChunksRef.current && audioChunksRef.current.length > 2) {
              const mime = audioChunksRef.current[0]?.type || 'audio/webm';
              const audioBlob = new Blob(audioChunksRef.current, { type: mime });
              // Only call Whisper if candidate has spoken at least ~1.5s of audio (avoids hallucinating on initial silence)
              if (audioBlob.size > 2000) {
                isTranscribingChunkRef.current = true;
                const b64 = await blobToBase64(audioBlob);
                const fmt = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm';
                const text = await interviewService.transcribeAudio(b64, fmt, 'en');
                const isHallucination = (str) => {
                  if (!str) return true;
                  const s = str.trim().toLowerCase();
                  const cleaned = s.replace(/[^\w\s]/g, '').trim();
                  if (!cleaned) return true;
                  const words = cleaned.split(/\s+/);
                  const hallucinationTokens = new Set([
                    'thank', 'thanks', 'you', 'very', 'much', 'watching', 'for', 'please',
                    'subscribe', 'subtitles', 'by', 'amara', 'org', 'bye', 'bell', 'icon',
                    'like', 'share', 'comment', 'video', 'channel', 'next', 'time'
                  ]);
                  if (words.every((w) => hallucinationTokens.has(w))) return true;
                  for (let n = 1; n <= 4; n++) {
                    if (words.length >= n * 2) {
                      const chunk = words.slice(0, n).join(' ');
                      let isRepeating = true;
                      for (let i = 0; i < words.length; i += n) {
                        const slice = words.slice(i, i + n).join(' ');
                        if (slice !== chunk && !chunk.startsWith(slice)) {
                          isRepeating = false;
                          break;
                        }
                      }
                      if (isRepeating) return true;
                    }
                  }
                  return false;
                };

                if (text && text !== '[Could not transcribe audio]' && !isHallucination(text) && text.trim().length > 0) {
                  const cleanedText = text.trim();
                  setFinalTranscript((prev) => {
                    if (prev && prev.length > cleanedText.length && !webSpeechDisabledRef.current) {
                      return prev;
                    }
                    return cleanedText;
                  });
                  accumulatedFinalRef.current = cleanedText;
                  setLiveTranscript('');
                  setSpeechNotice(null);
                }
              }
            }
          } catch (e) {
            console.warn('Live transcribe chunk notice:', e);
          } finally {
            isTranscribingChunkRef.current = false;
          }
        }
      }, 3500);
    }

    // 3. Start Browser Web Speech Recognition (for instant local text preview)
    if (typeof window === 'undefined') return;
    if (webSpeechDisabledRef.current) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechNotice(
        'Speech captured directly via high-accuracy backend Whisper model.'
      );
      return;
    }

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onend = null;
          recognitionRef.current.onerror = null;
          recognitionRef.current.stop();
        } catch {}
        recognitionRef.current = null;
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = 'en-US';
      recognition.maxAlternatives = 1;

      recognition.onstart = () => {
        setIsListening(true);
        resetSilenceTimer();
      };

      recognition.onresult = (event) => {
        let interim = '';
        let finalizedThisSession = '';

        for (let i = 0; i < event.results.length; i++) {
          const item = event.results[i];
          if (item.isFinal) {
            finalizedThisSession += item[0].transcript + ' ';
          } else {
            interim += item[0].transcript;
          }
        }

        const base = accumulatedFinalRef.current ? accumulatedFinalRef.current + ' ' : '';
        const fullFinal = (base + finalizedThisSession).trim();
        if (fullFinal) {
          setFinalTranscript(fullFinal);
        }
        setLiveTranscript(interim);
        resetSilenceTimer();
      };

      recognition.onerror = (event) => {
        if (event.error === 'no-speech' || event.error === 'aborted') {
          return;
        }
        if (
          event.error === 'network' ||
          event.error === 'not-allowed' ||
          event.error === 'service-not-allowed' ||
          event.error === 'audio-capture'
        ) {
          webSpeechDisabledRef.current = true;
          setSpeechNotice(
            'Live speech captured and transcribed via Groq Whisper AI.'
          );
          return;
        }
        console.warn('Speech recognition notice:', event.error);
      };

      recognition.onend = () => {
        if (finalTranscriptRef.current) {
          accumulatedFinalRef.current = finalTranscriptRef.current;
        }
        if (recognitionRef.current === recognition) {
          recognitionRef.current = null;
        }
        if (webSpeechDisabledRef.current) {
          return;
        }
        if (
          conversationStateRef.current === 'listening' &&
          !loadingRef.current &&
          !micMutedRef.current &&
          inputModeRef.current === 'voice'
        ) {
          if (restartListeningTimeoutRef.current) {
            clearTimeout(restartListeningTimeoutRef.current);
          }
          restartListeningTimeoutRef.current = setTimeout(() => {
            if (
              conversationStateRef.current === 'listening' &&
              !micMutedRef.current &&
              inputModeRef.current === 'voice' &&
              !webSpeechDisabledRef.current
            ) {
              try {
                recognition.start();
                recognitionRef.current = recognition;
              } catch (e) {
                // Whisper polling operates in parallel
              }
            }
          }, 200);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch (err) {
      console.warn('Speech recognition started in direct audio recording mode:', err);
    }
  };

  const resetSilenceTimer = () => {
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
    }
  };

  const stopListening = () => {
    if (liveTranscriptionIntervalRef.current) {
      clearInterval(liveTranscriptionIntervalRef.current);
      liveTranscriptionIntervalRef.current = null;
    }
    if (restartListeningTimeoutRef.current) {
      clearTimeout(restartListeningTimeoutRef.current);
      restartListeningTimeoutRef.current = null;
    }
    if (silenceTimerRef.current) {
      clearTimeout(silenceTimerRef.current);
      silenceTimerRef.current = null;
    }

    if (mediaRecorderRef.current && mediaRecorderRef.current.state !== 'inactive') {
      try {
        mediaRecorderRef.current.stop();
      } catch {
        // ignore
      }
      mediaRecorderRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.stop();
      } catch {
        // ignore
      }
      recognitionRef.current = null;
    }
    setIsListening(false);
    setLiveTranscript('');
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

  const recoverSessionState = async (targetSessionId) => {
    setLoading(true);
    setError('');
    try {
      const state = await interviewService.getSessionState(targetSessionId);
      if (!state) throw new Error('Could not fetch session state');

      setSessionId(state.session_id);

      // Check if session is already completed
      if (state.status === 'completed' || state.current_question_index >= state.total_questions) {
        try {
          const finalReport = await interviewService.getReport(targetSessionId);
          setReport(finalReport);
        } catch {
          try {
            const finalReport = await interviewService.endSession(targetSessionId);
            setReport(finalReport);
          } catch (endErr) {
            console.warn('Could not generate final report:', endErr);
          }
        }
        setLoading(false);
        return;
      }

      // Restore full questions curriculum from backend session state
      let loadedQuestions = [];
      if (Array.isArray(state.questions) && state.questions.length > 0) {
        loadedQuestions = state.questions;
      } else {
        const cached =
          typeof window !== 'undefined'
            ? sessionStorage.getItem('hiresight_questions_' + targetSessionId)
            : null;
        if (cached) {
          try {
            loadedQuestions = JSON.parse(cached);
          } catch {
            loadedQuestions = [];
          }
        }
      }

      if (loadedQuestions.length === 0 && state.current_question) {
        loadedQuestions = [state.current_question];
      }

      if (typeof window !== 'undefined' && loadedQuestions.length > 0) {
        sessionStorage.setItem(
          'hiresight_questions_' + targetSessionId,
          JSON.stringify(loadedQuestions)
        );
      }

      setQuestions(loadedQuestions);
      setCurrentIdx(state.current_question_index);
      setLastScore(null);
      setReport(null);

      // Initialize media and speak current question
      const mediaReady = await initializeMedia();
      const currentQ =
        loadedQuestions[state.current_question_index] || state.current_question;
      if (mediaReady && currentQ) {
        setTimeout(() => speakQuestion(currentQ.question_text, currentQ), 500);
      }
    } catch (err) {
      console.error('Session recovery failed:', err);
      setError(
        formatApiDetail(err.response?.data?.detail) ||
          'Failed to recover interview session state.'
      );
    } finally {
      setLoading(false);
    }
  };

  const startInterview = async (jobPostId = null, extraPayload = {}) => {
    setLoading(true);
    setError('');
    try {
      const payload = {
        num_questions: 20,
        ...(jobPostId ? { job_post_id: jobPostId } : {}),
        ...extraPayload,
      };
      const data = await interviewService.startSession(payload);
      setSessionId(data.session_id);
      setQuestions(data.questions || []);
      if (typeof window !== 'undefined') {
        sessionStorage.setItem(
          'hiresight_questions_' + data.session_id,
          JSON.stringify(data.questions || [])
        );
      }
      setCurrentIdx(0);
      setLastScore(null);
      setReport(null);
      setFaceRegistered(false);

      // Initialize media and start first question
      const mediaReady = await initializeMedia();
      if (mediaReady && data.questions?.length > 0) {
        setTimeout(() => speakQuestion(data.questions[0].question_text, data.questions[0]), 500);
      }
    } catch (err) {
      setError(formatApiDetail(err.response?.data?.detail) || 'Failed to start interview');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    if (!router.isReady || !authService.isAuthenticated()) return;
    if (sessionId || autoStartedRef.current) return;

    const querySessionId = router.query.sessionId || router.query.session_id;
    if (querySessionId && typeof querySessionId === 'string') {
      autoStartedRef.current = true;
      recoverSessionState(querySessionId);
      return;
    }

    const queryJobPostId = typeof router.query.jobPostId === 'string' ? router.query.jobPostId : null;
    const queryJobRole = typeof router.query.jobRole === 'string' ? router.query.jobRole : null;
    const autostart = router.query.autostart === 'true' || queryJobPostId || queryJobRole;

    if (autostart) {
      autoStartedRef.current = true;
      startInterview(queryJobPostId, queryJobRole ? { job_role: queryJobRole } : {});
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [router.isReady, router.query, sessionId]);

  const handleSubmitAnswer = () => {
    let transcript = '';
    if (inputMode === 'text') {
      transcript = textAnswer.trim();
    } else {
      transcript = displayTranscript.trim();
    }

    if (!transcript && isCodingPhase) {
      transcript =
        '[Coding round] Candidate continued in the code editor; verbal/text walkthrough optional.';
    }

    if (inputMode === 'text' && !transcript) {
      setError('Please enter your written response before submitting.');
      return;
    }

    submitAnswer(transcript);
  };

  const submitAnswer = async (transcript) => {
    if (!sessionId || !currentQuestion) return;

    stopListening();
    conversationStateRef.current = 'processing';
    setConversationState('processing');
    setLoading(true);
    setError('');

    try {
      // Capture video frame snapshot gracefully
      let frameBase64 = '';
      try {
        const frame = await captureFrame();
        if (frame) {
          frameBase64 = await blobToBase64(frame);
        }
      } catch (fErr) {
        console.warn('Non-fatal frame capture note:', fErr);
      }

      // Package real recorded audio chunks if available, or fallback WAV
      let audioBase64 = '';
      let audioFormat = 'webm';
      if (audioChunksRef.current && audioChunksRef.current.length > 0) {
        const mime = audioChunksRef.current[0]?.type || 'audio/webm';
        audioFormat = mime.includes('mp4') ? 'mp4' : mime.includes('ogg') ? 'ogg' : 'webm';
        const recordedBlob = new Blob(audioChunksRef.current, { type: mime });
        audioBase64 = await blobToBase64(recordedBlob);
      } else {
        const dummyAudio = new Blob([new ArrayBuffer(44)], { type: 'audio/wav' });
        audioBase64 = await blobToBase64(dummyAudio);
        audioFormat = 'wav';
      }

      const payload = {
        question_index: currentIdx,
        audio_base64: audioBase64,
        transcript_text: transcript || null,
        audio_format: audioFormat,
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

      // Clear transcripts and text draft for next question
      setLiveTranscript('');
      setFinalTranscript('');
      setTextAnswer('');

      // Handle follow-up questions
      let updatedQuestions = [...questions];
      if (score.follow_up_question) {
        updatedQuestions.splice(currentIdx + 1, 0, score.follow_up_question);
        setQuestions(updatedQuestions);
        if (typeof window !== 'undefined') {
          sessionStorage.setItem(
            'hiresight_questions_' + sessionId,
            JSON.stringify(updatedQuestions)
          );
        }
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
            speakQuestion(nextQ.question_text, nextQ);
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
      const detailStr = formatApiDetail(err.response?.data?.detail) || '';
      if (
        detailStr.toLowerCase().includes('already been answered') ||
        detailStr.toLowerCase().includes('out of order') ||
        detailStr.toLowerCase().includes('invalid question index')
      ) {
        // Automatically sync and recover exact question position or display report
        recoverSessionState(sessionId);
        return;
      }
      setError(detailStr || 'Failed to evaluate answer');
      setConversationState('listening');
      if (inputMode === 'voice') startListening();
    } finally {
      setLoading(false);
    }
  };

  const handleSkipQuestion = async () => {
    if (loading || !sessionId || !currentQuestion) return;
    if (
      !window.confirm(
        'Skip this question? A short placeholder will be sent and you will move to the next question.'
      )
    ) {
      return;
    }
    setError('');
    stopQuestionSpeech();
    stopListening();
    conversationStateRef.current = 'processing';
    setConversationState('processing');
    setLiveTranscript('');
    setFinalTranscript('');
    await submitAnswer(SKIP_QUESTION_TRANSCRIPT);
  };

  const formatMmSs = (total) => {
    const m = Math.floor(total / 60);
    const s = total % 60;
    return `${String(m).padStart(2, '0')}:${String(s).padStart(2, '0')}`;
  };

  const scoreToPercent = (v) => {
    if (v == null || Number.isNaN(Number(v))) return null;
    const n = Number(v);
    if (n <= 10) return Math.round(n * 10);
    return Math.round(Math.min(100, n));
  };

  const paceFromScore = (overall) => {
    if (overall == null) return '—';
    const n = Number(overall);
    if (n >= 7.5) return 'Good';
    if (n >= 5) return 'Steady';
    return 'Build depth';
  };

  const liveMetrics = useMemo(() => {
    if (!lastScore?.evaluation) {
      return { pace: '—', clarity: '—', confidence: '—' };
    }
    const ev = lastScore.evaluation;
    const clarity = scoreToPercent(ev.communication_score);
    const confidence = scoreToPercent(ev.depth_score);
    return {
      pace: paceFromScore(lastScore.per_answer_score),
      clarity: clarity != null ? `${clarity}%` : '—',
      confidence: confidence != null ? `${confidence}%` : '—',
    };
  }, [lastScore]);

  const difficultyBadge = useMemo(() => {
    const d = (currentQuestion?.difficulty || 'medium').toLowerCase();
    if (d === 'easy') return 'Easy';
    if (d === 'hard') return 'Hard';
    return 'Medium';
  }, [currentQuestion]);

  const toggleMic = useCallback(() => {
    const stream = mediaStreamRef.current;
    if (!stream) return;
    const nextMuted = !micMuted;
    stream.getAudioTracks().forEach((t) => {
      t.enabled = !nextMuted;
    });
    setMicMuted(nextMuted);
    micMutedRef.current = nextMuted;
    if (nextMuted) {
      stopListening();
    } else if (conversationStateRef.current === 'listening' && !loadingRef.current) {
      setTimeout(() => {
        if (!micMutedRef.current && conversationStateRef.current === 'listening') {
          startListening();
        }
      }, 0);
    }
  }, [micMuted]);

  const toggleCamera = useCallback(() => {
    const stream = mediaStreamRef.current;
    if (!stream) return;
    const nextOff = !cameraOff;
    stream.getVideoTracks().forEach((t) => {
      t.enabled = !nextOff;
    });
    setCameraOff(nextOff);
  }, [cameraOff]);

  const handleEndInterview = async () => {
    if (!window.confirm('End this interview session?')) return;
    stopListening();
    stopQuestionSpeech();
    cleanupMedia();
    try {
      if (sessionId) await interviewService.endSession(sessionId);
    } catch {
      /* ignore */
    }
    router.push('/dashboard');
  };

  return (
    <div className="min-h-screen bg-[#0B1120] text-slate-100">
      {/* Top bar */}
      <header className="sticky top-0 z-20 border-b border-white/10 bg-[#0B1120]/95 backdrop-blur-md">
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-4 px-4 py-3 sm:px-6">
          <div className="flex min-w-0 flex-1 flex-wrap items-center gap-3">
            <span className="text-sm font-semibold tracking-tight text-white">HireSight</span>
            <span className="text-slate-500">/</span>
            <span className="text-sm text-slate-300">Live Interview</span>
            {sessionId && (
              <>
                <span className="hidden h-4 w-px bg-white/15 sm:block" aria-hidden />
                <span className="inline-flex max-w-[200px] truncate rounded-full border border-indigo-400/40 bg-indigo-500/15 px-3 py-1 text-xs font-medium text-indigo-200 sm:max-w-xs">
                  {jobRoleLabel}
                </span>
                <span className="inline-flex items-center gap-1.5 rounded-full border border-emerald-500/30 bg-emerald-500/10 px-2.5 py-1 text-xs font-medium text-emerald-300">
                  <span className="h-1.5 w-1.5 animate-pulse rounded-full bg-emerald-400" />
                  Live Session
                </span>
              </>
            )}
        </div>
          <div className="flex shrink-0 items-center gap-1">
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition hover:bg-white/5 hover:text-white"
              aria-label="Settings"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.594 3.94c.09-.542.56-.94 1.11-.94h2.593c.55 0 1.02.398 1.11.94l.213 1.281c.063.374.313.686.645.87.074.04.147.083.22.127.325.196.72.257 1.075.124l1.217-.456a1.125 1.125 0 011.37.49l1.296 2.247a1.125 1.125 0 01-.26 1.431l-1.003.827c-.293.241-.438.613-.43.992a7.723 7.723 0 010 .255c-.008.378.137.75.43.991l1.004.827c.424.35.534.954.26 1.43l-1.298 2.247a1.125 1.125 0 01-1.369.491l-1.217-.456c-.355-.133-.75-.072-1.076.124a6.47 6.47 0 01-.22.128c-.331.183-.581.495-.644.869l-.213 1.281c-.09.543-.56.94-1.11.94h-2.594c-.55 0-1.019-.398-1.11-.94l-.213-1.281c-.062-.374-.312-.686-.644-.87a6.52 6.52 0 01-.22-.127c-.325-.196-.72-.257-1.075-.124l-1.217.456a1.125 1.125 0 01-1.369-.49l-1.297-2.247a1.125 1.125 0 01.26-1.431l1.004-.827c.292-.24.437-.613.43-.991a6.932 6.932 0 010-.255c.007-.38-.138-.751-.43-.992l-1.004-.827a1.125 1.125 0 01-.26-1.43l1.297-2.247a1.125 1.125 0 011.37-.491l1.216.456c.356.133.751.072 1.076-.124.072-.044.146-.087.22-.128.332-.183.582-.495.644-.869l.214-1.281z" />
                <path strokeLinecap="round" strokeLinejoin="round" d="M15 12a3 3 0 11-6 0 3 3 0 016 0z" />
              </svg>
            </button>
            <button
              type="button"
              className="flex h-10 w-10 items-center justify-center rounded-full text-slate-400 transition hover:bg-white/5 hover:text-white"
              aria-label="Help"
            >
              <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                <path strokeLinecap="round" strokeLinejoin="round" d="M9.879 7.519c1.171-1.025 3.071-1.025 4.242 0 1.172 1.025 1.172 2.687 0 3.712-.203.179-.43.326-.67.442-.745.361-1.45.999-1.45 1.827v.75M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9 5.25h.008v.008H12v-.008z" />
              </svg>
            </button>
            {sessionId && !report && (
              <button
                type="button"
                onClick={handleEndInterview}
                className="flex h-10 w-10 items-center justify-center rounded-full text-red-400 transition hover:bg-red-500/10 hover:text-red-300"
                aria-label="End session"
              >
                <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                  <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 9V5.25A2.25 2.25 0 0013.5 3h-6a2.25 2.25 0 00-2.25 2.25v13.5A2.25 2.25 0 007.5 21h6a2.25 2.25 0 002.25-2.25V15M12 9l-3 3m0 0l3 3m-3-3h12.75" />
                </svg>
              </button>
            )}
          </div>
        </div>
      </header>

      <main className="mx-auto max-w-[1600px] space-y-6 px-4 py-6 sm:px-6">
        {!sessionId && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-8 text-center">
            <p className="text-sm text-slate-400">Preparing your session…</p>
          <button
            onClick={() => startInterview(router.query.jobPostId)}
            disabled={loading}
              className="mt-4 rounded-xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-600 disabled:opacity-50"
          >
              {loading ? 'Starting…' : 'Start Interview'}
          </button>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-400/30 bg-red-500/10 px-4 py-3 text-sm text-red-200">
            {error}
          </div>
        )}

        {sessionId && currentQuestion && !report && (
          <div className="grid gap-6 lg:grid-cols-[1fr_400px] xl:grid-cols-[1fr_440px]">
            {/* Left: video + question */}
            <div className="space-y-5">
              <div className="relative overflow-hidden rounded-2xl border border-white/10 bg-slate-950/80 shadow-xl">
                <div className="aspect-video w-full min-h-[280px] sm:min-h-[320px]">
                <video
                  ref={videoRef}
                  autoPlay
                  muted
                  playsInline
                    className={`h-full w-full object-cover ${cameraOff ? 'opacity-0' : 'opacity-100'}`}
                  />
                  {cameraOff && (
                    <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950 text-slate-500">
                      <svg className="mb-3 h-14 w-14 opacity-50" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72M4.5 18.75h9a2.25 2.25 0 002.25-2.25v-9a2.25 2.25 0 00-2.25-2.25h-9A2.25 2.25 0 002.25 7.5v9a2.25 2.25 0 002.25 2.25z" />
                      </svg>
                      <p className="text-sm">Camera off</p>
                    </div>
                  )}
                </div>

                <div className="absolute left-4 top-4 flex flex-wrap items-center gap-2">
                  <span className="inline-flex items-center gap-1.5 rounded-lg border border-white/10 bg-black/50 px-2.5 py-1 text-xs font-medium text-slate-200 backdrop-blur-sm">
                    <svg className="h-3.5 w-3.5 text-emerald-400" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M4 4a2 2 0 012-2h4.586A2 2 0 0112 2.586L15.414 6A2 2 0 0116 7.414V16a2 2 0 01-2 2H6a2 2 0 01-2-2V4z" />
                    </svg>
                    {cameraOff ? 'Camera off' : 'Camera active'}
                  </span>
                  <span
                    className={`inline-flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium backdrop-blur-sm ${
                      micMuted
                        ? 'border-amber-400/40 bg-amber-500/15 text-amber-200'
                        : 'border-white/10 bg-black/50 text-slate-200'
                    }`}
                  >
                    <svg className={`h-3.5 w-3.5 ${micMuted ? 'text-amber-400' : 'text-sky-400'}`} fill="currentColor" viewBox="0 0 20 20">
                      <path
                        fillRule="evenodd"
                        d="M7 4a3 3 0 016 0v4a3 3 0 11-6 0V4zm4 10.93A7.001 7.001 0 0017 8a1 1 0 10-2 0A5 5 0 015 8a1 1 0 00-2 0 7.001 7.001 0 006 6.93V17H6a1 1 0 100 2h8a1 1 0 100-2h-3v-2.07z"
                        clipRule="evenodd"
                      />
                    </svg>
                    {micMuted ? 'Mic off' : 'Mic on'}
                  </span>
                  <span className="rounded-lg border border-white/10 bg-black/50 px-2.5 py-1 text-xs font-medium text-slate-200 backdrop-blur-sm">
                    Q{overallBaseNumber}/{overallBaseTotal || 1}
                    </span>
                </div>

                <div className="absolute bottom-4 left-1/2 flex -translate-x-1/2 flex-col items-center gap-2">
                  <p className="pointer-events-none text-[10px] font-medium text-slate-400">
                    {micMuted ? 'Mic muted — live captions paused' : 'Mic on — tap to mute'}
                  </p>
                  <div className="flex gap-3">
                  <button
                    type="button"
                    onClick={toggleMic}
                    title={micMuted ? 'Turn microphone on' : 'Turn microphone off'}
                    className={`flex h-12 w-12 items-center justify-center rounded-full border shadow-lg transition ${
                      micMuted
                        ? 'border-amber-400/50 bg-amber-500/20 text-amber-100'
                        : 'border-white/20 bg-slate-900/90 text-white hover:bg-slate-800'
                    }`}
                    aria-label={micMuted ? 'Turn microphone on' : 'Turn microphone off'}
                  >
                    {micMuted ? (
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                        <path strokeLinecap="round" strokeLinejoin="round" d="M4 4l16 16" />
                      </svg>
                    ) : (
                      <svg className="h-6 w-6" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                        <path strokeLinecap="round" strokeLinejoin="round" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
                      </svg>
                    )}
                  </button>
                  <button
                    type="button"
                    onClick={toggleCamera}
                    className={`flex h-12 w-12 items-center justify-center rounded-full border shadow-lg transition ${
                      cameraOff
                        ? 'border-amber-400/50 bg-amber-500/20 text-amber-200'
                        : 'border-white/20 bg-slate-900/90 text-white hover:bg-slate-800'
                    }`}
                    aria-label={cameraOff ? 'Turn camera on' : 'Turn camera off'}
                  >
                    <svg className="h-5 w-5" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M15.75 10.5l4.72-4.72a.75.75 0 011.28.53v11.38a.75.75 0 01-1.28.53l-4.72-4.72m0 0l-3.08 3.087m0 0l-3-3m3 3l3-3m-6 3h-7.5a2.25 2.25 0 01-2.25-2.25v-9a2.25 2.25 0 012.25-2.25h9a2.25 2.25 0 012.25 2.25v9a2.25 2.25 0 01-2.25 2.25z" />
                    </svg>
                  </button>
                  <button
                    type="button"
                    onClick={handleEndInterview}
                    className="flex h-12 w-12 items-center justify-center rounded-full border border-red-400/40 bg-red-500/20 text-red-200 shadow-lg transition hover:bg-red-500/30"
                    aria-label="End interview"
                  >
                    <span className="h-3 w-3 rounded-sm bg-red-400" />
                  </button>
                  </div>
                </div>
              </div>

              {/* AI question card */}
              <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-5 sm:p-6">
                {isFollowUpQuestion && (
                  <div className="mb-4 flex items-start gap-3 rounded-xl border border-violet-400/30 bg-violet-950/40 p-3.5 text-xs text-violet-200 shadow-inner">
                    <Sparkles className="mt-0.5 h-4 w-4 shrink-0 text-violet-400" />
                    <div>
                      <p className="font-semibold text-violet-100">Adaptive Deep-Dive Follow-Up</p>
                      <p className="mt-0.5 text-violet-200/80 leading-relaxed">
                        The interviewer is exploring technical depth based on your previous response. Take your time to clarify specific trade-offs and implementation nuances.
                      </p>
                    </div>
                  </div>
                )}

                <div className="mb-4 flex flex-wrap items-center gap-3">
                  <div className="flex items-center gap-2 text-slate-300">
                    <span
                      className={`flex gap-0.5 ${conversationState === 'asking' || isSpeakingQuestion ? 'opacity-100' : 'opacity-40'}`}
                      aria-hidden
                    >
                      {[0, 1, 2, 3, 4].map((i) => (
                        <span
                          key={i}
                          className="w-0.5 rounded-full bg-indigo-400"
                          style={{
                            height: `${10 + (i % 3) * 6}px`,
                            animation:
                              conversationState === 'asking' || isSpeakingQuestion
                                ? 'pulse 1s ease-in-out infinite'
                                : 'none',
                            animationDelay: `${i * 0.08}s`,
                          }}
                        />
                      ))}
                    </span>
                    <span className="text-sm font-medium">
                      {conversationState === 'asking' || isSpeakingQuestion
                        ? 'AI interviewer is asking…'
                        : conversationState === 'listening'
                          ? inputMode === 'text'
                            ? 'Awaiting your text response…'
                            : 'Listening for your answer…'
                          : conversationState === 'processing'
                            ? 'Processing your response…'
                            : 'Ready'}
                    </span>
                    <span className="rounded-md border border-white/10 bg-white/5 px-2 py-0.5 font-mono text-xs text-slate-400">
                      {formatMmSs(elapsedSec)}
                    </span>
                  </div>
                </div>
                <p className="mb-4 text-[11px] font-medium uppercase tracking-wider text-slate-500">
                  Phase {currentStageIndex}/{stageOrder.length} — {currentStageLabel.toUpperCase()}
                </p>
                <div className="mb-4 flex flex-wrap gap-2">
                  <span className="rounded-full border border-indigo-400/30 bg-indigo-500/10 px-3 py-1 text-xs font-medium text-indigo-200">
                    {currentStageLabel}
                  </span>
                  <span className="rounded-full border border-amber-400/30 bg-amber-500/10 px-3 py-1 text-xs font-medium text-amber-200">
                    {difficultyBadge}
                  </span>
                  {isFollowUpQuestion && (
                    <span className="inline-flex items-center gap-1 rounded-full border border-violet-400/40 bg-violet-500/20 px-3 py-1 text-xs font-semibold text-violet-200 shadow-sm">
                      <Sparkles className="h-3 w-3 text-violet-300" />
                      Follow-up Question
                    </span>
                  )}
                </div>
                <p className="text-lg font-medium leading-relaxed text-white sm:text-xl">
                  {currentQuestion.question_text}
                </p>

                {currentQuestion.coding_challenge && (
                  <div className="mt-6 space-y-4">
                    <div className="rounded-lg border border-emerald-500/30 bg-emerald-950/30 px-3 py-2">
                      <p className="text-xs font-semibold uppercase tracking-wide text-emerald-300">
                        Coding round · Monaco editor
                      </p>
                      <p className="mt-0.5 text-[11px] text-emerald-100/80">
                        Problem details stay on the left with your camera. Monaco editor and voice/text capture are in the
                        right panel.
                      </p>
                    </div>

                    <div className="space-y-4 rounded-xl border border-white/10 bg-slate-950/60 p-4 shadow-inner ring-1 ring-white/5">
                      <h3 className="text-base font-semibold text-white">
                        {currentQuestion.coding_challenge.title}
                      </h3>
                      <p className="whitespace-pre-wrap text-sm leading-relaxed text-slate-300">
                        {currentQuestion.coding_challenge.problem_statement}
                      </p>
                      {currentQuestion.coding_challenge.constraints ? (
                        <p className="text-xs text-slate-400">
                          <span className="font-medium text-slate-300">Constraints: </span>
                          {currentQuestion.coding_challenge.constraints}
                        </p>
                      ) : null}
                      {Array.isArray(currentQuestion.coding_challenge.public_test_cases) &&
                      currentQuestion.coding_challenge.public_test_cases.length > 0 ? (
                        <div>
                          <p className="mb-2 text-[11px] font-medium uppercase tracking-wide text-slate-500">
                            Public sample tests (stdin → expected stdout)
                          </p>
                          <ul className="max-h-56 space-y-2 overflow-y-auto pr-1">
                            {currentQuestion.coding_challenge.public_test_cases.map((tc, i) => (
                              <li
                                key={i}
                                className="rounded-lg border border-white/10 bg-[#0B1120] p-3 text-xs text-slate-300"
                              >
                                <p className="mb-1 font-medium text-slate-200">
                                  {tc.description || `Sample ${i + 1}`}
                                </p>
                                <p className="font-mono text-[11px] text-slate-400">
                                  <span className="text-slate-500">stdin:</span>{' '}
                                  <span className="whitespace-pre-wrap text-slate-300">{tc.stdin}</span>
                                </p>
                                <p className="mt-1 font-mono text-[11px] text-slate-400">
                                  <span className="text-slate-500">expected stdout:</span>{' '}
                                  <span className="whitespace-pre-wrap text-emerald-200/90">
                                    {tc.expected_stdout}
                                  </span>
                                </p>
                              </li>
                            ))}
                          </ul>
                        </div>
                      ) : null}
                    </div>
                  </div>
                )}
              </div>
            </div>

            {/* Right: Monaco + voice/text (coding) or live transcript / text input (other phases) */}
            <div className="flex min-h-0 flex-col gap-5">
              {isCodingPhase && currentQuestion.coding_challenge ? (
                <CodingWorkspace
                  key={currentQuestion.question_id}
                  sessionId={sessionId}
                  challengeId={
                    currentQuestion.coding_challenge?.challenge_id ||
                    currentQuestion.coding_challenge_id ||
                    `CHAL-${currentQuestion.question_id}`
                  }
                  questionIndex={currentIdx}
                  starterCode={currentQuestion.coding_challenge.starter_code || ''}
                  starterTemplates={currentQuestion.coding_challenge.starter_templates || {}}
                  recommendedLanguages={
                    currentQuestion.coding_challenge.recommended_languages || ['python']
                  }
                  title={currentQuestion.coding_challenge.title || 'solution.py'}
                  publicTestCases={currentQuestion.coding_challenge.public_test_cases || []}
                  onEditorFocus={stopListening}
                />
              ) : null}

              <div className="flex flex-1 flex-col rounded-2xl border border-white/10 bg-slate-900/50 p-5">
                {/* Input Mode Selector Header */}
                <div className="mb-4 flex flex-col gap-3">
                  <InputModeSelector
                    mode={inputMode}
                    onChange={handleInputModeChange}
                    disabled={loading || conversationState === 'processing'}
                    isListening={isListening}
                    micMuted={micMuted}
                  />

                  <div className="flex flex-wrap items-center justify-between gap-2 border-t border-white/5 pt-2">
                    <div className="flex items-center gap-2 text-sm font-semibold text-slate-200">
                      {inputMode === 'voice' ? (
                        <>
                          <svg className="h-4 w-4 text-indigo-400" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m12 0V9a3 3 0 00-3-3h-.75a3 3 0 00-3 3v.75m12 0h.008v.008H18V9z" />
                          </svg>
                          <span>{isCodingPhase ? 'Voice transcript (optional)' : 'Spoken response (captions)'}</span>
                        </>
                      ) : (
                        <>
                          <FileText className="h-4 w-4 text-indigo-400" />
                          <span>Written Response Input</span>
                        </>
                      )}
                    </div>
                    <div className="flex flex-wrap items-center gap-2">
                      {inputMode === 'voice' && (
                        <div className="inline-flex items-center gap-2 rounded-lg border border-white/10 bg-[#0B1120] px-2.5 py-1 text-xs">
                          <span className="flex items-end gap-0.5 h-3">
                            <span
                              className="w-1 bg-emerald-400 rounded-full transition-all duration-75"
                              style={{ height: `${Math.max(3, Math.min(14, audioLevel * 0.14))}px` }}
                            />
                            <span
                              className="w-1 bg-emerald-400 rounded-full transition-all duration-75"
                              style={{ height: `${Math.max(3, Math.min(14, audioLevel * 0.28))}px` }}
                            />
                            <span
                              className="w-1 bg-emerald-400 rounded-full transition-all duration-75"
                              style={{ height: `${Math.max(3, Math.min(14, audioLevel * 0.2))}px` }}
                            />
                          </span>
                          <span className={audioLevel > 5 ? 'text-emerald-300 font-medium' : 'text-slate-400'}>
                            {micMuted
                              ? 'Mic Muted'
                              : audioLevel > 5
                              ? 'Voice Active'
                              : isListening
                              ? 'Listening…'
                              : 'Mic Ready'}
                          </span>
                        </div>
                      )}
                      <button
                        type="button"
                        onClick={() => {
                          if (inputMode === 'text') {
                            setTextAnswer('');
                          } else {
                            clearTranscript();
                          }
                        }}
                        disabled={inputMode === 'text' ? !textAnswer.trim() : !displayTranscript.trim()}
                        className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/5 disabled:opacity-40"
                      >
                        Clear
                      </button>
                      <button
                        type="button"
                        onClick={async () => {
                          const t = inputMode === 'text' ? textAnswer.trim() : displayTranscript.trim();
                          if (!t) return;
                          try {
                            await navigator.clipboard.writeText(t);
                          } catch {
                            /* ignore */
                          }
                        }}
                        disabled={inputMode === 'text' ? !textAnswer.trim() : !displayTranscript.trim()}
                        className="rounded-lg border border-white/15 px-3 py-1.5 text-xs font-medium text-slate-300 transition hover:bg-white/5 disabled:opacity-40"
                      >
                        Copy
                      </button>
                      {inputMode === 'voice' ? (
                        <button
                          type="button"
                          onClick={() => {
                            if (micMuted) return;
                            if (isListening) {
                              stopListening();
                            } else {
                              startListening();
                            }
                          }}
                          disabled={micMuted || loading || conversationState === 'asking' || conversationState === 'processing'}
                          className={`inline-flex items-center gap-1.5 rounded-lg border px-3 py-1.5 text-xs font-medium transition ${
                            isListening
                              ? 'border-emerald-500/40 bg-emerald-500/15 text-emerald-300 hover:bg-emerald-500/25'
                              : 'border-indigo-500/30 bg-indigo-500/15 text-indigo-200 hover:bg-indigo-500/25'
                          } disabled:cursor-not-allowed disabled:opacity-40`}
                        >
                          <span className={`h-2 w-2 rounded-full ${isListening ? 'bg-emerald-400 animate-ping' : 'bg-slate-400'}`} />
                          <span>{isListening ? 'Listening… (pause)' : 'Start Speaking'}</span>
                        </button>
                      ) : null}
                    </div>
                  </div>
                </div>

                {/* Response Input Body (Voice Captions vs Text Editor) */}
                {inputMode === 'voice' ? (
                  <div
                    className={`flex flex-1 flex-col overflow-y-auto rounded-xl border border-white/10 bg-[#0B1120]/80 p-4 ${
                      isCodingPhase ? 'min-h-[200px]' : 'min-h-[260px]'
                    }`}
                  >
                    {speechNotice && (
                      <div className="mb-3 rounded-lg border border-indigo-500/30 bg-indigo-950/40 p-3 text-xs text-indigo-200 shadow-inner">
                        <p className="leading-relaxed">{speechNotice}</p>
                      </div>
                    )}
                    {displayTranscript ? (
                      <div className="flex flex-1 flex-col gap-2">
                        <textarea
                          value={displayTranscript}
                          onChange={(e) => {
                            setFinalTranscript(e.target.value);
                          }}
                          className="w-full flex-1 rounded-xl border border-white/10 bg-black/30 p-3.5 text-sm leading-relaxed text-slate-100 placeholder:text-slate-500 focus:border-indigo-400/50 focus:outline-none focus:ring-1 focus:ring-indigo-400/30 resize-none font-sans"
                          rows={isCodingPhase ? 6 : 8}
                          placeholder="Your spoken transcription appears here... You can edit or add notes anytime."
                        />
                        {liveTranscript && (
                          <p className="px-1 text-xs text-indigo-400 italic animate-pulse">
                            Live voice stream: {liveTranscript}…
                          </p>
                        )}
                      </div>
                    ) : (
                      <div className="flex h-full min-h-[200px] flex-col items-center justify-center text-center text-slate-500">
                        <div className="relative mb-3 flex items-center justify-center">
                          <div
                            className={`h-16 w-16 rounded-full border transition-all duration-150 flex items-center justify-center ${
                              audioLevel > 5
                                ? 'border-emerald-500/60 bg-emerald-500/15 scale-110 shadow-lg shadow-emerald-500/20'
                                : 'border-indigo-500/20 bg-indigo-500/5'
                            }`}
                          >
                            <svg className={`h-8 w-8 transition ${audioLevel > 5 ? 'text-emerald-400' : 'text-indigo-400/60'}`} fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                              <path strokeLinecap="round" strokeLinejoin="round" d="M12 18.75a6 6 0 006-6v-1.5m-6 7.5a6 6 0 01-6-6v-1.5m12 0V9a3 3 0 00-3-3h-.75a3 3 0 00-3 3v.75m12 0h.008v.008H18V9z" />
                            </svg>
                          </div>
                        </div>
                        <p className="text-sm font-medium text-slate-300">
                          {isCodingPhase
                            ? 'Speak to dictate your solution approach, or type in Monaco editor.'
                            : audioLevel > 5
                            ? 'Audio detected — speaking into microphone'
                            : 'Start speaking — your answer is being captured in real time'}
                        </p>
                        <p className="mt-1.5 text-xs text-slate-500">
                          Prefer typing? Click <button type="button" onClick={() => handleInputModeChange('text')} className="text-indigo-400 underline hover:text-indigo-300">Text Input</button> mode anytime.
                        </p>
                      </div>
                    )}
                  </div>
                ) : (
                  <div className="flex flex-1 flex-col gap-2.5">
                    <div className="relative flex-1">
                      <textarea
                        value={textAnswer}
                        onChange={(e) => setTextAnswer(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) {
                            e.preventDefault();
                            handleSubmitAnswer();
                          }
                        }}
                        disabled={loading || conversationState === 'processing'}
                        placeholder="Type your technical response here... Detail algorithms, system architecture, trade-offs, and practical examples."
                        className={`w-full rounded-xl border border-white/15 bg-[#0B1120]/90 p-4 text-sm leading-relaxed text-slate-100 placeholder:text-slate-500 focus:border-indigo-400/50 focus:outline-none focus:ring-1 focus:ring-indigo-400/30 resize-none font-sans ${
                          isCodingPhase ? 'min-h-[180px]' : 'min-h-[240px]'
                        }`}
                        rows={isCodingPhase ? 6 : 8}
                      />
                    </div>

                    <div className="flex flex-wrap items-center justify-between gap-2 px-1 text-xs text-slate-400">
                      <span className="font-mono text-[11px] text-slate-400">
                        {textAnswer.trim().split(/\s+/).filter(Boolean).length} words · {textAnswer.length} chars
                      </span>
                      <button
                        type="button"
                        onClick={() => setShowStarGuidance(!showStarGuidance)}
                        className="inline-flex items-center gap-1 text-[11px] text-indigo-300 transition hover:text-indigo-200"
                      >
                        <Lightbulb className="h-3.5 w-3.5 text-amber-400" />
                        <span>{showStarGuidance ? 'Hide STAR Framework' : 'STAR Framework Tips'}</span>
                        {showStarGuidance ? <ChevronUp className="h-3.5 w-3.5" /> : <ChevronDown className="h-3.5 w-3.5" />}
                      </button>
                    </div>

                    {showStarGuidance && (
                      <div className="rounded-xl border border-indigo-400/20 bg-indigo-950/40 p-3.5 text-[11px] text-slate-300 space-y-1.5 shadow-inner">
                        <p className="font-semibold text-indigo-200">Recommended Structuring Technique (STAR):</p>
                        <ul className="list-disc list-inside space-y-0.5 text-slate-400">
                          <li><strong className="text-slate-200">Situation:</strong> Context, scale, or business requirements.</li>
                          <li><strong className="text-slate-200">Task:</strong> Your core technical responsibility and constraints.</li>
                          <li><strong className="text-slate-200">Action:</strong> Architecture chosen, patterns used, and trade-offs made.</li>
                          <li><strong className="text-slate-200">Result:</strong> Measured impact, reliability, latency, or throughput gain.</li>
                        </ul>
                      </div>
                    )}
                  </div>
                )}
                
                {/* Score Indicators */}
                <div className="mt-4 grid grid-cols-3 gap-3">
                  <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 px-3 py-3 text-center">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Pace</p>
                    <p
                      className={`mt-1 text-sm font-semibold ${
                        liveMetrics.pace === '—' ? 'text-slate-500' : 'text-indigo-300'
                      }`}
                    >
                      {liveMetrics.pace}
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 px-3 py-3 text-center">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Clarity</p>
                    <p
                      className={`mt-1 text-sm font-semibold ${
                        liveMetrics.clarity === '—' ? 'text-slate-500' : 'text-emerald-300'
                      }`}
                    >
                      {liveMetrics.clarity}
                    </p>
                  </div>
                  <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 px-3 py-3 text-center">
                    <p className="text-[10px] font-medium uppercase tracking-wide text-slate-500">Confidence</p>
                    <p
                      className={`mt-1 text-sm font-semibold ${
                        liveMetrics.confidence === '—' ? 'text-slate-500' : 'text-amber-200'
                      }`}
                    >
                      {liveMetrics.confidence}
                    </p>
                  </div>
                </div>

                <p className="mt-3 flex items-center gap-1.5 text-[11px] text-slate-500">
                  <svg className="h-3.5 w-3.5 shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={1.5}>
                    <path strokeLinecap="round" strokeLinejoin="round" d="M11.25 11.25l.041-.02a.75.75 0 011.063.852l-.708 2.836a.75.75 0 001.063.853l.041-.021M21 12a9 9 0 11-18 0 9 9 0 0118 0zm-9-3.75h.008v.008H12V8.25z" />
                  </svg>
                  {inputMode === 'text'
                    ? 'Tip: Press Ctrl + Enter to quickly submit your response.'
                    : isCodingPhase
                      ? 'Speech recognition stays off while you type; resume it here for verbal notes.'
                      : 'AI evaluates answer depth, relevance, and technical accuracy live'}
                </p>

                <div className="mt-4 flex gap-3">
                  <button
                    type="button"
                    onClick={handleSkipQuestion}
                    disabled={loading || conversationState === 'processing'}
                    className="flex-1 rounded-xl border border-white/15 py-3 text-sm font-semibold text-slate-200 transition hover:bg-white/5 disabled:cursor-not-allowed disabled:opacity-40"
                  >
                    Skip question
                  </button>
                  <button
                    type="button"
                    onClick={handleSubmitAnswer}
                    disabled={
                      loading ||
                      conversationState === 'processing' ||
                      (inputMode === 'text' && !textAnswer.trim())
                    }
                    className="flex flex-1 items-center justify-center gap-2 rounded-xl bg-white py-3 text-sm font-semibold text-slate-900 transition hover:bg-slate-100 disabled:cursor-not-allowed disabled:opacity-40 shadow-lg shadow-white/10"
                  >
                    Next question
                    <svg className="h-4 w-4" fill="none" stroke="currentColor" viewBox="0 0 24 24" strokeWidth={2}>
                      <path strokeLinecap="round" strokeLinejoin="round" d="M13.5 4.5L21 12m0 0l-7.5 7.5M21 12H3" />
                    </svg>
                  </button>
                </div>
                <p className="mt-2 text-center text-[11px] text-slate-500">
                  {inputMode === 'text' ? (
                    <>
                      Enter your written answer, then tap <span className="text-slate-400">Next question</span> (or Ctrl+Enter)
                    </>
                  ) : isCodingPhase ? (
                    <>
                      Code in Monaco, optionally narrate with <span className="text-slate-400">Resume microphone</span>,
                      then <span className="text-slate-400">Next question</span>.
                    </>
                  ) : (
                    <>
                      Speak your answer, then tap <span className="text-slate-400">Next question</span>
                    </>
                  )}
                </p>
              </div>
            </div>
          </div>
        )}

        {lastScore && !report && sessionId && currentQuestion && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/40 p-5 text-sm">
            <h3 className="mb-3 font-semibold text-white">Previous answer evaluation</h3>
            <div className="grid grid-cols-2 gap-3 md:grid-cols-4">
              <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Overall</p>
                <p className="text-lg font-bold text-indigo-300">{lastScore.per_answer_score}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Relevance</p>
                <p className="text-lg font-bold text-white">{lastScore.evaluation?.relevance_score}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Depth</p>
                <p className="text-lg font-bold text-white">{lastScore.evaluation?.depth_score}</p>
              </div>
              <div className="rounded-xl border border-white/10 bg-[#0B1120]/60 p-3">
                <p className="text-[10px] uppercase tracking-wide text-slate-500">Communication</p>
                <p className="text-lg font-bold text-white">{lastScore.evaluation?.communication_score}</p>
              </div>
            </div>
          </div>
        )}

        {report && (
          <div className="rounded-2xl border border-white/10 bg-slate-900/50 p-6 space-y-6">
            <h2 className="text-xl font-semibold text-white">Interview complete</h2>
            <div className="grid grid-cols-2 gap-4 md:grid-cols-3">
              {[
                ['Overall', report.aggregate_scores?.overall_score],
                ['Technical', report.aggregate_scores?.technical_score],
                ['Behavioral', report.aggregate_scores?.behavioral_score],
                ['Communication', report.aggregate_scores?.communication_score],
                ['Video integrity', report.aggregate_scores?.video_integrity_score],
              ].map(([label, val]) => (
                <div key={label} className="rounded-xl border border-white/10 bg-[#0B1120]/60 p-4">
                  <p className="text-[10px] uppercase tracking-wide text-slate-500">{label}</p>
                  <p className="text-2xl font-bold text-indigo-300">{val ?? '—'}</p>
              </div>
              ))}
              </div>
            <div className="rounded-xl border border-indigo-400/20 bg-indigo-500/10 p-4">
              <p className="text-xs text-slate-400 mb-1">Recommendation</p>
              <p className="text-base font-medium text-white">{report.report?.recommendation}</p>
            </div>
            <button
              onClick={() => router.push('/dashboard')}
              className="rounded-xl bg-indigo-500 px-6 py-3 text-sm font-semibold text-white transition hover:bg-indigo-600"
            >
              Back to dashboard
            </button>
          </div>
        )}
      </main>
    </div>
  );
}
