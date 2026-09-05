import React from 'react';
import { Mic, Keyboard, AlertCircle } from 'lucide-react';

/**
 * Dual Input Mode Toggle component for Live Multimodal Interview Workspace.
 * Allows switching between WebRTC Voice Recording and Text Response with draft preservation.
 */
export default function InputModeSelector({
  mode = 'voice',
  onChange,
  disabled = false,
  isListening = false,
  micMuted = false,
}) {
  return (
    <div className="flex flex-col gap-1.5 sm:flex-row sm:items-center sm:justify-between">
      <div 
        role="radiogroup" 
        aria-label="Answer input mode selection" 
        className="inline-flex rounded-xl border border-white/10 bg-slate-950/70 p-1 backdrop-blur-md shadow-inner"
      >
        <button
          type="button"
          role="radio"
          aria-checked={mode === 'voice'}
          onClick={() => onChange?.('voice')}
          disabled={disabled}
          className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all ${
            mode === 'voice'
              ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
          aria-pressed={mode === 'voice'}
        >
          <div className="relative">
            <Mic className="h-3.5 w-3.5" />
            {mode === 'voice' && isListening && !micMuted && (
              <span className="absolute -right-0.5 -top-0.5 h-1.5 w-1.5 animate-ping rounded-full bg-emerald-400" />
            )}
          </div>
          <span>Voice Recording</span>
          {mode === 'voice' && (
            <span
              className={`ml-1 inline-block h-1.5 w-1.5 rounded-full ${
                micMuted ? 'bg-amber-400' : isListening ? 'bg-emerald-400' : 'bg-slate-400'
              }`}
            />
          )}
        </button>

        <button
          type="button"
          role="radio"
          aria-checked={mode === 'text'}
          onClick={() => onChange?.('text')}
          disabled={disabled}
          className={`flex items-center gap-2 rounded-lg px-3.5 py-1.5 text-xs font-semibold transition-all ${
            mode === 'text'
              ? 'bg-gradient-to-r from-indigo-500 to-indigo-600 text-white shadow-md'
              : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          } ${disabled ? 'cursor-not-allowed opacity-50' : ''}`}
          aria-pressed={mode === 'text'}
        >
          <Keyboard className="h-3.5 w-3.5" />
          <span>Text Input</span>
          {mode === 'text' && (
            <span className="ml-1 rounded bg-white/20 px-1 py-0.2 text-[9px] font-mono uppercase tracking-wider text-indigo-100">
              Active
            </span>
          )}
        </button>
      </div>

      {mode === 'text' && (
        <span className="inline-flex items-center gap-1.5 text-[11px] font-medium text-amber-300/90">
          <AlertCircle className="h-3.5 w-3.5 text-amber-400 shrink-0" />
          <span>Mic recording disabled · Text mode active</span>
        </span>
      )}
    </div>
  );
}
