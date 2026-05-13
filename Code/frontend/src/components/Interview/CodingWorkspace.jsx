/**
 * Professional Monaco workspace for live interview coding rounds.
 * Client-only (loaded via next/dynamic from the interview page).
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import Editor from '@monaco-editor/react';
import interviewService from '@/services/interviewService';
import { formatApiDetail } from '@/utils/formatApiDetail';

const RUN_TIMEOUT_SEC = 12;

/** API language keys sent to /interview/coding/run */
const LANGUAGE_OPTIONS = [
  { id: 'python', label: 'Python 3', monaco: 'python' },
  { id: 'javascript', label: 'JavaScript (Node)', monaco: 'javascript' },
  { id: 'c', label: 'C (gcc)', monaco: 'c' },
  { id: 'cpp', label: 'C++ (g++)', monaco: 'cpp' },
  { id: 'java', label: 'Java', monaco: 'java' },
];

function inferApiLanguageFromRecommended(recommended) {
  const raw = Array.isArray(recommended)
    ? recommended[0]
    : typeof recommended === 'string'
      ? recommended
      : 'python';
  const l = String(raw || 'python').toLowerCase();
  if (l.includes('typescript') || l === 'ts') return 'javascript';
  if (l.includes('javascript') || l.includes('node') || l === 'js') return 'javascript';
  if (l.includes('java')) return 'java';
  if (l.includes('cpp') || l.includes('c++')) return 'cpp';
  if (l === 'c' || (l.includes(' c') && !l.includes('++'))) return 'c';
  if (l.includes('python')) return 'python';
  return 'python';
}

function monacoLanguageForApi(apiId) {
  const row = LANGUAGE_OPTIONS.find((o) => o.id === apiId);
  return row?.monaco || 'python';
}

export default function CodingWorkspace({
  starterCode = '',
  recommendedLanguages = ['python'],
  title = 'Solution',
  onEditorFocus,
  publicTestCases = [],
}) {
  const initialLang = useMemo(
    () => inferApiLanguageFromRecommended(recommendedLanguages),
    [recommendedLanguages]
  );

  const [selectedLang, setSelectedLang] = useState(initialLang);
  const [code, setCode] = useState(starterCode);

  const [runLoading, setRunLoading] = useState(false);
  const [runError, setRunError] = useState(null);
  const [runResult, setRunResult] = useState(null);

  useEffect(() => {
    setSelectedLang(inferApiLanguageFromRecommended(recommendedLanguages));
  }, [recommendedLanguages]);

  useEffect(() => {
    setCode(starterCode);
  }, [starterCode]);

  const monacoLang = useMemo(() => monacoLanguageForApi(selectedLang), [selectedLang]);

  const canRun = Array.isArray(publicTestCases) && publicTestCases.length > 0;

  const handleRun = useCallback(async () => {
    if (!canRun) return;
    setRunLoading(true);
    setRunError(null);
    setRunResult(null);
    try {
      const payload = {
        language: selectedLang,
        source_code: code,
        timeout_seconds: RUN_TIMEOUT_SEC,
        test_cases: publicTestCases.map((tc) => ({
          stdin: tc.stdin ?? '',
          expected_stdout: tc.expected_stdout ?? '',
          description: tc.description,
        })),
      };
      const data = await interviewService.runCode(payload);
      setRunResult(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const fallback = err?.response?.data?.message || err?.message || 'Run failed';
      const msg = formatApiDetail(detail) || fallback;
      setRunError(msg);
    } finally {
      setRunLoading(false);
    }
  }, [canRun, code, publicTestCases, selectedLang]);

  const handleReset = useCallback(() => {
    setCode(starterCode);
  }, [starterCode]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(code);
    } catch {
      /* ignore */
    }
  }, [code]);

  const editorOptions = useMemo(
    () => ({
      readOnly: false,
      domReadOnly: false,
      minimap: { enabled: true, scale: 0.85 },
      fontSize: 14,
      lineNumbers: 'on',
      scrollBeyondLastLine: false,
      automaticLayout: true,
      tabSize: 4,
      insertSpaces: true,
      wordWrap: 'on',
      padding: { top: 12, bottom: 12 },
      smoothScrolling: true,
      cursorBlinking: 'smooth',
      renderLineHighlight: 'all',
      bracketPairColorization: { enabled: true },
      guides: { bracketPairs: true, indentation: true },
      fontFamily:
        "'JetBrains Mono', 'Fira Code', 'SF Mono', Consolas, 'Liberation Mono', Menlo, monospace",
      fontLigatures: true,
      scrollbar: {
        verticalScrollbarSize: 10,
        horizontalScrollbarSize: 10,
      },
    }),
    []
  );

  const handleMount = useCallback(
    (editor) => {
      try {
        editor.updateOptions({ readOnly: false });
        editor.onDidFocusEditorText(() => {
          onEditorFocus?.();
        });
        editor.onDidFocusEditorWidget(() => {
          onEditorFocus?.();
        });
      } catch {
        /* ignore */
      }
    },
    [onEditorFocus]
  );

  const summaryBadge = useMemo(() => {
    if (!runResult) return null;
    if (runResult.missing_tools?.length) {
      return (
        <span className="rounded-md bg-amber-500/20 px-2 py-0.5 text-[11px] font-medium text-amber-200">
          Toolchain missing
        </span>
      );
    }
    if (!runResult.compile_success) {
      return (
        <span className="rounded-md bg-red-500/20 px-2 py-0.5 text-[11px] font-medium text-red-200">
          Compile error
        </span>
      );
    }
    if (runResult.all_passed) {
      return (
        <span className="rounded-md bg-emerald-500/20 px-2 py-0.5 text-[11px] font-medium text-emerald-200">
          All tests passed
        </span>
      );
    }
    return (
      <span className="rounded-md bg-orange-500/20 px-2 py-0.5 text-[11px] font-medium text-orange-100">
        Some tests failed
      </span>
    );
  }, [runResult]);

  return (
    <div className="relative z-20 flex min-h-0 flex-col overflow-hidden rounded-xl border border-white/15 bg-[#1a1b26] shadow-2xl ring-1 ring-white/5">
      {/* IDE-style chrome */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-[#16161e] px-3 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-emerald-500/20 text-xs font-bold text-emerald-300">
            {'</>'}
          </span>
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-slate-200">{title}</p>
            <p className="text-[10px] text-slate-500">Monaco · run against public tests</p>
          </div>
        </div>
        <div className="flex flex-wrap items-center gap-2">
          <label className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span className="hidden sm:inline">Language</span>
            <select
              value={selectedLang}
              onChange={(e) => setSelectedLang(e.target.value)}
              className="max-w-[160px] rounded-md border border-white/15 bg-black/40 px-2 py-1 text-[11px] font-medium text-slate-200 outline-none focus:border-emerald-500/40"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>
          <span className="rounded-md border border-white/10 bg-black/30 px-2 py-0.5 font-mono text-[11px] font-medium uppercase tracking-wide text-slate-300">
            {monacoLang}
          </span>
          <button
            type="button"
            onClick={handleCopy}
            className="rounded-lg border border-white/15 bg-white/5 px-3 py-1.5 text-xs font-medium text-slate-200 transition hover:bg-white/10"
          >
            Copy
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-3 py-1.5 text-xs font-medium text-amber-100 transition hover:bg-amber-500/20"
          >
            Reset to starter
          </button>
          <button
            type="button"
            onClick={handleRun}
            disabled={!canRun || runLoading}
            title={
              canRun
                ? 'Compile (if needed) and run all public tests'
                : 'No public tests available for this question'
            }
            className="rounded-lg border border-emerald-500/40 bg-emerald-600/90 px-3 py-1.5 text-xs font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {runLoading ? 'Running…' : 'Run tests'}
          </button>
        </div>
      </div>

      <div className="relative isolate h-[min(520px,52vh)] min-h-[380px] w-full flex-1 [&_.monaco-editor]:pointer-events-auto [&_.monaco-mouse-cursor-text]:pointer-events-auto">
        <Editor
          height="100%"
          language={monacoLang}
          theme="vs-dark"
          value={code}
          onChange={(v) => setCode(v ?? '')}
          onMount={handleMount}
          options={editorOptions}
          loading={
            <div className="flex h-full min-h-[380px] items-center justify-center bg-[#1e1e1e] text-sm text-slate-400">
              Loading editor…
            </div>
          }
        />
      </div>

      <div className="shrink-0 border-t border-white/10 bg-[#16161e] px-3 py-3">
        <div className="mb-2 flex flex-wrap items-center justify-between gap-2">
          <p className="text-[11px] font-semibold uppercase tracking-wide text-slate-400">
            Test results
          </p>
          {summaryBadge}
        </div>

        {runError && (
          <div className="mb-2 rounded-lg border border-red-500/30 bg-red-950/40 px-3 py-2 text-xs text-red-100">
            {runError}
          </div>
        )}

        {runResult?.missing_tools?.length ? (
          <p className="mb-2 text-xs text-amber-100/90">
            Install these on the interview API server PATH: {runResult.missing_tools.join(', ')}
          </p>
        ) : null}

        {runResult && !runResult.compile_success && runResult.compile_output ? (
          <pre className="mb-2 max-h-40 overflow-auto rounded-lg border border-white/10 bg-black/50 p-3 font-mono text-[11px] leading-relaxed text-red-100/95">
            {runResult.compile_output}
          </pre>
        ) : null}

        {runResult?.compile_success && runResult.results?.length ? (
          <div className="max-h-64 space-y-2 overflow-y-auto">
            {runResult.results.map((row, i) => (
              <div
                key={`${row.index}-${i}`}
                className={`rounded-lg border px-3 py-2 text-xs ${
                  row.passed
                    ? 'border-emerald-500/25 bg-emerald-950/30 text-emerald-50'
                    : 'border-orange-500/25 bg-orange-950/25 text-orange-50'
                }`}
              >
                <div className="flex flex-wrap items-center justify-between gap-2 font-medium">
                  <span>
                    {row.description || `Case ${row.index + 1}`}{' '}
                    <span className="font-mono text-[10px] opacity-80">
                      {row.passed ? 'PASS' : 'FAIL'}
                    </span>
                  </span>
                  <span className="font-mono text-[10px] text-slate-400">
                    exit {row.exit_code}
                  </span>
                </div>
                {row.error ? (
                  <p className="mt-1 font-mono text-[10px] text-red-200/90">{row.error}</p>
                ) : null}
                {!row.passed && (
                  <div className="mt-2 grid gap-2 font-mono text-[10px] text-slate-300/95 sm:grid-cols-2">
                    <div>
                      <p className="mb-0.5 text-slate-500">Expected stdout</p>
                      <pre className="whitespace-pre-wrap rounded bg-black/40 p-2">{row.expected_stdout}</pre>
                    </div>
                    <div>
                      <p className="mb-0.5 text-slate-500">Your stdout</p>
                      <pre className="whitespace-pre-wrap rounded bg-black/40 p-2">{row.actual_stdout}</pre>
                    </div>
                  </div>
                )}
                {row.stderr?.trim() ? (
                  <pre className="mt-2 max-h-24 overflow-auto rounded border border-white/10 bg-black/40 p-2 font-mono text-[10px] text-slate-400">
                    {row.stderr}
                  </pre>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          !runError &&
          !runResult && (
            <p className="text-[11px] leading-relaxed text-slate-500">
              Switch language if needed, implement stdin → stdout, then <strong className="text-slate-400">Run tests</strong>{' '}
              to compare against the public cases on the left.
            </p>
          )
        )}
      </div>
    </div>
  );
}
