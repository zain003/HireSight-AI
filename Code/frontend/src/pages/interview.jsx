import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import dynamic from 'next/dynamic';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import interviewService from '@/services/interviewService';
import { formatApiDetail } from '@/utils/formatApiDetail';
import ProblemStatementViewer from '@/components/Interview/ProblemStatementViewer';
import {
  Sparkles,
  FileText,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Lightbulb,
  RefreshCw,
  Mic,
  MicOff,
  Video,
  VideoOff,
  Code2,
  Terminal,
  Volume2,
  ShieldCheck,
  PlayCircle,
  Copy,
  AlertCircle,
  HelpCircle,
  Info,
  Check,
  Sun,
  Moon,
  Clock,
  Timer,
  Zap,
  ArrowRight,
  UserCheck,
  AlertTriangle,
  LogOut,
  SkipForward,
  Hourglass,
  X,
  ShieldAlert,
  AlertOctagon,
  Ban,
  FileWarning
} from 'lucide-react';

const CodingWorkspace = dynamic(
  () => import('@/components/Interview/CodingWorkspace'),
  {
    ssr: false,
    loading: () => (
      <div className="flex min-h-[380px] items-center justify-center rounded-xl border border-slate-200 bg-white text-sm text-slate-500 shadow-sm">
        Loading code editor…
      </div>
    ),
  }
);

import FaceTrackingOverlay from '@/components/Interview/FaceTrackingOverlay';

/** Sent to the API so the session advances; backend uses transcript_text when non-empty. */
const SKIP_QUESTION_TRANSCRIPT =
  '[Skipped] Candidate chose to skip this question. No verbal answer was provided.';

/** 6 Canonical Interview Phases with canonical timing allocations */
const CANONICAL_STAGES = [
  { key: 'introduction', label: 'Intro & CV', fullLabel: 'Introduction & CV Overview', timeSec: 120, timeBadge: '2m' },
  { key: 'technical', label: 'Core Technical', fullLabel: 'Core Technical Assessment', timeSec: 150, timeBadge: '2.5m' },
  { key: 'system_design', label: 'System Design', fullLabel: 'System Design & Architecture', timeSec: 240, timeBadge: '4m' },
  { key: 'coding', label: 'Coding Sandbox', fullLabel: 'Hands-On Coding Sandbox', timeSec: 600, timeBadge: '10m' },
  { key: 'behavioral', label: 'Behavioral', fullLabel: 'Behavioral & Engineering Standards', timeSec: 150, timeBadge: '2.5m' },
  { key: 'wrap_up', label: 'Wrap-Up', fullLabel: 'Closing & Candidate Q&A', timeSec: 120, timeBadge: '2m' },
];

export default function InterviewPage() {
  const router = useRouter();
  const [theme, setTheme] = useState('light'); // 'light' (default) | 'dark'
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
  const [questionTimerSec, setQuestionTimerSec] = useState(0);
  const [visionWarning, setVisionWarning] = useState(null);

  // High-visibility confirmation modals & transition overlays
  const [showSkipModal, setShowSkipModal] = useState(false);
  const [showLeaveModal, setShowLeaveModal] = useState(false);
  const [autoTransitionActive, setAutoTransitionActive] = useState(false);
  const [transitionStatusText, setTransitionStatusText] = useState('');

  // Proctoring integrity & anti-cheating violation state
  const [isViolated, setIsViolated] = useState(false);
  const [violationData, setViolationData] = useState(null);
  const violationHandledRef = useRef(false);
  const sessionIdRef = useRef('');

  useEffect(() => {
    sessionIdRef.current = sessionId;
  }, [sessionId]);

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
  const conversationStateRef = useRef(conversationState);
  const loadingRef = useRef(loading);
  const micMutedRef = useRef(micMuted);
  const inputModeRef = useRef(inputMode);
  const frameSnapshotsRef = useRef([]);
  const frameSamplingIntervalRef = useRef(null);
  const skipSpeechListenAfterRef = useRef(false);
  const autoSubmittedIdxRef = useRef(null);

  // Keyboard typing monitor & proctoring flags for gaze tracking
  const [isActivelyTyping, setIsActivelyTyping] = useState(false);
  const lastTypingTimestampRef = useRef(0);
  const sessionProctoringFlagsRef = useRef(new Set());

  // Global & Monaco keyboard typing monitor for keyboard exception in gaze tracking
  useEffect(() => {
    const handleKeyDown = () => {
      lastTypingTimestampRef.current = Date.now();
      setIsActivelyTyping(true);
    };

    window.addEventListener('keydown', handleKeyDown, { passive: true });

    const interval = setInterval(() => {
      const elapsed = Date.now() - lastTypingTimestampRef.current;
      if (elapsed >= 3500) {
        setIsActivelyTyping(false);
      }
    }, 500);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      clearInterval(interval);
    };
  }, []);

  const handleFaceStatusChange = useCallback((status) => {
    if (!status) return;
    if (Array.isArray(status.redFlags)) {
      status.redFlags.forEach((f) => {
        // Only collect genuine security flags (e.g. camera disabled), not natural keyboard/reading behavior
        if (f && f !== 'downward_gaze_without_typing' && f !== 'sustained_gaze_deviation') {
          sessionProctoringFlagsRef.current.add(f);
        }
      });
    }

    if (cameraOff) return;

    if (status.isOccluded || status.gaze === 'eyes_hidden') {
      setVisionWarning({
        type: 'eye_occlusion',
        title: 'Eyes Covered / Hidden',
        message: 'Kindly keep your eyes visible toward the camera and screen for AI proctoring verification.',
      });
    } else if (status.gaze === 'turned_side') {
      setVisionWarning({
        type: 'turned_side',
        title: 'Head Turned Away',
        message: 'Kindly face toward the interview screen and workspace.',
      });
    } else if (!status.detected) {
      setVisionWarning({
        type: 'face_missing',
        title: 'Face Not Detected',
        message: 'Kindly position your face within the camera view.',
      });
    } else {
      setVisionWarning((prev) => {
        if (!prev || prev.type === 'camera_off') {
          return prev;
        }
        return null;
      });
    }
  }, [cameraOff]);

  // ── Tab Switching & Window Focus Integrity Violation Monitor ───────────
  const handleViolation = useCallback(
    async (
      type = 'TAB_SWITCHING',
      reason = 'Candidate switched tabs during the live proctored interview. Cheating violation.'
    ) => {
      if (violationHandledRef.current) return;
      violationHandledRef.current = true;

      // 1. Immediately abort media streams
      if (mediaStreamRef.current) {
        try {
          mediaStreamRef.current.getTracks().forEach((track) => track.stop());
        } catch (e) {
          console.warn('Error stopping media tracks on violation:', e);
        }
      }

      // 2. Stop TTS synthesis
      if (ttsAudioRef.current) {
        try {
          ttsAudioRef.current.pause();
        } catch {}
      }
      if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
        try {
          window.speechSynthesis.cancel();
        } catch {}
      }

      // 3. Stop speech recognition and clear sampling intervals
      if (recognitionRef.current) {
        try {
          recognitionRef.current.abort();
        } catch {}
      }
      if (liveTranscriptionIntervalRef.current) {
        clearInterval(liveTranscriptionIntervalRef.current);
      }
      if (frameSamplingIntervalRef.current) {
        clearInterval(frameSamplingIntervalRef.current);
      }
      if (restartListeningTimeoutRef.current) {
        clearTimeout(restartListeningTimeoutRef.current);
      }

      setIsListening(false);
      setIsSpeakingQuestion(false);
      setConversationState('idle');
      setIsViolated(true);
      setViolationData({
        type,
        reason:
          'You have violated interview integrity policies and cheated by switching tabs. Tab switching is strictly prohibited. You are blacklisted, and this interview has been cancelled.',
      });

      const currentSid = sessionIdRef.current || sessionId;
      if (currentSid) {
        try {
          await interviewService.reportViolation(currentSid, {
            violation_type: type,
            reason,
          });
        } catch (err) {
          console.error('Failed to notify backend of violation:', err);
        }
      }
    },
    [sessionId]
  );

  useEffect(() => {
    // Only monitor tab switching during an active interview session
    if (!sessionId || questions.length === 0 || report || isViolated) {
      return;
    }

    const onVisibilityChange = () => {
      if (document.hidden || document.visibilityState === 'hidden') {
        handleViolation(
          'TAB_SWITCHING',
          'Candidate switched tabs during the live proctored interview. Cheating violation.'
        );
      }
    };

    const onWindowBlur = () => {
      if (document.hidden || !document.hasFocus()) {
        handleViolation(
          'TAB_SWITCHING',
          'Candidate switched away from the active interview window. Cheating violation.'
        );
      }
    };

    document.addEventListener('visibilitychange', onVisibilityChange);
    window.addEventListener('blur', onWindowBlur);

    return () => {
      document.removeEventListener('visibilitychange', onVisibilityChange);
      window.removeEventListener('blur', onWindowBlur);
    };
  }, [sessionId, questions.length, report, isViolated, handleViolation]);

  // Initialize theme from localStorage
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const savedTheme = localStorage.getItem('hiresight_interview_theme');
      if (savedTheme === 'dark' || savedTheme === 'light') {
        setTheme(savedTheme);
      } else {
        setTheme('light');
      }
    }
  }, []);


  const toggleTheme = useCallback(() => {
    setTheme((prev) => {
      const next = prev === 'light' ? 'dark' : 'light';
      if (typeof window !== 'undefined') {
        localStorage.setItem('hiresight_interview_theme', next);
      }
      return next;
    });
  }, []);

  const isLight = theme === 'light';

  const currentQuestion = useMemo(
    () => questions[currentIdx] || null,
    [questions, currentIdx]
  );

  const resolveStageFromQuestion = useCallback(
    (question, idx) => {
      if (!question) return 'introduction';
      const explicit = (question?.stage || '').toLowerCase().trim();
      const type = (question?.question_type || '').toLowerCase().trim();
      const text = (question?.question_text || '').toLowerCase();

      const normalize = (val) => {
        if (!val) return '';
        if (val === 'icebreaker' || val === 'intro' || val === 'introduction' || val === 'cv_overview') return 'introduction';
        if (val === 'system_design' || val === 'architecture' || val === 'sys_design') return 'system_design';
        if (val === 'core_technical' || val === 'technical' || val === 'tech' || val === 'deep_dive' || val === 'cv_based') return 'technical';
        if (val === 'coding' || val === 'code_sandbox') return 'coding';
        if (val === 'behavioral' || val === 'situational' || val === 'star' || val === 'leadership') return 'behavioral';
        if (val === 'closing' || val === 'wrap_up' || val === 'conclusion') return 'wrap_up';
        return '';
      };

      if (question.parent_question_id && Array.isArray(questions)) {
        const parent = questions.find((q) => q?.question_id === question.parent_question_id);
        if (parent) {
          const parentNorm = normalize(parent?.stage) || normalize(parent?.question_type);
          if (parentNorm) return parentNorm;
        }
      }

      if (question?.coding_challenge || type === 'coding' || explicit === 'coding') return 'coding';

      const fromExplicit = normalize(explicit);
      if (fromExplicit) return fromExplicit;

      const fromType = normalize(type);
      if (fromType) return fromType;

      if (text.includes('system design') || text.includes('architecture') || text.includes('high-volume') || text.includes('scalability')) {
        return 'system_design';
      }

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

  const currentStageKey = useMemo(() => {
    return resolveStageFromQuestion(currentQuestion, currentIdx);
  }, [currentQuestion, currentIdx, resolveStageFromQuestion]);

  const isCodingPhase = useMemo(
    () => currentStageKey === 'coding' || (currentQuestion?.question_type || '').toLowerCase() === 'coding' || !!currentQuestion?.coding_challenge,
    [currentStageKey, currentQuestion]
  );

  const currentStageObj = useMemo(() => {
    return CANONICAL_STAGES.find((s) => s.key === currentStageKey) || CANONICAL_STAGES[0];
  }, [currentStageKey]);

  const currentStageLabel = currentStageObj.fullLabel;

  /** Time limit allocated for the active question */
  const questionAllocatedTime = useMemo(() => {
    if (isCodingPhase || currentQuestion?.coding_challenge) return 600; // 10 min for coding
    if (currentStageKey === 'system_design') return 240; // 4 min
    if (currentStageKey === 'introduction') return 120; // 2 min
    if (currentStageKey === 'technical') return 150; // 2.5 min
    if (currentStageKey === 'behavioral') return 150; // 2.5 min
    if (currentStageKey === 'wrap_up') return 120; // 2 min
    return currentStageObj.timeSec || 150;
  }, [currentStageKey, isCodingPhase, currentQuestion, currentStageObj]);

  const isInterviewerSpeaking = useMemo(() => {
    return isSpeakingQuestion || conversationState === 'asking';
  }, [isSpeakingQuestion, conversationState]);

  /** Live countdown timer remaining in seconds for the current question */
  const remainingQuestionSec = useMemo(() => {
    if (isInterviewerSpeaking) return questionAllocatedTime;
    return Math.max(0, questionAllocatedTime - questionTimerSec);
  }, [questionAllocatedTime, questionTimerSec, isInterviewerSpeaking]);

  /** Total interview budget in seconds across all curriculum questions */
  const totalInterviewBudgetSec = useMemo(() => {
    if (!Array.isArray(questions) || questions.length === 0) return 1800; // 30 min default
    return questions.reduce((sum, q, idx) => {
      const stage = resolveStageFromQuestion(q, idx);
      const isCoding = stage === 'coding' || !!q?.coding_challenge || (q?.question_type || '').toLowerCase() === 'coding';
      if (isCoding) return sum + 600; // 10 min
      if (stage === 'system_design') return sum + 240; // 4 min
      if (stage === 'introduction') return sum + 120; // 2 min
      if (stage === 'wrap_up') return sum + 120; // 2 min
      return sum + 150; // 2.5 min
    }, 0);
  }, [questions, resolveStageFromQuestion]);

  /** Total remaining time for the entire interview session */
  const totalInterviewRemainingSec = useMemo(() => {
    return Math.max(0, totalInterviewBudgetSec - elapsedSec);
  }, [totalInterviewBudgetSec, elapsedSec]);

  /** Progress percentage remaining for linear bar */
  const questionProgressPct = useMemo(() => {
    if (questionAllocatedTime <= 0 || isInterviewerSpeaking) return 100;
    return Math.max(0, Math.min(100, (remainingQuestionSec / questionAllocatedTime) * 100));
  }, [remainingQuestionSec, questionAllocatedTime, isInterviewerSpeaking]);

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

  /** Smart key focal points for the question */
  const questionKeyPoints = useMemo(() => {
    if (!currentQuestion) return [];
    if (Array.isArray(currentQuestion.key_points) && currentQuestion.key_points.length > 0) {
      return currentQuestion.key_points.slice(0, 4);
    }
    if (currentQuestion.rubric && typeof currentQuestion.rubric === 'object') {
      const keys = Object.keys(currentQuestion.rubric);
      if (keys.length > 0) {
        return keys.slice(0, 3).map((k) => k.replace(/_/g, ' '));
      }
    }
    const qType = (currentQuestion.question_type || '').toLowerCase();
    if (qType === 'coding' || currentQuestion.coding_challenge) {
      return ['Implementation correctness', 'Edge cases & constraints', 'Algorithm efficiency'];
    }
    if (currentStageKey === 'system_design') {
      return ['End-to-end architecture', 'Service boundaries & data flow', 'Fault tolerance & scaling'];
    }
    if (currentStageKey === 'technical') {
      return ['Core mechanics & implementation', 'Trade-offs & alternatives', 'Production reliability'];
    }
    if (currentStageKey === 'behavioral') {
      return ['Situation & challenge context', 'Concrete actions taken', 'Measurable impact'];
    }
    return ['Key architectural choices', 'Trade-offs & alternatives', 'Production reliability'];
  }, [currentQuestion, currentStageKey]);

  // Reset timer on question change
  useEffect(() => {
    setQuestionTimerSec(0);
    autoSubmittedIdxRef.current = null;
    setAutoTransitionActive(false);
    setTransitionStatusText('');
  }, [currentIdx]);

  // Question timer ticker - only runs when candidate is answering
  useEffect(() => {
    if (
      !sessionId ||
      report ||
      isInterviewerSpeaking ||
      conversationState === 'processing'
    ) {
      return;
    }
    const interval = setInterval(() => {
      setQuestionTimerSec((s) => s + 1);
    }, 1000);
    return () => clearInterval(interval);
  }, [sessionId, report, isInterviewerSpeaking, conversationState, currentIdx]);

  // Total session elapsed timer ticker
  useEffect(() => {
    if (!sessionId || report) return;
    const id = setInterval(() => setElapsedSec((s) => s + 1), 1000);
    return () => clearInterval(id);
  }, [sessionId, report]);

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
      // Voice-only interview response mode: typing answers is disabled
      if (newMode !== 'voice') return;
      if (conversationStateRef.current === 'listening' && !micMutedRef.current) {
        startListening();
      }
      setInputMode('voice');
    },
    []
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
      .catch(() => { });
  }, []);

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
    micMutedRef.current = micMuted;
  }, [micMuted]);

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
  }, []);

  useEffect(() => {
    if (isCodingPhase) {
      stopListening();
    }
  }, [isCodingPhase, currentIdx]);

  // Continuous Real-Time Camera Feed & Computer Vision Health Monitor
  useEffect(() => {
    const checkVisionHealth = () => {
      // 1. If user explicitly toggled camera off
      if (cameraOff) {
        setVisionWarning({
          type: 'camera_off',
          title: 'Camera is Turned Off',
          message: 'Kindly turn on your camera. Computer vision requires live video for facial engagement and proctoring verification.',
        });
        return;
      }

      const stream = mediaStreamRef.current;
      // 2. If media stream or video tracks are missing/ended
      if (!stream || stream.getVideoTracks().length === 0 || !stream.getVideoTracks().some((t) => t.enabled && t.readyState === 'live')) {
        setVisionWarning({
          type: 'camera_off',
          title: 'Camera Feed Unavailable',
          message: 'No video feed detected. Kindly allow camera access or turn on your webcam.',
        });
        return;
      }

      // 3. Analyze live frame from video element
      const video = videoRef.current;
      if (video && video.videoWidth > 0 && video.videoHeight > 0) {
        try {
          const testCanvas = document.createElement('canvas');
          testCanvas.width = 64;
          testCanvas.height = 48;
          const ctx = testCanvas.getContext('2d', { willReadFrequently: true });
          if (ctx) {
            ctx.drawImage(video, 0, 0, 64, 48);
            const imgData = ctx.getImageData(0, 0, 64, 48).data;
            let totalLum = 0;
            let totalSq = 0;
            const pixelCount = 64 * 48;
            for (let i = 0; i < imgData.length; i += 4) {
              const lum = 0.299 * imgData[i] + 0.587 * imgData[i + 1] + 0.114 * imgData[i + 2];
              totalLum += lum;
              totalSq += lum * lum;
            }
            const meanLum = totalLum / pixelCount;
            const variance = (totalSq / pixelCount) - (meanLum * meanLum);
            const stdDev = Math.sqrt(Math.max(0, variance));

            if (meanLum < 32) {
              setVisionWarning({
                type: 'weak_lighting',
                title: 'Camera Feed is Dark / Covered',
                message: 'Your camera feed is too dark or shutter is closed. Kindly turn on room lighting or uncover your webcam for computer vision facial analysis.',
              });
            } else if (stdDev < 10) {
              setVisionWarning({
                type: 'weak_camera',
                title: 'Camera Result is Weak / Blurry',
                message: 'Camera image is low quality or obstructed. Kindly adjust your webcam angle and lighting for clear facial analysis.',
              });
            } else {
              setVisionWarning((prev) => (prev?.type === 'camera_off' ? prev : null));
            }
          }
        } catch { }
      }
    };

    checkVisionHealth();
    const intervalId = setInterval(checkVisionHealth, 800);
    return () => clearInterval(intervalId);
  }, [cameraOff]);

  /** Persistent video ref callback to guarantee stream is always attached when DOM element mounts */
  const attachVideoElement = useCallback((node) => {
    videoRef.current = node;
    if (node && mediaStreamRef.current) {
      if (node.srcObject !== mediaStreamRef.current) {
        node.srcObject = mediaStreamRef.current;
      }
      if (!cameraOff) {
        node.play().catch(() => { });
      }
    }
  }, [cameraOff]);

  /** Re-sync video playback and stream on question or phase change */
  useEffect(() => {
    if (videoRef.current && mediaStreamRef.current) {
      if (videoRef.current.srcObject !== mediaStreamRef.current) {
        videoRef.current.srcObject = mediaStreamRef.current;
      }
      if (!cameraOff) {
        videoRef.current.play().catch(() => { });
      }
    }
  }, [isCodingPhase, currentIdx, cameraOff]);

  /** Continuous Computer Vision Frame Sampling (Active for both Voice and Text answering modes) */
  useEffect(() => {
    if (!sessionId || !currentQuestion || Boolean(report) || cameraOff) {
      if (frameSamplingIntervalRef.current) {
        clearInterval(frameSamplingIntervalRef.current);
        frameSamplingIntervalRef.current = null;
      }
      return;
    }

    const capturePeriodicSample = async () => {
      if (conversationStateRef.current === 'processing' || cameraOff) return;
      try {
        const frameBlob = await captureFrame();
        if (frameBlob) {
          const b64 = await blobToBase64(frameBlob);
          if (b64) {
            frameSnapshotsRef.current.push(b64);
            if (frameSnapshotsRef.current.length > 8) {
              frameSnapshotsRef.current.shift();
            }
          }
        }
      } catch { }
    };

    capturePeriodicSample();
    const interval = setInterval(capturePeriodicSample, 1600);
    frameSamplingIntervalRef.current = interval;

    return () => {
      clearInterval(interval);
      frameSamplingIntervalRef.current = null;
    };
  }, [sessionId, currentIdx, report, cameraOff, currentQuestion]);

  const cleanupMedia = () => {
    if (animFrameRef.current) {
      cancelAnimationFrame(animFrameRef.current);
      animFrameRef.current = null;
    }
    if (audioContextRef.current) {
      audioContextRef.current.close().catch(() => { });
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
      console.warn('Audio autoplay notice:', err);
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

  /** Instant, snappy speech synthesis for zero-delay question transitions */
  const speakQuestion = async (text, metaQuestion = null) => {
    if (!text) return;
    const isCodingQ =
      metaQuestion &&
      ((metaQuestion.question_type || '').toLowerCase() === 'coding' ||
        (metaQuestion.stage || '').toLowerCase() === 'coding' ||
        Boolean(metaQuestion.coding_challenge));
    skipSpeechListenAfterRef.current = !!isCodingQ;

    let textToSpeak = text;
    if (isCodingQ || metaQuestion?.coding_challenge) {
      const challengeTitle = metaQuestion?.coding_challenge?.title || 'hands-on problem';
      textToSpeak = `Here is your coding challenge: ${challengeTitle}. Please review the problem description and constraints below, and write your solution in the code editor.`;
    }

    stopQuestionSpeech();
    stopListening();
    setIsSpeakingQuestion(true);
    conversationStateRef.current = 'asking';
    setConversationState('asking');

    // Fast Race: Try TTS with low latency timeout, fallback immediately to instant browser speech
    try {
      const ttsPromise = interviewService.tts(textToSpeak);
      const timeoutPromise = new Promise((_, reject) =>
        setTimeout(() => reject(new Error('TTS timeout')), 350)
      );
      const tts = await Promise.race([ttsPromise, timeoutPromise]);
      if (tts?.audio_base64) {
        playAudioFromBase64(tts.audio_base64);
        return;
      }
    } catch {
      // Instant browser speech synthesis fallback
    }

    if (typeof window !== 'undefined' && window.speechSynthesis) {
      const utterance = new SpeechSynthesisUtterance(textToSpeak);
      utterance.rate = 1.05;
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
        try {
          const audioStream = await navigator.mediaDevices.getUserMedia({ audio: true });
          let videoStream = null;
          try {
            videoStream = await navigator.mediaDevices.getUserMedia({ video: true });
          } catch {
            console.warn('Camera not available, proceeding with audio');
          }

          if (videoStream) {
            stream = new MediaStream([
              ...audioStream.getAudioTracks(),
              ...videoStream.getVideoTracks(),
            ]);
          } else {
            stream = audioStream;
          }
        } catch {
          throw new Error('Microphone access is required for the live interview.');
        }
      }

      mediaStreamRef.current = stream;
      setError('');

      if (videoRef.current && stream.getVideoTracks().length > 0) {
        videoRef.current.srcObject = stream;
        try {
          await new Promise((resolve) => {
            videoRef.current.onloadedmetadata = () => {
              videoRef.current.play().catch(() => { });
              resolve();
            };
            setTimeout(resolve, 1000);
          });
        } catch { }
      } else if (stream.getVideoTracks().length === 0) {
        setCameraOff(true);
        setVisionWarning({
          type: 'camera_off',
          title: 'Camera Not Connected',
          message: 'Camera permission was not granted or webcam is unavailable. Kindly allow camera permissions and turn on your camera.',
        });
      }

      // Initialize Live Audio Meter
      try {
        const AudioCtx = window.AudioContext || window.webkitAudioContext;
        if (AudioCtx && stream.getAudioTracks().length > 0) {
          if (audioContextRef.current) {
            audioContextRef.current.close().catch(() => { });
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
        console.warn('Audio meter init note:', audioErr);
      }

      if (!faceRegistered && sessionId && stream.getVideoTracks().length > 0) {
        setTimeout(() => registerFaceAutomatically(), 1500);
      }

      if (
        conversationStateRef.current === 'listening' &&
        !micMutedRef.current &&
        inputModeRef.current === 'voice'
      ) {
        startListening();
      }

      return true;
    } catch (err) {
      console.error('Media init error:', err);
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
      console.error('Face verification init note:', err);
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

    const audioTracks = mediaStreamRef.current ? mediaStreamRef.current.getAudioTracks() : [];
    if (audioTracks.length > 0) {
      try {
        audioTracks.forEach((t) => {
          t.enabled = true;
        });

        if (!mediaRecorderRef.current || mediaRecorderRef.current.state === 'inactive') {
          audioChunksRef.current = [];
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
        console.warn('MediaRecorder notice:', mrErr);
      }
    }

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
              } catch { }
            }

            if (audioChunksRef.current && audioChunksRef.current.length > 2) {
              const mime = audioChunksRef.current[0]?.type || 'audio/webm';
              const audioBlob = new Blob(audioChunksRef.current, { type: mime });
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
                  return words.every((w) => hallucinationTokens.has(w));
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
            console.warn('Live transcribe chunk note:', e);
          } finally {
            isTranscribingChunkRef.current = false;
          }
        }
      }, 3500);
    }

    if (typeof window === 'undefined') return;
    if (webSpeechDisabledRef.current) return;
    const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
    if (!SpeechRecognition) {
      setSpeechNotice('Speech captured directly via high-accuracy backend AI Whisper model.');
      return;
    }

    try {
      if (recognitionRef.current) {
        try {
          recognitionRef.current.onend = null;
          recognitionRef.current.onerror = null;
          recognitionRef.current.stop();
        } catch { }
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
          setSpeechNotice('Live speech transcribed via backend Whisper AI.');
          return;
        }
      };

      recognition.onend = () => {
        if (finalTranscriptRef.current) {
          accumulatedFinalRef.current = finalTranscriptRef.current;
        }
        if (recognitionRef.current === recognition) {
          recognitionRef.current = null;
        }
        if (webSpeechDisabledRef.current) return;
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
              } catch { }
            }
          }, 200);
        }
      };

      recognitionRef.current = recognition;
      recognition.start();
    } catch { }
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
      } catch { }
      mediaRecorderRef.current = null;
    }

    if (recognitionRef.current) {
      try {
        recognitionRef.current.onend = null;
        recognitionRef.current.onerror = null;
        recognitionRef.current.onresult = null;
        recognitionRef.current.stop();
      } catch { }
      recognitionRef.current = null;
    }
    setIsListening(false);
    setLiveTranscript('');
  };

  const captureFrame = () =>
    new Promise((resolve) => {
      const video = videoRef.current;
      if (!video || !video.videoWidth || !video.videoHeight) {
        resolve(null);
        return;
      }

      try {
        const maxWidth = 540;
        const scale = Math.min(1.0, maxWidth / (video.videoWidth || 540));
        const canvas = document.createElement('canvas');
        canvas.width = Math.round((video.videoWidth || 540) * scale);
        canvas.height = Math.round((video.videoHeight || 380) * scale);

        const ctx = canvas.getContext('2d');
        if (!ctx) {
          resolve(null);
          return;
        }

        ctx.drawImage(video, 0, 0, canvas.width, canvas.height);
        canvas.toBlob((blob) => {
          if (blob) {
            resolve(blob);
          } else {
            resolve(null);
          }
        }, 'image/jpeg', 0.75);
      } catch {
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

      if (state.is_violated || state.status === 'cancelled' || state.status === 'blacklisted') {
        violationHandledRef.current = true;
        setIsViolated(true);
        setViolationData({
          type: state.violation_type || 'TAB_SWITCHING',
          reason:
            state.violation_reason ||
            'You have violated interview integrity policies and cheated by switching tabs. Tab switching is strictly prohibited. You are blacklisted, and this interview has been cancelled.',
        });
        setLoading(false);
        return;
      }

      if (state.status === 'completed' || state.current_question_index >= state.total_questions) {
        try {
          const finalReport = await interviewService.getReport(targetSessionId);
          setReport(finalReport);
        } catch {
          try {
            const finalReport = await interviewService.endSession(targetSessionId);
            setReport(finalReport);
          } catch (endErr) {
            console.warn('Final report notice:', endErr);
          }
        }
        setLoading(false);
        return;
      }

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

      const mediaReady = await initializeMedia();
      const currentQ =
        loadedQuestions[state.current_question_index] || state.current_question;
      if (mediaReady && currentQ) {
        setTimeout(() => speakQuestion(currentQ.question_text, currentQ), 300);
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

      const mediaReady = await initializeMedia();
      if (mediaReady && data.questions?.length > 0) {
        setTimeout(() => speakQuestion(data.questions[0].question_text, data.questions[0]), 300);
      }
    } catch (err) {
      if (
        err.response?.status === 403 &&
        String(err.response?.data?.detail).toLowerCase().includes('blacklisted')
      ) {
        violationHandledRef.current = true;
        setIsViolated(true);
        setViolationData({
          type: 'BLACKLISTED',
          reason: err.response.data.detail,
        });
      }
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
  }, [router.isReady, router.query, sessionId]);

  const handleSubmitAnswer = () => {
    if (isViolated || violationHandledRef.current) return;
    let transcript = displayTranscript.trim();

    if (!transcript && isCodingPhase) {
      transcript =
        '[Coding round] Candidate continued in the code editor; verbal walkthrough optional.';
    }

    if (!transcript) {
      setError('Please speak your answer aloud before submitting.');
      return;
    }

    submitAnswer(transcript);
  };

  /** Fast, optimized answer submission pipeline */
  const submitAnswer = async (transcript) => {
    if (isViolated || violationHandledRef.current) return;
    if (!sessionId || !currentQuestion) return;

    if (mediaRecorderRef.current && mediaRecorderRef.current.state === 'recording') {
      try {
        mediaRecorderRef.current.requestData();
      } catch { }
    }

    stopListening();
    conversationStateRef.current = 'processing';
    setConversationState('processing');
    setLoading(true);
    setError('');

    try {
      let currentFrameBase64 = '';
      try {
        const frame = await captureFrame();
        if (frame) {
          currentFrameBase64 = await blobToBase64(frame);
        }
      } catch { }

      const allFrames = [];
      if (frameSnapshotsRef.current && frameSnapshotsRef.current.length > 0) {
        allFrames.push(...frameSnapshotsRef.current);
      }
      if (currentFrameBase64) {
        allFrames.push(currentFrameBase64);
      }
      frameSnapshotsRef.current = [];

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
      audioChunksRef.current = [];

      const payload = {
        question_index: currentIdx,
        audio_base64: audioBase64,
        transcript_text: transcript || null,
        audio_format: audioFormat,
        language: 'en',
        frame_base64_list: allFrames,
        is_actively_typing: isActivelyTyping || isCodingPhase,
        proctoring_flags: Array.from(sessionProctoringFlagsRef.current || []),
      };

      sessionProctoringFlagsRef.current = new Set();

      const score = await interviewService.submitAnswer(sessionId, payload);

      setLastScore({
        ...score,
        details: {
          transcript: score.transcript,
          evaluation: score.evaluation,
        },
      });

      setLiveTranscript('');
      setFinalTranscript('');
      setTextAnswer('');

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

      const hasMoreQuestions = currentIdx < updatedQuestions.length - 1;

      if (hasMoreQuestions) {
        const nextIdx = currentIdx + 1;
        setCurrentIdx(nextIdx);
        setAutoTransitionActive(false);
        setTransitionStatusText('');
        const nextQ = updatedQuestions[nextIdx];
        if (nextQ) {
          speakQuestion(nextQ.question_text, nextQ);
        }
      } else {
        const finalReport = await interviewService.endSession(sessionId);
        setReport(finalReport);
        setAutoTransitionActive(false);
        setTransitionStatusText('');
        setConversationState('idle');
        stopListening();
      }
    } catch (err) {
      console.error('Error submitting answer:', err);
      setAutoTransitionActive(false);
      setTransitionStatusText('');
      const detailStr = formatApiDetail(err.response?.data?.detail) || '';
      if (
        err.response?.status === 403 &&
        detailStr.toLowerCase().includes('blacklisted')
      ) {
        violationHandledRef.current = true;
        setIsViolated(true);
        setViolationData({
          type: 'BLACKLISTED',
          reason: detailStr,
        });
        return;
      }
      if (
        detailStr.toLowerCase().includes('already been answered') ||
        detailStr.toLowerCase().includes('out of order') ||
        detailStr.toLowerCase().includes('invalid question index')
      ) {
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

  /** Prominent auto-transition effect when timer runs out (00:00) */
  useEffect(() => {
    if (
      !sessionId ||
      !currentQuestion ||
      report ||
      isInterviewerSpeaking ||
      conversationState === 'processing' ||
      loadingRef.current
    ) {
      return;
    }
    if (remainingQuestionSec <= 0) {
      if (autoSubmittedIdxRef.current === currentIdx) return;
      autoSubmittedIdxRef.current = currentIdx;

      setAutoTransitionActive(true);
      setTransitionStatusText(
        `Time expired for Question ${currentIdx + 1}. Auto-submitting response and advancing to next question…`
      );

      let draft = (finalTranscriptRef.current || '').trim();
      if (!draft && textAnswer) {
        draft = textAnswer.trim();
      }

      if (!draft) {
        if (isCodingPhase) {
          draft = '[Auto-Submission: Coding round timer expired. Solution submitted from editor.]';
        } else {
          draft = `[Auto-Submission: Allocated time expired for this question. Auto-advancing to next phase.]`;
        }
      }

      const timerId = setTimeout(() => {
        submitAnswer(draft);
      }, 500);

      return () => clearTimeout(timerId);
    }
  }, [
    remainingQuestionSec,
    sessionId,
    currentQuestion,
    report,
    isInterviewerSpeaking,
    conversationState,
    currentIdx,
    isCodingPhase,
    textAnswer,
  ]);

  const confirmSkipQuestion = async () => {
    setShowSkipModal(false);
    if (loading || !sessionId || !currentQuestion) return;
    setError('');
    setAutoTransitionActive(true);
    setTransitionStatusText(`Skipping Question ${currentIdx + 1} and advancing to next question…`);
    stopQuestionSpeech();
    stopListening();
    conversationStateRef.current = 'processing';
    setConversationState('processing');
    setLiveTranscript('');
    setFinalTranscript('');
    await submitAnswer(SKIP_QUESTION_TRANSCRIPT);
  };

  const confirmLeaveInterview = async () => {
    setShowLeaveModal(false);
    stopListening();
    stopQuestionSpeech();
    cleanupMedia();
    try {
      if (sessionId) await interviewService.endSession(sessionId);
    } catch { }
    router.push('/dashboard');
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
    if (nextOff) {
      setVisionWarning({
        type: 'camera_off',
        title: 'Camera is Off',
        message: 'Kindly turn on your camera. Computer vision requires live video for facial engagement and proctoring verification.',
      });
    } else {
      setVisionWarning(null);
    }
  }, [cameraOff]);

  return (
    <div
      className={`min-h-screen flex flex-col font-sans transition-colors duration-200 ${
        isLight
          ? 'bg-[#F8FAFC] text-slate-900 selection:bg-indigo-600 selection:text-white'
          : 'bg-[#0B1120] text-slate-100 selection:bg-indigo-500 selection:text-white'
      }`}
    >
      {/* Top Navigation Bar */}
      <header
        className={`sticky top-0 z-30 border-b backdrop-blur-md transition-colors ${
          isLight
            ? 'border-slate-200/90 bg-white/95 shadow-xs'
            : 'border-white/10 bg-[#0B1120]/95'
        }`}
      >
        <div className="mx-auto flex max-w-[1600px] items-center justify-between gap-3 px-4 py-2.5 sm:px-6">
          {/* Left: Brand + Role Title */}
          <div className="flex min-w-0 items-center gap-3">
            <div className="flex items-center gap-2">
              <div
                className={`flex h-8 w-8 items-center justify-center rounded-xl font-bold shadow-xs ${
                  isLight
                    ? 'bg-indigo-600 text-white'
                    : 'bg-indigo-600/20 border border-indigo-500/40 text-indigo-400'
                }`}
              >
                <Sparkles className="h-4 w-4" />
              </div>
              <span
                className={`text-base font-bold tracking-tight ${
                  isLight ? 'text-slate-900' : 'text-white'
                }`}
              >
                HireSight
              </span>
            </div>

            {jobRoleLabel && (
              <>
                <span className={isLight ? 'text-slate-300 font-light text-lg' : 'text-slate-600 font-light text-lg'}>
                  |
                </span>
                <div className="hidden sm:flex items-center gap-1.5 text-sm">
                  <span className={`font-semibold ${isLight ? 'text-slate-900' : 'text-slate-100'}`}>
                    {jobRoleLabel}
                  </span>
                  <span className={isLight ? 'text-slate-500 font-normal' : 'text-slate-400 font-normal'}>
                    interview
                  </span>
                </div>
              </>
            )}
          </div>

          {/* Center: Proctoring Active Warning */}
          {sessionId && !report && !isViolated && (
            <div className="hidden lg:flex items-center gap-2 rounded-full border border-amber-300 bg-amber-50 dark:border-amber-500/30 dark:bg-amber-500/10 px-3.5 py-1 text-xs font-semibold text-amber-800 dark:text-amber-300">
              <ShieldAlert className="h-3.5 w-3.5 text-amber-600 dark:text-amber-400 shrink-0" />
              <span>Proctored: Tab switching is strictly forbidden and triggers immediate blacklisting</span>
            </div>
          )}

          {/* Right: Comprehensive Live Timers, Status, Theme Switcher & Leave Button */}
          <div className="flex items-center gap-2 sm:gap-3">
            {sessionId && !report && currentQuestion && (
              <>
                {/* 1. Question Countdown Timer */}
                <div
                  className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-lg border font-mono text-xs sm:text-sm font-bold transition-all ${
                    isInterviewerSpeaking
                      ? isLight
                        ? 'border-indigo-200 bg-indigo-50/90 text-indigo-700'
                        : 'border-indigo-500/30 bg-indigo-950/40 text-indigo-300'
                      : remainingQuestionSec <= 10
                        ? 'border-red-400 bg-red-500/20 text-red-600 dark:text-red-300 animate-pulse'
                        : remainingQuestionSec <= 30
                          ? 'border-amber-400 bg-amber-500/15 text-amber-700 dark:text-amber-200'
                          : isLight
                            ? 'border-indigo-200 bg-indigo-50/80 text-indigo-900'
                            : 'border-white/10 bg-black/40 text-slate-200'
                  }`}
                  title={
                    isInterviewerSpeaking
                      ? 'Interviewer speaking prompt — countdown starts after speech finishes'
                      : 'Time remaining for active question'
                  }
                >
                  <Timer
                    className={`h-3.5 w-3.5 ${
                      isInterviewerSpeaking
                        ? 'text-indigo-500 animate-pulse'
                        : remainingQuestionSec <= 10
                          ? 'text-red-600 dark:text-red-400 animate-spin'
                          : remainingQuestionSec <= 30
                            ? 'text-amber-600 dark:text-amber-400'
                            : isLight
                              ? 'text-indigo-600'
                              : 'text-indigo-400'
                    }`}
                  />
                  <span>{formatMmSs(remainingQuestionSec)}</span>
                  <span className={`text-[10px] uppercase font-sans ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                    {isInterviewerSpeaking ? 'starts soon' : 'q-left'}
                  </span>
                </div>

                {/* 2. Total Remaining Interview Time */}
                <div
                  className={`flex items-center gap-1.5 px-2.5 sm:px-3 py-1 rounded-lg border font-mono text-xs font-bold ${
                    isLight
                      ? 'border-sky-200 bg-sky-50 text-sky-800'
                      : 'border-sky-500/30 bg-sky-950/40 text-sky-200'
                  }`}
                  title={`Total remaining time in complete interview (${formatMmSs(totalInterviewRemainingSec)} left of ~${formatMmSs(totalInterviewBudgetSec)})`}
                >
                  <Hourglass className="h-3.5 w-3.5 text-sky-500" />
                  <span>{formatMmSs(totalInterviewRemainingSec)}</span>
                  <span className={`text-[10px] uppercase font-sans ${isLight ? 'text-sky-600' : 'text-sky-400'}`}>
                    total left
                  </span>
                </div>

                {/* 3. Session Elapsed Time */}
                <div
                  className={`hidden md:flex items-center gap-1.5 font-mono text-xs font-medium px-2.5 py-1 rounded-lg border ${
                    isLight
                      ? 'border-slate-200 bg-slate-100 text-slate-700'
                      : 'border-white/10 bg-black/30 text-slate-400'
                  }`}
                  title={`Total session elapsed (${formatMmSs(elapsedSec)})`}
                >
                  <Clock className="h-3 w-3" />
                  <span>{formatMmSs(elapsedSec)}</span>
                </div>
              </>
            )}

            {/* Live Session Status Indicator */}
            <div
              className={`inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-xs font-medium ${
                isLight
                  ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                  : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
              }`}
            >
              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-500" />
              <span className="hidden sm:inline">Live</span>
            </div>

            {/* Theme Toggle Button */}
            <button
              type="button"
              onClick={toggleTheme}
              title={`Switch to ${isLight ? 'Dark' : 'White'} Theme`}
              className={`flex h-8 w-8 items-center justify-center rounded-xl border transition ${
                isLight
                  ? 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200 hover:text-slate-900'
                  : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
              }`}
            >
              {isLight ? <Moon className="h-4 w-4" /> : <Sun className="h-4 w-4 text-amber-300" />}
            </button>

            {/* Leave Session Button (Opens Custom Modal) */}
            {sessionId && !report && (
              <button
                type="button"
                onClick={() => setShowLeaveModal(true)}
                className={`inline-flex items-center gap-1.5 rounded-xl border px-3 py-1.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:border-red-300 hover:bg-red-50 hover:text-red-700'
                    : 'border-white/15 bg-white/5 text-slate-300 hover:bg-red-500/10 hover:border-red-500/30 hover:text-red-300'
                }`}
              >
                <LogOut className="h-3.5 w-3.5" />
                <span>Leave</span>
              </button>
            )}
          </div>
        </div>

        {/* Phase Time Remaining Linear Bar */}
        {sessionId && currentQuestion && !report && (
          <div
            className={`h-1 w-full overflow-hidden ${
              isLight ? 'bg-slate-100' : 'bg-slate-900'
            }`}
          >
            <div
              className={`h-full transition-all duration-1000 ease-linear ${
                remainingQuestionSec <= 10
                  ? 'bg-red-500'
                  : remainingQuestionSec <= 30
                    ? 'bg-amber-500'
                    : 'bg-indigo-600'
              }`}
              style={{ width: `${questionProgressPct}%` }}
            />
          </div>
        )}
      </header>

      {/* 6-Stage Progress Stepper Subheader */}
      {sessionId && currentQuestion && !report && (
        <div
          className={`border-b backdrop-blur-sm px-4 py-2.5 sm:px-6 transition-colors ${
            isLight
              ? 'border-slate-200/80 bg-white/80'
              : 'border-white/10 bg-[#080d1a]/80'
          }`}
        >
          <div className="mx-auto flex max-w-[1600px] flex-wrap items-center justify-between gap-4">
            {/* Stepper Tabs */}
            <div className="flex items-center gap-3 sm:gap-6 overflow-x-auto text-xs py-1">
              {CANONICAL_STAGES.map((s, idx) => {
                const isActive = currentStageKey === s.key;
                const stageIdx = CANONICAL_STAGES.findIndex((x) => x.key === currentStageKey);
                const isCompleted = idx < stageIdx;

                return (
                  <div key={s.key} className="relative flex items-center gap-2 pb-1 whitespace-nowrap">
                    <span
                      className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold transition ${
                        isActive
                          ? isLight
                            ? 'bg-indigo-600 text-white shadow-xs'
                            : 'bg-indigo-500 text-white'
                          : isCompleted
                            ? isLight
                              ? 'bg-emerald-100 text-emerald-800'
                              : 'bg-emerald-500/20 text-emerald-300'
                            : isLight
                              ? 'bg-slate-100 text-slate-500'
                              : 'bg-slate-800 text-slate-500'
                      }`}
                    >
                      {isCompleted ? '✓' : idx + 1}
                    </span>

                    <span
                      className={`font-medium transition ${
                        isActive
                          ? isLight
                            ? 'text-indigo-700 font-bold'
                            : 'text-indigo-300 font-semibold'
                          : isCompleted
                            ? isLight
                              ? 'text-slate-700'
                              : 'text-slate-400'
                            : isLight
                              ? 'text-slate-500'
                              : 'text-slate-500'
                      }`}
                    >
                      {s.label}
                    </span>

                    <span
                      className={`rounded px-1.5 py-0.2 font-mono text-[10px] ${
                        isActive
                          ? isLight
                            ? 'bg-indigo-100 text-indigo-800 font-semibold'
                            : 'bg-indigo-500/20 text-indigo-300'
                          : isLight
                            ? 'bg-slate-100 text-slate-500'
                            : 'bg-black/30 text-slate-500'
                      }`}
                    >
                      {s.timeBadge}
                    </span>

                    {isActive && (
                      <span
                        className={`absolute -bottom-1 left-0 right-0 h-0.5 rounded-full ${
                          isLight ? 'bg-indigo-600 shadow-xs' : 'bg-indigo-500 shadow-[0_0_8px_rgba(99,102,241,0.8)]'
                        }`}
                      />
                    )}
                  </div>
                );
              })}
            </div>

            {/* Right: Question X of Y, Total Left & Total Interview Budget */}
            <div className="flex items-center gap-3 text-xs">
              <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>
                Total Left: <strong className="text-sky-600 dark:text-sky-400 font-mono font-bold">{formatMmSs(totalInterviewRemainingSec)}</strong>
              </span>
              <span className={isLight ? 'text-slate-300' : 'text-slate-600'}>•</span>
              <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>
                Budget: <strong className={isLight ? 'text-slate-800' : 'text-slate-200'}>{formatMmSs(totalInterviewBudgetSec)}</strong>
              </span>
              <span className={isLight ? 'text-slate-300' : 'text-slate-600'}>•</span>
              <div className={`font-medium ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                Question <strong className={isLight ? 'text-slate-900 font-bold' : 'text-white font-bold'}>{overallBaseNumber}</strong> of {overallBaseTotal || 1}
              </div>
            </div>
          </div>
        </div>
      )}

      {/* PROMINENT AUTO-TRANSITION / SUBMISSION MODAL OVERLAY */}
      {autoTransitionActive && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div
            className={`w-full max-w-md rounded-2xl p-6 sm:p-7 text-center shadow-2xl border ${
              isLight
                ? 'bg-white border-amber-300 text-slate-900 ring-4 ring-amber-500/10'
                : 'bg-slate-900 border-amber-500/50 text-slate-100 ring-4 ring-amber-500/20'
            }`}
          >
            <div className="mx-auto mb-4 flex h-16 w-16 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-8 ring-amber-500/10 animate-pulse">
              <Timer className="h-8 w-8" />
            </div>

            <h3 className="text-xl font-bold tracking-tight mb-2">
              Time Expired for Question {currentIdx + 1}
            </h3>
            <p className={`text-sm leading-relaxed mb-5 ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
              {transitionStatusText || `Auto-submitting your response and advancing to Question ${currentIdx + 2}…`}
            </p>

            <div className={`rounded-xl border p-3 mb-5 text-left text-xs space-y-2 ${isLight ? 'border-slate-200 bg-slate-50 text-slate-700' : 'border-white/10 bg-black/40 text-slate-300'}`}>
              <div className="flex items-center gap-2">
                <CheckCircle2 className="h-4 w-4 text-emerald-500 shrink-0" />
                <span>Response snapshot captured</span>
              </div>
              <div className="flex items-center gap-2">
                <RefreshCw className="h-4 w-4 text-indigo-500 animate-spin shrink-0" />
                <span>Evaluating response & loading next question…</span>
              </div>
            </div>

            <div className="flex items-center justify-center gap-2 text-xs font-semibold text-indigo-600 dark:text-indigo-400">
              <RefreshCw className="h-4 w-4 animate-spin" />
              <span>Advancing now…</span>
            </div>
          </div>
        </div>
      )}

      {/* CUSTOM SKIP QUESTION CONFIRMATION MODAL */}
      {showSkipModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div
            className={`w-full max-w-md rounded-2xl p-6 sm:p-7 shadow-2xl border ${
              isLight
                ? 'bg-white border-amber-300 text-slate-900 ring-4 ring-amber-500/10'
                : 'bg-slate-900 border-amber-500/40 text-slate-100 ring-4 ring-amber-500/20'
            }`}
          >
            <div className="flex items-start gap-4 mb-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-amber-500/15 text-amber-600 dark:text-amber-400 ring-4 ring-amber-500/10">
                <SkipForward className="h-6 w-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold tracking-tight">
                  Skip Question {currentIdx + 1}?
                </h3>
                <p className={`mt-1 text-xs leading-relaxed line-clamp-2 font-mono ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  "{currentQuestion?.question_text}"
                </p>
                <p className={`mt-2 text-xs sm:text-sm leading-relaxed ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  Are you sure you want to skip this question? A skipped response will be recorded, and you will advance directly to the next question.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowSkipModal(false)}
                className={`rounded-xl border px-4 py-2.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'
                    : 'border-white/15 bg-white/5 text-slate-300 hover:bg-white/10'
                }`}
              >
                Cancel
              </button>
              <button
                type="button"
                onClick={confirmSkipQuestion}
                className="rounded-xl bg-amber-600 px-5 py-2.5 text-xs font-semibold text-white shadow-md transition hover:bg-amber-500"
              >
                Yes, Skip Question
              </button>
            </div>
          </div>
        </div>
      )}

      {/* CUSTOM LEAVE INTERVIEW CONFIRMATION MODAL */}
      {showLeaveModal && (
        <div className="fixed inset-0 z-[100] flex items-center justify-center bg-black/70 backdrop-blur-md p-4 animate-in fade-in duration-200">
          <div
            className={`w-full max-w-md rounded-2xl p-6 sm:p-7 shadow-2xl border ${
              isLight
                ? 'bg-white border-red-300 text-slate-900 ring-4 ring-red-500/10'
                : 'bg-slate-900 border-red-500/40 text-slate-100 ring-4 ring-red-500/20'
            }`}
          >
            <div className="flex items-start gap-4 mb-4">
              <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-red-500/15 text-red-600 dark:text-red-400 ring-4 ring-red-500/10">
                <AlertTriangle className="h-6 w-6" />
              </div>
              <div className="flex-1 min-w-0">
                <h3 className="text-lg font-bold tracking-tight">
                  Leave Interview Session?
                </h3>
                <p className={`mt-2 text-xs sm:text-sm leading-relaxed ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                  Are you sure you want to exit? Your answered questions have been safely recorded, and you will be returned to your candidate dashboard.
                </p>
              </div>
            </div>

            <div className="flex items-center justify-end gap-3 pt-2">
              <button
                type="button"
                onClick={() => setShowLeaveModal(false)}
                className={`rounded-xl border px-4 py-2.5 text-xs font-semibold transition ${
                  isLight
                    ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100'
                    : 'border-white/15 bg-white/5 text-slate-300 hover:bg-white/10'
                }`}
              >
                Stay in Interview
              </button>
              <button
                type="button"
                onClick={confirmLeaveInterview}
                className="rounded-xl bg-red-600 px-5 py-2.5 text-xs font-semibold text-white shadow-md transition hover:bg-red-500"
              >
                Leave Session
              </button>
            </div>
          </div>
        </div>
      )}

      {/* INTEGRITY BREACH & CHEATING VIOLATION BARRIER */}
      {isViolated && (
        <div className="fixed inset-0 z-[200] flex items-center justify-center bg-black/90 backdrop-blur-xl p-4 sm:p-6 animate-in fade-in duration-300">
          <div
            className={`w-full max-w-lg rounded-3xl p-8 sm:p-10 text-center shadow-2xl border ${
              isLight
                ? 'bg-white border-rose-300 text-slate-900 shadow-rose-950/10'
                : 'bg-slate-950 border-rose-500/40 text-slate-100 shadow-rose-950/50'
            }`}
          >
            <div className="mx-auto mb-5 flex h-20 w-20 items-center justify-center rounded-2xl bg-rose-500/15 text-rose-600 dark:text-rose-400 ring-8 ring-rose-500/10 animate-bounce">
              <ShieldAlert className="h-10 w-10 text-rose-600 dark:text-rose-400" />
            </div>

            <div className="space-y-2 mb-6">
              <span className="inline-flex items-center gap-1.5 rounded-full border border-rose-300 bg-rose-100 dark:border-rose-500/30 dark:bg-rose-500/20 px-3.5 py-1 text-xs font-bold uppercase tracking-wider text-rose-700 dark:text-rose-300">
                Integrity Violation Detected
              </span>
              <h2 className="text-2xl sm:text-3xl font-black tracking-tight text-rose-600 dark:text-rose-400">
                You Have Violated and Cheated
              </h2>
              <p className={`text-base font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                You are blacklisted, and this interview has been cancelled.
              </p>
            </div>

            <div className={`rounded-2xl border p-4 sm:p-5 mb-6 text-left text-xs space-y-3 leading-relaxed ${
              isLight ? 'border-rose-200 bg-rose-50/70 text-rose-900' : 'border-rose-900/40 bg-rose-950/20 text-rose-200'
            }`}>
              <div className="flex items-start gap-2.5">
                <AlertOctagon className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                <div>
                  <p className="font-bold text-rose-700 dark:text-rose-300">Violation Details:</p>
                  <p className="mt-0.5">{violationData?.reason || 'Tab switching detected during active proctored interview. Cheating violation.'}</p>
                </div>
              </div>
              <div className="flex items-start gap-2.5">
                <Ban className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                <div>
                  <p className="font-bold text-rose-700 dark:text-rose-300">Account Action:</p>
                  <p className="mt-0.5">Your candidate account has been permanently blacklisted. Further attempts to restart or complete this assessment are revoked.</p>
                </div>
              </div>
              <div className="flex items-start gap-2.5">
                <FileWarning className="h-4 w-4 shrink-0 text-rose-600 mt-0.5" />
                <div>
                  <p className="font-bold text-rose-700 dark:text-rose-300">Recruiter Audit Feedback:</p>
                  <p className="mt-0.5">The recruiting admin has received immediate telemetry and violation logs detailing this cheating incident, and your score has been set to 0.</p>
                </div>
              </div>
            </div>

            <button
              type="button"
              onClick={() => {
                if (typeof window !== 'undefined') {
                  authService.logout();
                }
                router.push('/login');
              }}
              className="w-full inline-flex items-center justify-center gap-2 rounded-xl bg-rose-600 py-3 text-sm font-bold text-white shadow-lg transition hover:bg-rose-500"
            >
              <LogOut className="h-4 w-4" />
              Exit & Return to Login
            </button>
          </div>
        </div>
      )}

      <main className="mx-auto max-w-[1600px] flex-1 w-full space-y-6 px-4 py-6 sm:px-6">
        {!sessionId && (
          <div
            className={`rounded-2xl border p-8 text-center max-w-lg mx-auto mt-10 shadow-xl ${
              isLight
                ? 'border-slate-200 bg-white text-slate-800 shadow-slate-200/50'
                : 'border-white/10 bg-slate-900/40 text-slate-200'
            }`}
          >
            <div className="mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-2xl bg-indigo-50 text-indigo-600 dark:bg-indigo-950 dark:text-indigo-400">
              <Sparkles className="h-6 w-6" />
            </div>
            <h2 className="text-xl font-bold mb-2">Preparing Live Interview Session</h2>
            <p className="text-sm text-slate-500 mb-6">
              AI-driven multi-phase technical assessment with live question timing, proctoring, and automated progression.
            </p>
            <button
              onClick={() => startInterview(router.query.jobPostId)}
              disabled={loading}
              className="rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-500 disabled:opacity-50"
            >
              {loading ? 'Initializing Session…' : 'Start Live Interview'}
            </button>
          </div>
        )}

        {error && (
          <div className="rounded-xl border border-red-300 bg-red-50 px-4 py-3 text-sm text-red-800 dark:border-red-400/30 dark:bg-red-500/10 dark:text-red-200">
            {error}
          </div>
        )}

        {sessionId && currentQuestion && !report && (
          <div
            className={`grid gap-6 ${
              isCodingPhase
                ? 'lg:grid-cols-[480px_1fr] xl:grid-cols-[520px_1fr]'
                : 'lg:grid-cols-[1fr_360px] xl:grid-cols-[1fr_400px]'
            }`}
          >
            {/* NON-CODING MODE: LEFT COLUMN = QUESTION CARD + ANSWER CARD */}
            {!isCodingPhase && (
              <div className="space-y-5">
                {/* Card 1: Question Card */}
                <div
                  className={`rounded-2xl border p-6 sm:p-7 shadow-xl backdrop-blur-xl space-y-5 transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5 text-slate-800'
                      : 'border-white/10 bg-slate-900/70 text-slate-100 ring-1 ring-white/5'
                  }`}
                >
                  {/* Top Badges, Phase Timer & Replay Control */}
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <div className="flex flex-wrap items-center gap-2">
                      <span
                        className={`rounded-lg border px-2.5 py-1 text-xs font-semibold ${
                          isLight
                            ? 'border-indigo-200 bg-indigo-50 text-indigo-800'
                            : 'border-indigo-400/30 bg-indigo-500/10 text-indigo-200'
                        }`}
                      >
                        {currentStageLabel}
                      </span>
                      <span
                        className={`rounded-lg border px-2.5 py-1 text-xs font-semibold ${
                          isLight
                            ? 'border-amber-200 bg-amber-50 text-amber-800'
                            : 'border-amber-400/30 bg-amber-500/10 text-amber-200'
                        }`}
                      >
                        {difficultyBadge}
                      </span>
                      {isFollowUpQuestion && (
                        <span
                          className={`rounded-lg border px-2.5 py-1 text-xs font-semibold flex items-center gap-1 ${
                            isLight
                              ? 'border-violet-200 bg-violet-50 text-violet-800'
                              : 'border-violet-400/30 bg-violet-500/15 text-violet-200'
                          }`}
                        >
                          <Sparkles className="h-3 w-3 text-violet-500" />
                          Follow-up Question
                        </span>
                      )}
                    </div>

                    <div className="flex items-center gap-3">
                      <div className="flex items-center gap-1.5 text-xs">
                        <span
                          className={`flex gap-0.5 ${conversationState === 'asking' || isSpeakingQuestion ? 'opacity-100' : 'opacity-40'}`}
                          aria-hidden
                        >
                          {[0, 1, 2, 3].map((i) => (
                            <span
                              key={i}
                              className={`w-1 rounded-full ${isLight ? 'bg-indigo-600' : 'bg-indigo-400'}`}
                              style={{
                                height: `${6 + (i % 3) * 4}px`,
                                animation:
                                  conversationState === 'asking' || isSpeakingQuestion
                                    ? 'pulse 1s ease-in-out infinite'
                                    : 'none',
                                animationDelay: `${i * 0.1}s`,
                              }}
                            />
                          ))}
                        </span>
                        <span className={`text-[11px] font-medium ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                          {conversationState === 'asking' || isSpeakingQuestion
                            ? 'Interviewer speaking…'
                            : conversationState === 'processing'
                              ? 'Evaluating answer…'
                              : 'Your turn to answer'}
                        </span>
                      </div>

                      <button
                        type="button"
                        onClick={() => speakQuestion(currentQuestion.question_text, currentQuestion)}
                        disabled={isSpeakingQuestion || loading}
                        className={`inline-flex items-center gap-1.5 text-xs font-semibold transition disabled:opacity-50 ${
                          isLight
                            ? 'text-indigo-600 hover:text-indigo-800'
                            : 'text-indigo-400 hover:text-indigo-300'
                        }`}
                      >
                        <Volume2 className="h-3.5 w-3.5" />
                        <span>Replay</span>
                      </button>
                    </div>
                  </div>

                  {/* Question Heading */}
                  <h1
                    className={`text-xl sm:text-2xl lg:text-[25px] font-bold leading-relaxed tracking-tight ${
                      isLight ? 'text-slate-900' : 'text-white'
                    }`}
                  >
                    {currentQuestion.question_text}
                  </h1>

                  {/* Context Subtitle */}
                  <p className={`text-xs sm:text-sm leading-relaxed ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                    {isFollowUpQuestion
                      ? 'The interviewer wants more depth on your last answer: be specific about trade-offs, design patterns, and concrete implementation details.'
                      : 'Structure your response clearly. Detail your technical architecture, design trade-offs, edge cases, and production reliability.'}
                  </p>

                  {/* "Cover these points in your answer" */}
                  <div
                    className={`border-t pt-4 space-y-2.5 ${
                      isLight ? 'border-slate-100' : 'border-white/10'
                    }`}
                  >
                    <p
                      className={`text-xs font-bold uppercase tracking-wider ${
                        isLight ? 'text-slate-700' : 'text-slate-300'
                      }`}
                    >
                      Cover these key focal points in your answer
                    </p>
                    <div className="flex flex-wrap gap-2">
                      {questionKeyPoints.map((pt, i) => (
                        <div
                          key={i}
                          className={`inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs shadow-xs ${
                            isLight
                              ? 'border-slate-200 bg-slate-50 text-slate-700'
                              : 'border-white/10 bg-black/40 text-slate-300'
                          }`}
                        >
                          <span
                            className={`h-2 w-2 rounded-full border ${
                              isLight ? 'border-indigo-400 bg-indigo-50' : 'border-slate-500'
                            }`}
                          />
                          <span>{pt}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Card 2: Candidate Answer Card */}
                <div
                  className={`rounded-2xl border p-5 sm:p-6 shadow-xl backdrop-blur-xl space-y-4 transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5 text-slate-800'
                      : 'border-white/10 bg-slate-900/70 text-slate-100 ring-1 ring-white/5'
                  }`}
                >
                  {/* Mode Switcher Tabs + Question Remaining Time Display */}
                  <div
                    className={`flex flex-wrap items-center justify-between gap-3 border-b pb-3 ${
                      isLight ? 'border-slate-100' : 'border-white/10'
                    }`}
                  >
                    <div
                      className={`inline-flex items-center gap-2 rounded-xl border px-3 py-1.5 text-xs font-semibold ${
                        isLight
                          ? 'border-indigo-200/90 bg-indigo-50/70 text-indigo-900'
                          : 'border-indigo-500/20 bg-indigo-950/40 text-indigo-300'
                      }`}
                    >
                      <div className="relative flex items-center justify-center">
                        <Mic className="h-3.5 w-3.5 text-indigo-500" />
                        {isListening && !micMuted && (
                          <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                        )}
                      </div>
                      <span>Voice Response (Speech-to-Text)</span>
                      <span
                        className={`inline-block h-1.5 w-1.5 rounded-full ${
                          micMuted ? 'bg-amber-400' : isListening ? 'bg-emerald-400' : 'bg-slate-400'
                        }`}
                      />
                    </div>

                    <div className="flex items-center gap-3 text-xs">
                      {/* Live Phase Remaining Countdown */}
                      <div
                        className={`flex items-center gap-1 font-semibold ${
                          isInterviewerSpeaking
                            ? isLight
                              ? 'text-indigo-600'
                              : 'text-indigo-300'
                            : remainingQuestionSec <= 10
                              ? 'text-red-600 dark:text-red-400 animate-pulse'
                              : remainingQuestionSec <= 30
                                ? 'text-amber-600 dark:text-amber-400'
                                : isLight
                                  ? 'text-indigo-700'
                                  : 'text-slate-300'
                        }`}
                      >
                        <Clock className="h-3.5 w-3.5" />
                        <span>{isInterviewerSpeaking ? 'Timer starts after question:' : 'Time remaining:'}</span>
                        <strong className="font-mono">{formatMmSs(remainingQuestionSec)}</strong>
                        {isInterviewerSpeaking && (
                          <span className="text-[10px] font-normal italic opacity-80">(paused)</span>
                        )}
                      </div>

                      {/* Mic Audio Level Visualizer */}
                      <div
                        className={`flex items-center gap-0.5 h-3.5 px-2 py-1 rounded border ${
                          isLight ? 'border-slate-200 bg-slate-50' : 'border-white/5 bg-black/40'
                        }`}
                      >
                        <span
                          className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                          style={{ height: `${Math.max(2, Math.min(10, audioLevel * 0.1))}px` }}
                        />
                        <span
                          className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                          style={{ height: `${Math.max(2, Math.min(10, audioLevel * 0.2))}px` }}
                        />
                        <span
                          className="w-1 bg-emerald-500 rounded-full transition-all duration-75"
                          style={{ height: `${Math.max(2, Math.min(10, audioLevel * 0.15))}px` }}
                        />
                      </div>
                    </div>
                  </div>

                  {/* Body: Live Speech Transcription Only (Audio Only • Read-Only) */}
                  <div className="space-y-2">
                    <div
                      className={`min-h-[190px] rounded-xl border p-4 flex flex-col justify-between transition ${
                        isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-black/40'
                      }`}
                    >
                      {speechNotice && (
                        <div
                          className={`mb-3 rounded-lg border p-2.5 text-xs ${
                            isLight
                              ? 'border-indigo-200 bg-indigo-50 text-indigo-800'
                              : 'border-indigo-500/30 bg-indigo-950/40 text-indigo-200'
                          }`}
                        >
                          <p className="leading-relaxed">{speechNotice}</p>
                        </div>
                      )}
                      {displayTranscript ? (
                        <div className="space-y-2.5">
                          <div className="flex items-center justify-between">
                            <span
                              className={`inline-flex items-center gap-1.5 px-2.5 py-0.5 rounded-md text-[11px] font-semibold ${
                                isLight
                                  ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                                  : 'bg-emerald-500/10 text-emerald-300 border border-emerald-500/20'
                              }`}
                            >
                              <Mic className="h-3 w-3 text-emerald-500 animate-pulse" />
                              <span>Live Audio Transcription (Read-Only)</span>
                            </span>
                            <span className={`text-[11px] font-medium ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                              Audio transcribed automatically · No manual editing
                            </span>
                          </div>
                          <textarea
                            value={displayTranscript}
                            readOnly={true}
                            tabIndex={-1}
                            onKeyDown={(e) => e.preventDefault()}
                            placeholder="Your spoken words will appear here automatically..."
                            className={`w-full bg-transparent text-sm leading-relaxed focus:outline-none resize-none cursor-default select-text ${
                              isLight ? 'text-slate-900' : 'text-slate-100'
                            }`}
                            rows={5}
                          />
                          {liveTranscript && (
                            <p
                              className={`text-xs italic animate-pulse ${
                                isLight ? 'text-indigo-600' : 'text-indigo-400'
                              }`}
                            >
                              Live voice stream: {liveTranscript}…
                            </p>
                          )}
                        </div>
                      ) : (
                        <div className="flex h-full min-h-[140px] flex-col items-center justify-center text-center py-4">
                          <div className="relative mb-2.5 flex items-center justify-center">
                            <div
                              className={`h-12 w-12 rounded-full border transition-all duration-150 flex items-center justify-center ${
                                audioLevel > 5
                                  ? isLight
                                    ? 'border-emerald-500 bg-emerald-100 text-emerald-700 scale-110 shadow-md shadow-emerald-500/20'
                                    : 'border-emerald-500/60 bg-emerald-500/15 scale-110 shadow-lg shadow-emerald-500/20'
                                  : isLight
                                    ? 'border-indigo-200 bg-indigo-50 text-indigo-600'
                                    : 'border-indigo-500/20 bg-indigo-500/5 text-indigo-400'
                              }`}
                            >
                              <Mic className={`h-6 w-6 transition ${audioLevel > 5 ? 'text-emerald-600' : ''}`} />
                            </div>
                          </div>
                          <p className={`text-sm font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                            {audioLevel > 5
                              ? 'Voice detected — transcribing in real time…'
                              : 'Start speaking — your answer is being captured in real time'}
                          </p>
                          <p className={`mt-1 text-xs ${isLight ? 'text-slate-500' : 'text-slate-500'}`}>
                            Speak naturally. Your acoustic delivery and transcribed answer are analyzed. Keyboard typing is disabled.
                          </p>
                        </div>
                      )}

                      <div
                        className={`flex items-center justify-between pt-2 border-t text-xs ${
                          isLight ? 'border-slate-200 text-slate-500' : 'border-white/5 text-slate-400'
                        }`}
                      >
                        <div className="flex items-center gap-2">
                          <button
                            type="button"
                            onClick={async () => {
                              if (displayTranscript.trim()) {
                                try {
                                  await navigator.clipboard.writeText(displayTranscript.trim());
                                } catch { }
                              }
                            }}
                            disabled={!displayTranscript.trim()}
                            className={`text-[11px] disabled:opacity-30 ${
                              isLight ? 'hover:text-slate-900' : 'hover:text-white'
                            }`}
                          >
                            Copy
                          </button>
                        </div>
                        <span className="font-mono text-[11px]">
                          {displayTranscript.trim().split(/\s+/).filter(Boolean).length} words
                        </span>
                      </div>
                    </div>

                    <div className={`flex items-center justify-between text-[11px] pt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      <button
                        type="button"
                        onClick={() => setShowStarGuidance(!showStarGuidance)}
                        className={`inline-flex items-center gap-1 font-medium ${
                          isLight ? 'text-indigo-600 hover:text-indigo-800' : 'text-indigo-300 hover:text-indigo-200'
                        }`}
                      >
                        <Lightbulb className="h-3 w-3 text-amber-500" />
                        <span>{showStarGuidance ? 'Hide STAR Framework' : 'STAR Answer Framework'}</span>
                      </button>
                      <span className="text-[10px] opacity-75">Voice mode active</span>
                    </div>

                    {showStarGuidance && (
                      <div
                        className={`rounded-xl border p-3 text-[11px] space-y-1 shadow-inner ${
                          isLight
                            ? 'border-indigo-100 bg-indigo-50/70 text-slate-700'
                            : 'border-indigo-400/20 bg-indigo-950/40 text-slate-300'
                        }`}
                      >
                        <p className={`font-semibold ${isLight ? 'text-indigo-900' : 'text-indigo-200'}`}>
                          STAR Framework Guide:
                        </p>
                        <p><strong className={isLight ? 'text-slate-900' : 'text-white'}>Situation &amp; Task:</strong> Define the background, scale, constraints and core problem.</p>
                        <p><strong className={isLight ? 'text-slate-900' : 'text-white'}>Action &amp; Result:</strong> Detail the architecture chosen, trade-offs made, and measured outcomes.</p>
                      </div>
                    )}
                  </div>

                  {/* Footer Action Buttons */}
                  <div className="flex flex-wrap items-center justify-between gap-3 pt-2">
                    <p className={`text-xs ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      Speak your response clearly. Speech is transcribed automatically into text.
                    </p>

                    <div className="flex items-center gap-3">
                      <button
                        type="button"
                        onClick={() => setShowSkipModal(true)}
                        disabled={loading || conversationState === 'processing'}
                        className={`rounded-xl border px-4 py-2.5 text-xs font-semibold transition disabled:opacity-40 ${
                          isLight
                            ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                            : 'border-white/15 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        Skip question
                      </button>

                      <button
                        type="button"
                        onClick={handleSubmitAnswer}
                        disabled={
                          loading ||
                          conversationState === 'processing' ||
                          !displayTranscript.trim()
                        }
                        className="inline-flex items-center gap-2 rounded-xl bg-indigo-600 px-5 py-2.5 text-xs font-semibold text-white shadow-lg shadow-indigo-600/20 transition hover:bg-indigo-500 disabled:cursor-not-allowed disabled:opacity-40"
                      >
                        {loading || conversationState === 'processing' ? (
                          <>
                            <RefreshCw className="h-3.5 w-3.5 animate-spin" />
                            <span>Evaluating…</span>
                          </>
                        ) : (
                          <>
                            <span>Submit answer</span>
                            <ArrowRight className="h-3.5 w-3.5" />
                          </>
                        )}
                      </button>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* CODING MODE: LEFT COLUMN = CAMERA + CODING DETAILS */}
            {isCodingPhase && currentQuestion.coding_challenge && (
              <div className="space-y-5">
                {/* Camera Tile in Coding Mode */}
                <div
                  className={`rounded-2xl border p-4 shadow-xl backdrop-blur-xl space-y-3 transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5'
                      : 'border-white/10 bg-slate-900/70 ring-1 ring-white/5'
                  }`}
                >
                  <div className="relative aspect-video w-full max-h-[220px] overflow-hidden rounded-xl bg-slate-950 border border-slate-800/80">
                    <video
                      ref={attachVideoElement}
                      autoPlay
                      muted
                      playsInline
                      className={`h-full w-full object-cover ${cameraOff ? 'opacity-0' : 'opacity-100'}`}
                    />
                    {cameraOff && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950 text-slate-500 z-10">
                        <div className="h-11 w-11 rounded-full bg-slate-900 border border-red-500/30 flex items-center justify-center mb-2">
                          <VideoOff className="h-5 w-5 text-red-400" />
                        </div>
                        <p className="text-xs font-semibold text-red-300">Camera Turned Off</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Turn on camera for proctoring</p>
                      </div>
                    )}
                    <FaceTrackingOverlay
                      videoRef={videoRef}
                      cameraOff={cameraOff}
                      theme={theme}
                      isCodingPhase={true}
                      isActivelyTyping={isActivelyTyping}
                      onFaceStatusChange={handleFaceStatusChange}
                    />
                  </div>

                  {/* Real-time Computer Vision & Camera Warning Banner */}
                  {visionWarning && (
                    <div
                      className={`rounded-xl border p-2.5 text-xs flex items-start gap-2.5 transition-all duration-200 ${
                        visionWarning.type === 'camera_off'
                          ? isLight
                            ? 'border-red-200 bg-red-50 text-red-900 shadow-xs'
                            : 'border-red-500/30 bg-red-950/70 text-red-200'
                          : isLight
                            ? 'border-amber-200 bg-amber-50 text-amber-900 shadow-xs'
                            : 'border-amber-500/30 bg-amber-950/70 text-amber-200'
                      }`}
                    >
                      <AlertTriangle
                        className={`h-4 w-4 shrink-0 mt-0.5 ${
                          visionWarning.type === 'camera_off'
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-amber-600 dark:text-amber-400'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-[12px]">{visionWarning.title}</p>
                        <p className="text-[11px] leading-relaxed opacity-90 mt-0.5">{visionWarning.message}</p>
                      </div>
                      {visionWarning.type === 'camera_off' && (
                        <button
                          type="button"
                          onClick={toggleCamera}
                          className={`shrink-0 rounded-md px-2.5 py-1 text-[11px] font-semibold transition shadow-xs ${
                            isLight
                              ? 'bg-red-600 text-white hover:bg-red-700'
                              : 'bg-red-500 text-white hover:bg-red-600'
                          }`}
                        >
                          Turn On
                        </button>
                      )}
                    </div>
                  )}

                  <div className="flex items-center justify-between pt-1">
                    <div
                      className={`flex items-center gap-2 text-xs font-medium ${
                        isLight ? 'text-slate-700' : 'text-slate-300'
                      }`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${
                          visionWarning
                            ? visionWarning.type === 'camera_off'
                              ? 'bg-red-500 animate-pulse'
                              : 'bg-amber-400 animate-pulse'
                            : cameraOff || micMuted
                              ? 'bg-amber-400'
                              : 'bg-emerald-500 animate-pulse'
                        }`}
                      />
                      <span className="truncate max-w-[200px]">
                        {visionWarning
                          ? `${visionWarning.title} · ${micMuted ? 'Mic muted' : 'Mic active'}`
                          : cameraOff && micMuted
                            ? 'Camera & mic off'
                            : cameraOff
                              ? 'Camera off · Mic on'
                              : micMuted
                                ? 'Camera on · Mic muted'
                                : 'Camera & mic active'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={toggleMic}
                        title={micMuted ? 'Turn microphone on' : 'Mute microphone'}
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border transition ${
                          micMuted
                            ? isLight
                              ? 'border-amber-300 bg-amber-100 text-amber-800'
                              : 'border-amber-400/40 bg-amber-500/20 text-amber-200'
                            : isLight
                              ? 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200'
                              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        {micMuted ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
                      </button>
                      <button
                        type="button"
                        onClick={toggleCamera}
                        title={cameraOff ? 'Turn camera on' : 'Turn camera off'}
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border transition ${
                          cameraOff
                            ? isLight
                              ? 'border-amber-300 bg-amber-100 text-amber-800'
                              : 'border-amber-400/40 bg-amber-500/20 text-amber-200'
                            : isLight
                              ? 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200'
                              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        {cameraOff ? <VideoOff className="h-3.5 w-3.5" /> : <Video className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>

                {/* Problem Statement Viewer */}
                <ProblemStatementViewer
                  challenge={currentQuestion.coding_challenge}
                  difficultyBadge={difficultyBadge}
                  theme={theme}
                />
              </div>
            )}

            {/* RIGHT COLUMN:
                NON-CODING MODE: CAMERA (TOP) + DELIVERY GUIDE (BOTTOM)
                CODING MODE: MONACO WORKSPACE (TOP) + VOICE/TEXT NOTES DRAWER (BOTTOM) */}
            <div className="flex min-h-0 flex-col gap-5">
              {/* In Non-Coding Mode: Camera Card */}
              {!isCodingPhase && (
                <div
                  className={`rounded-2xl border p-4 shadow-xl backdrop-blur-xl space-y-3 transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5 text-slate-800'
                      : 'border-white/10 bg-slate-900/70 ring-1 ring-white/5 text-slate-100'
                  }`}
                >
                  <div className="relative aspect-video w-full overflow-hidden rounded-xl bg-slate-950 border border-slate-800/80">
                    <video
                      ref={attachVideoElement}
                      autoPlay
                      muted
                      playsInline
                      className={`h-full w-full object-cover ${cameraOff ? 'opacity-0' : 'opacity-100'}`}
                    />
                    {cameraOff && (
                      <div className="absolute inset-0 flex flex-col items-center justify-center bg-slate-950 text-slate-500 z-10">
                        <div className="h-14 w-14 rounded-full bg-slate-900 border border-red-500/30 flex items-center justify-center mb-2">
                          <VideoOff className="h-6 w-6 text-red-400" />
                        </div>
                        <p className="text-xs font-semibold text-red-300">Camera Turned Off</p>
                        <p className="text-[11px] text-slate-400 mt-0.5">Turn on camera for proctoring</p>
                      </div>
                    )}

                    <FaceTrackingOverlay
                      videoRef={videoRef}
                      cameraOff={cameraOff}
                      theme={theme}
                      isCodingPhase={false}
                      isActivelyTyping={isActivelyTyping}
                      onFaceStatusChange={handleFaceStatusChange}
                    />
                  </div>

                  {/* Real-time Computer Vision & Camera Warning Banner */}
                  {visionWarning && (
                    <div
                      className={`rounded-xl border p-2.5 text-xs flex items-start gap-2.5 transition-all duration-200 ${
                        visionWarning.type === 'camera_off'
                          ? isLight
                            ? 'border-red-200 bg-red-50 text-red-900 shadow-xs'
                            : 'border-red-500/30 bg-red-950/70 text-red-200'
                          : isLight
                            ? 'border-amber-200 bg-amber-50 text-amber-900 shadow-xs'
                            : 'border-amber-500/30 bg-amber-950/70 text-amber-200'
                      }`}
                    >
                      <AlertTriangle
                        className={`h-4 w-4 shrink-0 mt-0.5 ${
                          visionWarning.type === 'camera_off'
                            ? 'text-red-600 dark:text-red-400'
                            : 'text-amber-600 dark:text-amber-400'
                        }`}
                      />
                      <div className="flex-1 min-w-0">
                        <p className="font-semibold text-[12px]">{visionWarning.title}</p>
                        <p className="text-[11px] leading-relaxed opacity-90 mt-0.5">{visionWarning.message}</p>
                      </div>
                      {visionWarning.type === 'camera_off' && (
                        <button
                          type="button"
                          onClick={toggleCamera}
                          className={`shrink-0 rounded-md px-2.5 py-1 text-[11px] font-semibold transition shadow-xs ${
                            isLight
                              ? 'bg-red-600 text-white hover:bg-red-700'
                              : 'bg-red-500 text-white hover:bg-red-600'
                          }`}
                        >
                          Turn On
                        </button>
                      )}
                    </div>
                  )}

                  {/* Device Status & Quick Controls */}
                  <div className="flex items-center justify-between pt-1">
                    <div
                      className={`flex items-center gap-2 text-xs font-medium ${
                        isLight ? 'text-slate-700' : 'text-slate-300'
                      }`}
                    >
                      <span
                        className={`h-2 w-2 rounded-full ${
                          visionWarning
                            ? visionWarning.type === 'camera_off'
                              ? 'bg-red-500 animate-pulse'
                              : 'bg-amber-400 animate-pulse'
                            : cameraOff || micMuted
                              ? 'bg-amber-400'
                              : 'bg-emerald-500 animate-pulse'
                        }`}
                      />
                      <span className="truncate max-w-[220px]">
                        {visionWarning
                          ? `${visionWarning.title} · ${micMuted ? 'Mic muted' : 'Mic active'}`
                          : cameraOff && micMuted
                            ? 'Camera & mic off'
                            : cameraOff
                              ? 'Camera off · Mic on'
                              : micMuted
                                ? 'Camera on · Mic muted'
                                : 'Camera & mic active'}
                      </span>
                    </div>

                    <div className="flex items-center gap-1.5">
                      <button
                        type="button"
                        onClick={toggleMic}
                        title={micMuted ? 'Turn microphone on' : 'Mute microphone'}
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border transition ${
                          micMuted
                            ? isLight
                              ? 'border-amber-300 bg-amber-100 text-amber-800'
                              : 'border-amber-400/40 bg-amber-500/20 text-amber-200'
                            : isLight
                              ? 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200'
                              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        {micMuted ? <MicOff className="h-3.5 w-3.5" /> : <Mic className="h-3.5 w-3.5" />}
                      </button>
                      <button
                        type="button"
                        onClick={toggleCamera}
                        title={cameraOff ? 'Turn camera on' : 'Turn camera off'}
                        className={`flex h-8 w-8 items-center justify-center rounded-lg border transition ${
                          cameraOff
                            ? isLight
                              ? 'border-amber-300 bg-amber-100 text-amber-800'
                              : 'border-amber-400/40 bg-amber-500/20 text-amber-200'
                            : isLight
                              ? 'border-slate-200 bg-slate-100 text-slate-700 hover:bg-slate-200'
                              : 'border-white/10 bg-white/5 text-slate-300 hover:bg-white/10 hover:text-white'
                        }`}
                      >
                        {cameraOff ? <VideoOff className="h-3.5 w-3.5" /> : <Video className="h-3.5 w-3.5" />}
                      </button>
                    </div>
                  </div>
                </div>
              )}

              {/* In Non-Coding Mode: Delivery Feedback Guide Card */}
              {!isCodingPhase && (
                <div
                  className={`rounded-2xl border p-5 shadow-xl backdrop-blur-xl space-y-4 transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5 text-slate-800'
                      : 'border-white/10 bg-slate-900/70 text-slate-100 ring-1 ring-white/5'
                  }`}
                >
                  <div>
                    <h3 className={`text-sm font-bold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
                      Live Delivery Guide
                    </h3>
                    <p className={`text-xs mt-0.5 ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                      Acoustic and clarity metrics update as you speak.
                    </p>
                  </div>

                  <div className="space-y-3.5">
                    {/* Pace */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>Pace</span>
                        <span className={`font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                          {liveMetrics.pace}
                        </span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`}>
                        <div
                          className="h-full rounded-full bg-indigo-600 transition-all duration-300"
                          style={{
                            width:
                              liveMetrics.pace === 'Good'
                                ? '85%'
                                : liveMetrics.pace === 'Steady'
                                  ? '65%'
                                  : liveMetrics.pace === 'Build depth'
                                    ? '40%'
                                    : '0%',
                          }}
                        />
                      </div>
                    </div>

                    {/* Clarity */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>Clarity</span>
                        <span className={`font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                          {liveMetrics.clarity}
                        </span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`}>
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all duration-300"
                          style={{
                            width: liveMetrics.clarity !== '—' ? liveMetrics.clarity : '0%',
                          }}
                        />
                      </div>
                    </div>

                    {/* Voice level */}
                    <div className="space-y-1.5">
                      <div className="flex items-center justify-between text-xs">
                        <span className={isLight ? 'text-slate-500' : 'text-slate-400'}>Voice level</span>
                        <span className={`font-semibold ${isLight ? 'text-slate-800' : 'text-slate-200'}`}>
                          {micMuted ? 'Muted' : audioLevel > 5 ? 'Optimal' : '—'}
                        </span>
                      </div>
                      <div className={`h-1.5 w-full rounded-full overflow-hidden ${isLight ? 'bg-slate-100' : 'bg-slate-800'}`}>
                        <div
                          className="h-full rounded-full bg-emerald-500 transition-all duration-75"
                          style={{
                            width: `${Math.min(100, Math.max(0, audioLevel * 2))}%`,
                          }}
                        />
                      </div>
                    </div>
                  </div>

                  <div
                    className={`border-t pt-3 flex items-start gap-2 text-[11px] leading-relaxed ${
                      isLight ? 'border-slate-100 text-slate-500' : 'border-white/10 text-slate-500'
                    }`}
                  >
                    <Info className={`h-3.5 w-3.5 shrink-0 mt-0.5 ${isLight ? 'text-indigo-600' : 'text-slate-400'}`} />
                    <span>Answers are evaluated on depth, relevance and technical accuracy. Delivery is an advisory guide.</span>
                  </div>
                </div>
              )}

              {/* In Coding Mode: Monaco Workspace */}
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
                  theme={theme}
                  onEditorFocus={stopListening}
                  onTyping={() => {
                    lastTypingTimestampRef.current = Date.now();
                    setIsActivelyTyping(true);
                  }}
                />
              ) : null}

              {/* In Coding Mode: Candidate Response & Voice Notes Drawer */}
              {isCodingPhase && (
                <div
                  className={`flex flex-1 flex-col rounded-2xl border p-5 shadow-xl backdrop-blur-md transition-colors ${
                    isLight
                      ? 'border-slate-200/90 bg-white shadow-slate-200/50 ring-1 ring-slate-900/5'
                      : 'border-white/10 bg-slate-900/60 ring-1 ring-white/5'
                  }`}
                >
                  <div className="mb-4 flex flex-col gap-3">
                    <div
                      className={`flex flex-wrap items-center justify-between gap-2 border-b pb-2 ${
                        isLight ? 'border-slate-100' : 'border-white/5'
                      }`}
                    >
                      <div
                        className={`inline-flex items-center gap-1.5 px-3 py-1 text-xs font-semibold ${
                          isLight ? 'text-indigo-700' : 'text-indigo-300'
                        }`}
                      >
                        <Mic className="h-3.5 w-3.5" />
                        <span>Verbal Solution Walkthrough (Audio Only)</span>
                        {isListening && (
                          <span className="h-1.5 w-1.5 rounded-full bg-emerald-500 animate-ping" />
                        )}
                      </div>

                      <div className="flex items-center gap-2">
                        <button
                          type="button"
                          onClick={async () => {
                            const t = displayTranscript.trim();
                            if (!t) return;
                            try {
                              await navigator.clipboard.writeText(t);
                            } catch { }
                          }}
                          disabled={!displayTranscript.trim()}
                          className={`text-[11px] disabled:opacity-30 ${
                            isLight ? 'text-slate-500 hover:text-slate-900' : 'text-slate-400 hover:text-white'
                          }`}
                        >
                          Copy
                        </button>
                      </div>
                    </div>
                  </div>

                  {/* Input Body: Audio transcription only, strictly read-only */}
                  <div
                    className={`flex flex-1 flex-col min-h-[120px] rounded-xl border p-3 ${
                      isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]/80'
                    }`}
                  >
                    {displayTranscript ? (
                      <textarea
                        value={displayTranscript}
                        readOnly={true}
                        tabIndex={-1}
                        onKeyDown={(e) => e.preventDefault()}
                        className={`w-full flex-1 bg-transparent text-xs leading-relaxed focus:outline-none resize-none cursor-default select-text ${
                          isLight ? 'text-slate-900' : 'text-slate-100'
                        }`}
                        rows={3}
                        placeholder="Spoken notes on your solution approach..."
                      />
                    ) : (
                      <div className="flex h-full min-h-[100px] flex-col items-center justify-center text-center text-slate-500 text-xs">
                        <Mic className="h-4 w-4 mb-1 text-indigo-400/60" />
                        <p className="font-medium text-slate-400">Verbal explanation transcribes automatically</p>
                        <p className="text-[11px] text-slate-500 mt-0.5">
                          Dictate your solution approach or code explanations verbally. Audio transcribed in real time (read-only).
                        </p>
                      </div>
                    )}
                  </div>

                  {/* Footer Buttons */}
                  <div className="mt-4 flex gap-3">
                    <button
                      type="button"
                      onClick={() => setShowSkipModal(true)}
                      disabled={loading || conversationState === 'processing'}
                      className={`flex-1 rounded-xl border py-2.5 text-xs font-semibold transition disabled:opacity-40 ${
                        isLight
                          ? 'border-slate-200 bg-white text-slate-700 hover:bg-slate-100 hover:text-slate-900'
                          : 'border-white/15 py-2.5 text-slate-200 hover:bg-white/5'
                      }`}
                    >
                      Skip question
                    </button>
                    <button
                      type="button"
                      onClick={handleSubmitAnswer}
                      disabled={loading || conversationState === 'processing'}
                      className="flex-1 inline-flex items-center justify-center gap-2 rounded-xl bg-indigo-600 py-2.5 text-xs font-semibold text-white shadow-lg transition hover:bg-indigo-500 disabled:opacity-40"
                    >
                      {loading || conversationState === 'processing' ? 'Evaluating…' : 'Submit solution'}
                    </button>
                  </div>
                </div>
              )}
            </div>
          </div>
        )}

        {report && (
          <div
            className={`rounded-2xl border p-8 space-y-6 shadow-xl backdrop-blur-md transition-colors ${
              isLight
                ? 'border-slate-200/90 bg-white shadow-slate-200/50 text-slate-800'
                : 'border-white/10 bg-slate-900/60 text-slate-100'
            }`}
          >
            <div
              className={`flex flex-col sm:flex-row sm:items-center justify-between gap-4 border-b pb-6 ${
                isLight ? 'border-slate-100' : 'border-white/10'
              }`}
            >
              <div>
                <div
                  className={`inline-flex items-center gap-2 rounded-full border px-3 py-1 text-xs font-semibold mb-3 ${
                    isLight
                      ? 'border-emerald-300 bg-emerald-50 text-emerald-800'
                      : 'border-emerald-500/30 bg-emerald-500/10 text-emerald-300'
                  }`}
                >
                  <CheckCircle2 className="h-4 w-4 text-emerald-500" />
                  Assessment Completed & Submitted
                </div>
                <h2 className={`text-2xl font-bold tracking-tight ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  Interview Completed Successfully
                </h2>
                <p className={`mt-1 text-sm ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                  Your verbal responses, code solutions, and interview metrics have been securely submitted for evaluation.
                </p>
              </div>
              <button
                onClick={() => router.push('/dashboard')}
                className="inline-flex items-center justify-center rounded-xl bg-indigo-600 px-6 py-3 text-sm font-semibold text-white shadow-lg transition hover:bg-indigo-500 hover:shadow-indigo-500/25"
              >
                Back to Dashboard
              </button>
            </div>

            <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
              <div
                className={`rounded-xl border p-4 ${
                  isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]/70'
                }`}
              >
                <p className={`text-[11px] font-medium uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Questions Completed
                </p>
                <p className={`mt-1 text-2xl font-bold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                  {questions.length || '—'}
                </p>
              </div>
              <div
                className={`rounded-xl border p-4 ${
                  isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]/70'
                }`}
              >
                <p className={`text-[11px] font-medium uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Total Duration
                </p>
                <p className="mt-1 text-2xl font-bold text-indigo-600 dark:text-indigo-300">
                  {formatMmSs(elapsedSec)}
                </p>
              </div>
              <div
                className={`rounded-xl border p-4 ${
                  isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]/70'
                }`}
              >
                <p className={`text-[11px] font-medium uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Audio / Speech
                </p>
                <p className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                  Processed
                </p>
              </div>
              <div
                className={`rounded-xl border p-4 ${
                  isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]/70'
                }`}
              >
                <p className={`text-[11px] font-medium uppercase tracking-wider ${isLight ? 'text-slate-500' : 'text-slate-400'}`}>
                  Video Integrity
                </p>
                <p className="mt-1 text-sm font-semibold text-emerald-600 dark:text-emerald-400 flex items-center gap-1.5">
                  <span className="inline-block h-2 w-2 rounded-full bg-emerald-500" />
                  Verified
                </p>
              </div>
            </div>

            <div
              className={`rounded-xl border p-5 ${
                isLight
                  ? 'border-indigo-100 bg-indigo-50/70 text-slate-800'
                  : 'border-indigo-500/20 bg-indigo-500/10 text-slate-100'
              }`}
            >
              <div className="flex items-start gap-3">
                <Sparkles className="h-5 w-5 text-indigo-600 dark:text-indigo-400 shrink-0 mt-0.5" />
                <div className="space-y-1">
                  <p className={`text-sm font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
                    What happens next?
                  </p>
                  <p className={`text-xs leading-relaxed ${isLight ? 'text-slate-600' : 'text-slate-300'}`}>
                    The recruiting team will review your comprehensive evaluation, code submission, and technical breakdown. You will be notified via email regarding status updates and subsequent interview rounds.
                  </p>
                </div>
              </div>
            </div>
          </div>
        )}
      </main>
    </div>
  );
}
