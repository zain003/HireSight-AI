import React, { useEffect, useState, useRef } from 'react';
import {
  ShieldCheck,
  Eye,
  Activity,
  Sparkles,
  CheckCircle2,
  Code,
  Laptop,
  EyeOff,
  AlertTriangle,
} from 'lucide-react';
import { interviewService } from '@/services/interviewService';

/**
 * Real-Time Face Detection, Gaze Direction & Eye Occlusion Proctoring HUD Overlay
 * 
 * Powered by MediaPipe FaceMesh (468 landmarks), FaceDetection, and OpenCV solvePnP:
 * - Real 3D head pose estimation: detects 90° head profile turns left/right.
 * - Eye Aspect Ratio (EAR) & patch variance: detects eyes closed or covered by hands/objects.
 * - Workspace engagement cone: distinguishes looking at screen vs. typing/looking down at keyboard.
 * - Ultra-clean, non-intrusive holographic corner reticle with responsive status telemetry.
 */
export default function FaceTrackingOverlay({
  videoRef,
  cameraOff = false,
  theme = 'dark',
  isCodingPhase = false,
  isActivelyTyping = false,
  onFaceStatusChange = null,
  onProctoringEvent = null,
}) {
  const [faceDetected, setFaceDetected] = useState(false);
  const [isCentered, setIsCentered] = useState(false);
  const [gazeDirection, setGazeDirection] = useState('center'); // 'center' | 'keyboard' | 'eyes_hidden' | 'turned_side' | 'away'
  const [isEyeOccluded, setIsEyeOccluded] = useState(false);
  const [severityLevel, setSeverityLevel] = useState('normal'); // 'normal' | 'low' | 'warning' | 'red_flag'

  const consecutiveFaceHitsRef = useRef(0);
  const consecutiveMissesRef = useRef(0);
  const consecutiveOcclusionHitsRef = useRef(0);
  const consecutiveTurnedHitsRef = useRef(0);
  const isAnalyzingRef = useRef(false);

  // Temporal Event Tracking Ref
  const currentEventRef = useRef({
    type: 'center',
    startTime: Date.now(),
    flagged: false,
  });

  const isLight = theme === 'light';

  // Real-time Computer Vision Frame Analyzer (Runs every 300ms via MediaPipe backend)
  useEffect(() => {
    if (cameraOff) {
      setFaceDetected(false);
      setIsCentered(false);
      setGazeDirection('away');
      setIsEyeOccluded(false);
      setSeverityLevel('red_flag');
      if (onFaceStatusChange) {
        onFaceStatusChange({
          detected: false,
          isCentered: false,
          presence: 0,
          gaze: 'away',
          isOccluded: false,
          isTyping: isActivelyTyping,
          severity: 'red_flag',
          redFlags: ['camera_off'],
        });
      }
      return;
    }

    const canvas = document.createElement('canvas');
    canvas.width = 320;
    canvas.height = 240;
    const ctx = canvas.getContext('2d', { willReadFrequently: true });

    const detectFaceAndGaze = async () => {
      const video = videoRef?.current;
      if (!video || !video.videoWidth || !video.videoHeight || video.paused || video.ended || !ctx) {
        return;
      }

      if (isAnalyzingRef.current) return;
      isAnalyzingRef.current = true;

      try {
        ctx.drawImage(video, 0, 0, 320, 240);
        const b64 = canvas.toDataURL('image/jpeg', 0.6);

        const res = await interviewService.checkLiveGaze(b64, isCodingPhase, isActivelyTyping);

        let detected = false;
        let calculatedGaze = 'away';
        let centered = false;
        let occluded = false;
        let turnedAway = false;

        if (res && res.detected) {
          detected = true;
          centered = !!res.is_centered;
          occluded = !!res.is_occluded;
          calculatedGaze = res.gaze || 'center';

          // 1. Actively typing or downward keyboard focus -> Immediately keyboard mode
          if (isActivelyTyping || calculatedGaze === 'keyboard') {
            calculatedGaze = 'keyboard';
            centered = true;
            turnedAway = false;
          } else if (occluded || calculatedGaze === 'eyes_hidden') {
            occluded = true;
            calculatedGaze = 'eyes_hidden';
            centered = false;
            turnedAway = false;
          } else if (calculatedGaze === 'turned_side' || Math.abs(res.head_pose?.yaw || 0) >= 42) {
            turnedAway = true;
            calculatedGaze = 'turned_side';
            centered = false;
          } else {
            // Normal engagement: center view across workspace
            calculatedGaze = 'center';
            centered = true;
            turnedAway = false;
          }
        }

        // Smooth temporal filtering
        if (detected) {
          consecutiveFaceHitsRef.current = Math.min(6, consecutiveFaceHitsRef.current + 1);
          consecutiveMissesRef.current = 0;
        } else {
          consecutiveMissesRef.current = Math.min(6, consecutiveMissesRef.current + 1);
          if (consecutiveMissesRef.current >= 2) {
            consecutiveFaceHitsRef.current = 0;
          }
        }

        if (occluded) {
          consecutiveOcclusionHitsRef.current = Math.min(6, consecutiveOcclusionHitsRef.current + 1);
        } else {
          consecutiveOcclusionHitsRef.current = 0;
        }

        if (turnedAway) {
          consecutiveTurnedHitsRef.current = Math.min(6, consecutiveTurnedHitsRef.current + 1);
        } else {
          // Instantly clear turned counter when user faces screen or keyboard
          consecutiveTurnedHitsRef.current = 0;
        }

        const stableDetected = consecutiveFaceHitsRef.current >= 1;
        const stableOccluded = consecutiveOcclusionHitsRef.current >= 1;
        const stableTurned = consecutiveTurnedHitsRef.current >= 2;

        let finalGaze = 'away';
        if (stableDetected) {
          if (stableOccluded) {
            finalGaze = 'eyes_hidden';
          } else if (stableTurned) {
            finalGaze = 'turned_side';
          } else {
            finalGaze = calculatedGaze;
          }
        }

        const isEngagedGaze = finalGaze === 'center' || finalGaze === 'keyboard';
        const finalCentered = stableDetected && centered && isEngagedGaze && !stableOccluded && !stableTurned;

        // Temporal Duration & Escalation Tracking
        const now = Date.now();
        const currentEvent = currentEventRef.current;

        let computedSeverity = 'normal';
        const activeFlags = [];

        if (finalGaze === 'eyes_hidden') {
          computedSeverity = 'red_flag';
          activeFlags.push('eye_occlusion_detected');
        } else if (finalGaze === 'turned_side') {
          computedSeverity = 'warning';
          activeFlags.push('head_turned_away');
        } else if (!stableDetected) {
          computedSeverity = 'warning';
          activeFlags.push('face_not_detected');
        } else {
          computedSeverity = 'normal';
        }

        setFaceDetected(stableDetected);
        setIsCentered(finalCentered);
        setGazeDirection(finalGaze);
        setIsEyeOccluded(stableOccluded);
        setSeverityLevel(computedSeverity);

        if (onFaceStatusChange) {
          onFaceStatusChange({
            detected: stableDetected,
            isCentered: finalCentered,
            presence: stableDetected ? 100 : 0,
            gaze: finalGaze,
            isOccluded: stableOccluded,
            isTyping: isActivelyTyping,
            severity: computedSeverity,
            headPose: res?.head_pose || null,
            score: res?.score ?? 100,
            redFlags: activeFlags,
          });
        }
      } catch {
        // Fallback gracefully on network anomaly
      } finally {
        isAnalyzingRef.current = false;
      }
    };

    const intervalId = setInterval(detectFaceAndGaze, 300);
    return () => {
      clearInterval(intervalId);
    };
  }, [cameraOff, videoRef, isCodingPhase, isActivelyTyping, onFaceStatusChange, onProctoringEvent]);

  if (cameraOff) return null;

  const isCenterGaze = gazeDirection === 'center';
  const isKeyboardGaze = gazeDirection === 'keyboard';
  const isTurnedSide = gazeDirection === 'turned_side';
  const isEyesHidden = gazeDirection === 'eyes_hidden' || isEyeOccluded;
  const isNormalEngaged = (isCenterGaze || isKeyboardGaze || (faceDetected && !isTurnedSide)) && !isEyesHidden;

  return (
    <div className="absolute inset-0 pointer-events-none z-10 flex flex-col justify-between p-2.5 select-none">
      {/* Top Bar: Single Clean Status Pill */}
      <div className="flex items-center justify-between gap-2">
        <div
          className={`flex items-center gap-1.5 px-2.5 py-1 rounded-full text-[11px] font-semibold tracking-wide backdrop-blur-md transition-all duration-300 shadow-xs ${
            isEyesHidden || severityLevel === 'red_flag'
              ? isLight
                ? 'bg-rose-500/15 text-rose-800 border border-rose-500/30'
                : 'bg-rose-950/80 text-rose-300 border border-rose-500/40 shadow-rose-500/10'
              : isTurnedSide || severityLevel === 'warning'
                ? isLight
                  ? 'bg-amber-500/15 text-amber-800 border border-amber-500/30'
                  : 'bg-amber-950/80 text-amber-300 border border-amber-500/40 shadow-amber-500/10'
                : isNormalEngaged
                  ? isLight
                    ? 'bg-emerald-500/15 text-emerald-800 border border-emerald-500/30'
                    : 'bg-emerald-950/70 text-emerald-300 border border-emerald-500/40 shadow-emerald-500/10'
                  : isLight
                    ? 'bg-slate-500/15 text-slate-800 border border-slate-400'
                    : 'bg-slate-900/80 text-slate-300 border border-slate-700'
          }`}
        >
          <span className="relative flex h-2 w-2">
            <span
              className={`animate-ping absolute inline-flex h-full w-full rounded-full opacity-75 ${
                isEyesHidden || severityLevel === 'red_flag'
                  ? 'bg-rose-400'
                  : isTurnedSide || severityLevel === 'warning'
                    ? 'bg-amber-400'
                    : isNormalEngaged
                      ? 'bg-emerald-400'
                      : 'bg-slate-400'
              }`}
            />
            <span
              className={`relative inline-flex rounded-full h-2 w-2 ${
                isEyesHidden || severityLevel === 'red_flag'
                  ? 'bg-rose-500'
                  : isTurnedSide || severityLevel === 'warning'
                    ? 'bg-amber-500'
                    : isNormalEngaged
                      ? 'bg-emerald-500'
                      : 'bg-slate-500'
              }`}
            />
          </span>
          <span>
            {isEyesHidden
              ? 'Eyes Covered / Closed'
              : isTurnedSide
                ? 'Head Turned Away • Turn to Screen'
                : faceDetected && isKeyboardGaze
                  ? 'Typing / Keyboard Focus • Calibrated'
                  : faceDetected
                    ? 'Screen Focused • Calibrated'
                    : 'Camera Active • Searching'}
          </span>
        </div>

        {/* AI Vision & Keyboard Status Telemetry Badge */}
        <div
          className={`hidden sm:flex items-center gap-1.5 px-2.5 py-1 rounded-md text-[10px] font-medium backdrop-blur-sm transition-colors ${
            isActivelyTyping
              ? isLight
                ? 'bg-emerald-50 text-emerald-700 border border-emerald-200'
                : 'bg-emerald-950/80 text-emerald-300 border border-emerald-500/40'
              : isLight
                ? 'bg-slate-900/10 text-slate-700 border border-slate-200'
                : 'bg-black/60 text-slate-300 border border-white/10'
          }`}
        >
          {isCodingPhase ? (
            <>
              <Code className={`h-3 w-3 ${isActivelyTyping ? 'text-emerald-400 animate-pulse' : 'text-slate-400'}`} />
              <span>{isActivelyTyping ? 'Typing Active' : 'IDE Workspace'}</span>
            </>
          ) : (
            <>
              <Sparkles className="h-3 w-3 text-sky-400" />
              <span>AI Vision 468p</span>
            </>
          )}
        </div>
      </div>

      {/* Center: Holographic Framing Reticle */}
      <div className="relative self-center w-40 h-48 sm:w-48 sm:h-56 my-auto pointer-events-none transition-all duration-300 opacity-60 hover:opacity-90">
        {/* Top-Left Corner */}
        <div
          className={`absolute top-0 left-0 w-4 h-4 border-t-2 border-l-2 rounded-tl-md transition-colors duration-300 ${
            isEyesHidden || severityLevel === 'red_flag'
              ? 'border-rose-400'
              : isTurnedSide || severityLevel === 'warning'
                ? 'border-amber-400'
                : isNormalEngaged
                  ? 'border-emerald-400/80'
                  : 'border-slate-500/60'
          }`}
        />
        {/* Top-Right Corner */}
        <div
          className={`absolute top-0 right-0 w-4 h-4 border-t-2 border-r-2 rounded-tr-md transition-colors duration-300 ${
            isEyesHidden || severityLevel === 'red_flag'
              ? 'border-rose-400'
              : isTurnedSide || severityLevel === 'warning'
                ? 'border-amber-400'
                : isNormalEngaged
                  ? 'border-emerald-400/80'
                  : 'border-slate-500/60'
          }`}
        />
        {/* Bottom-Left Corner */}
        <div
          className={`absolute bottom-0 left-0 w-4 h-4 border-b-2 border-l-2 rounded-bl-md transition-colors duration-300 ${
            isEyesHidden || severityLevel === 'red_flag'
              ? 'border-rose-400'
              : isTurnedSide || severityLevel === 'warning'
                ? 'border-amber-400'
                : isNormalEngaged
                  ? 'border-emerald-400/80'
                  : 'border-slate-500/60'
          }`}
        />
        {/* Bottom-Right Corner */}
        <div
          className={`absolute bottom-0 right-0 w-4 h-4 border-b-2 border-r-2 rounded-br-md transition-colors duration-300 ${
            isEyesHidden || severityLevel === 'red_flag'
              ? 'border-rose-400'
              : isTurnedSide || severityLevel === 'warning'
                ? 'border-amber-400'
                : isNormalEngaged
                  ? 'border-emerald-400/80'
                  : 'border-slate-500/60'
          }`}
        />
      </div>

      {/* Bottom Bar: Clean Presence & Identity Badges */}
      <div className="flex items-center justify-between gap-1 text-[10px]">
        <div className="flex items-center gap-1.5">
          <div className="rounded-md bg-black/70 px-2 py-0.5 font-semibold text-white backdrop-blur-sm border border-white/10">
            You
          </div>
          <div
            className={`hidden sm:flex items-center gap-1 rounded-md px-2 py-0.5 backdrop-blur-sm border ${
              faceDetected
                ? isLight
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'
                : isLight
                  ? 'bg-slate-100 text-slate-700 border-slate-200'
                  : 'bg-slate-900/60 text-slate-300 border-slate-700'
            }`}
          >
            <Activity className="h-3 w-3 text-emerald-400" />
            <span>Presence: {faceDetected ? '100%' : 'Calibrated'}</span>
          </div>
        </div>

        {/* Live Proctoring Status Chip */}
        <div
          className={`flex items-center gap-1 rounded-md px-2 py-0.5 backdrop-blur-sm border transition-colors duration-200 ${
            isEyesHidden
              ? isLight
                ? 'bg-rose-50 text-rose-800 border-rose-300'
                : 'bg-rose-950/80 text-rose-300 border-rose-500/40'
              : isTurnedSide
                ? isLight
                  ? 'bg-amber-50 text-amber-800 border-amber-300'
                  : 'bg-amber-950/80 text-amber-300 border-amber-500/40'
                : isLight
                  ? 'bg-emerald-50 text-emerald-700 border-emerald-200'
                  : 'bg-emerald-950/60 text-emerald-300 border-emerald-500/30'
          }`}
        >
          {isEyesHidden ? (
            <EyeOff className="h-3 w-3 text-rose-400" />
          ) : isTurnedSide ? (
            <EyeOff className="h-3 w-3 text-amber-400" />
          ) : (
            <Eye className="h-3 w-3 text-emerald-400" />
          )}
          <span>
            {isEyesHidden
              ? 'Eyes Occluded / Closed'
              : isTurnedSide
                ? 'Head Turned Away'
                : isKeyboardGaze
                  ? 'Keyboard / Code'
                  : faceDetected
                    ? 'Screen Focused'
                    : 'Searching Face'}
          </span>
        </div>
      </div>
    </div>
  );
}
