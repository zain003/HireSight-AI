/**
 * Professional Monaco workspace for live interview coding rounds.
 * Supports Python 3, JavaScript (Node), Java, C++, C with interactive
 * public test case runner, execution metrics, and hidden test submission.
 */
import { useCallback, useEffect, useMemo, useState } from 'react';
import Editor from '@monaco-editor/react';
import interviewService from '@/services/interviewService';
import { formatApiDetail } from '@/utils/formatApiDetail';

const RUN_TIMEOUT_SEC = 3.0;

/** API language keys sent to backend */
const LANGUAGE_OPTIONS = [
  { id: 'python', label: 'Python 3', monaco: 'python', ext: '.py' },
  { id: 'javascript', label: 'JavaScript (Node)', monaco: 'javascript', ext: '.js' },
  { id: 'cpp', label: 'C++ (g++)', monaco: 'cpp', ext: '.cpp' },
  { id: 'c', label: 'C (gcc)', monaco: 'c', ext: '.c' },
  { id: 'java', label: 'Java', monaco: 'java', ext: '.java' },
];

const DEFAULT_TEMPLATES = {
  python: `import sys\n\ndef main():\n    data = sys.stdin.read().strip().split()\n    # TODO: Implement solution\n    pass\n\nif __name__ == "__main__":\n    main()\n`,
  javascript: `const fs = require('fs');\n\nfunction main() {\n    const input = fs.readFileSync(0, 'utf-8').trim().split(/\\s+/);\n    // TODO: Implement solution\n}\n\nmain();\n`,
  cpp: `#include <iostream>\n#include <vector>\n#include <string>\nusing namespace std;\n\nint main() {\n    ios_base::sync_with_stdio(false);\n    cin.tie(NULL);\n    // TODO: Implement solution\n    return 0;\n}\n`,
  c: `#include <stdio.h>\n#include <stdlib.h>\n\nint main() {\n    // TODO: Implement solution\n    return 0;\n}\n`,
  java: `import java.util.*;\n\npublic class Solution {\n    public static void main(String[] args) {\n        Scanner sc = new Scanner(System.in);\n        // TODO: Implement solution\n    }\n}\n`,
};

function inferApiLanguageFromRecommended(recommended) {
  const raw = Array.isArray(recommended)
    ? recommended[0]
    : typeof recommended === 'string'
      ? recommended
      : 'python';
  const l = String(raw || 'python').toLowerCase();
  if (l.includes('typescript') || l === 'ts') return 'javascript';
  if (l.includes('javascript') || l.includes('node') || l === 'js') return 'javascript';
  if (l.includes('java') && !l.includes('javascript')) return 'java';
  if (l.includes('cpp') || l.includes('c++')) return 'cpp';
  if (l === 'c' || (l.includes(' c') && !l.includes('++'))) return 'c';
  if (l.includes('python') || l === 'py') return 'python';
  return 'python';
}

function monacoLanguageForApi(apiId) {
  const row = LANGUAGE_OPTIONS.find((o) => o.id === apiId);
  return row?.monaco || 'python';
}

export default function CodingWorkspace({
  sessionId,
  challengeId,
  questionIndex = 0,
  starterCode = '',
  starterTemplates = {},
  recommendedLanguages = ['python'],
  title = 'Solution',
  publicTestCases = [],
  onEditorFocus,
  onSubmitSuccess,
}) {
  const initialLang = useMemo(
    () => inferApiLanguageFromRecommended(recommendedLanguages),
    [recommendedLanguages]
  );

  const [selectedLang, setSelectedLang] = useState(initialLang);
  
  // Store code per language so language switching preserves candidate edits
  const [codeByLang, setCodeByLang] = useState(() => {
    const initial = { ...DEFAULT_TEMPLATES, ...starterTemplates };
    if (starterCode) {
      initial[initialLang] = starterCode;
    }
    return initial;
  });

  const [activeTab, setActiveTab] = useState(0);
  const [runLoading, setRunLoading] = useState(false);
  const [runError, setRunError] = useState(null);
  const [runResult, setRunResult] = useState(null);

  const [submitLoading, setSubmitLoading] = useState(false);
  const [submitError, setSubmitError] = useState(null);
  const [submissionEval, setSubmissionEval] = useState(null);
  const [copied, setCopied] = useState(false);

  // Sync starter templates if props change
  useEffect(() => {
    if (starterTemplates && Object.keys(starterTemplates).length > 0) {
      setCodeByLang((prev) => ({
        ...DEFAULT_TEMPLATES,
        ...starterTemplates,
        ...prev,
      }));
    }
  }, [starterTemplates]);

  // Sync initial language if recommended languages change
  useEffect(() => {
    const lang = inferApiLanguageFromRecommended(recommendedLanguages);
    setSelectedLang(lang);
  }, [recommendedLanguages]);

  const currentCode = codeByLang[selectedLang] || DEFAULT_TEMPLATES[selectedLang] || '';
  const monacoLang = useMemo(() => monacoLanguageForApi(selectedLang), [selectedLang]);
  const canRun = Array.isArray(publicTestCases) && publicTestCases.length > 0;

  const handleLanguageChange = (newLang) => {
    setSelectedLang(newLang);
    setRunResult(null);
    setRunError(null);
  };

  const handleCodeChange = (newVal) => {
    setCodeByLang((prev) => ({
      ...prev,
      [selectedLang]: newVal ?? '',
    }));
  };

  const handleRun = useCallback(async () => {
    if (!canRun) return;
    setRunLoading(true);
    setRunError(null);
    setRunResult(null);
    try {
      const payload = {
        language: selectedLang,
        source_code: currentCode,
        timeout_seconds: RUN_TIMEOUT_SEC,
        test_cases: publicTestCases.map((tc) => ({
          stdin: tc.stdin ?? '',
          expected_stdout: tc.expected_stdout ?? '',
          description: tc.description,
        })),
      };
      const data = await interviewService.runPublicCode(payload);
      setRunResult(data);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const fallback = err?.response?.data?.message || err?.message || 'Run failed';
      const msg = formatApiDetail(detail) || fallback;
      setRunError(msg);
    } finally {
      setRunLoading(false);
    }
  }, [canRun, currentCode, publicTestCases, selectedLang]);

  const handleSubmit = useCallback(async () => {
    if (!sessionId) {
      setSubmitError('Missing active interview session ID');
      return;
    }
    setSubmitLoading(true);
    setSubmitError(null);
    try {
      const payload = {
        challenge_id: challengeId || 'CHAL-CURRENT',
        language: selectedLang,
        source_code: currentCode,
        question_index: questionIndex,
      };
      const evaluation = await interviewService.submitCodingChallenge(sessionId, payload);
      setSubmissionEval(evaluation);
      onSubmitSuccess?.(evaluation);
    } catch (err) {
      const detail = err?.response?.data?.detail;
      const fallback = err?.response?.data?.message || err?.message || 'Submission failed';
      const msg = formatApiDetail(detail) || fallback;
      setSubmitError(msg);
    } finally {
      setSubmitLoading(false);
    }
  }, [challengeId, currentCode, onSubmitSuccess, questionIndex, selectedLang, sessionId]);

  const handleReset = useCallback(() => {
    const defaultTemplate = starterTemplates?.[selectedLang] || DEFAULT_TEMPLATES[selectedLang] || starterCode || '';
    setCodeByLang((prev) => ({
      ...prev,
      [selectedLang]: defaultTemplate,
    }));
    setRunResult(null);
    setRunError(null);
  }, [selectedLang, starterCode, starterTemplates]);

  const handleCopy = useCallback(async () => {
    try {
      await navigator.clipboard.writeText(currentCode);
      setCopied(true);
      setTimeout(() => setCopied(false), 2000);
    } catch {
      /* ignore */
    }
  }, [currentCode]);

  const editorOptions = useMemo(
    () => ({
      readOnly: submitLoading,
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
    [submitLoading]
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
        <span className="inline-flex items-center gap-1 rounded-md bg-amber-500/20 px-2.5 py-1 text-[11px] font-medium text-amber-200">
          <span className="h-1.5 w-1.5 rounded-full bg-amber-400" />
          Toolchain Missing
        </span>
      );
    }
    if (!runResult.compile_success) {
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-red-500/20 px-2.5 py-1 text-[11px] font-medium text-red-200">
          <span className="h-1.5 w-1.5 rounded-full bg-red-400" />
          Compile Error
        </span>
      );
    }
    if (runResult.all_passed) {
      return (
        <span className="inline-flex items-center gap-1 rounded-md bg-emerald-500/20 px-2.5 py-1 text-[11px] font-medium text-emerald-200">
          <span className="h-1.5 w-1.5 rounded-full bg-emerald-400" />
          All Public Tests Passed ({runResult.results?.filter((r) => r.passed).length}/{runResult.results?.length})
        </span>
      );
    }
    return (
      <span className="inline-flex items-center gap-1 rounded-md bg-orange-500/20 px-2.5 py-1 text-[11px] font-medium text-orange-200">
        <span className="h-1.5 w-1.5 rounded-full bg-orange-400" />
        Tests Failed ({runResult.results?.filter((r) => r.passed).length}/{runResult.results?.length} Passed)
      </span>
    );
  }, [runResult]);

  return (
    <div className="relative z-20 flex min-h-0 flex-col overflow-hidden rounded-xl border border-white/15 bg-[#1a1b26] shadow-2xl ring-1 ring-white/5">
      {/* Top Chrome / Header */}
      <div className="flex shrink-0 flex-wrap items-center justify-between gap-2 border-b border-white/10 bg-[#16161e] px-3 py-2.5">
        <div className="flex min-w-0 items-center gap-2">
          <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-md bg-emerald-500/20 text-xs font-bold text-emerald-300">
            {'</>'}
          </span>
          <div className="min-w-0">
            <p className="truncate text-xs font-semibold text-slate-200">{title}</p>
            <p className="text-[10px] text-slate-400">Sandboxed multi-language test runner (3.0s CPU limit)</p>
          </div>
        </div>

        <div className="flex flex-wrap items-center gap-2">
          {/* Language Selector */}
          <label className="flex items-center gap-1.5 text-[11px] text-slate-400">
            <span className="hidden sm:inline">Language:</span>
            <select
              value={selectedLang}
              onChange={(e) => handleLanguageChange(e.target.value)}
              className="max-w-[160px] rounded-md border border-white/15 bg-black/40 px-2 py-1 text-[11px] font-medium text-slate-200 outline-none focus:border-emerald-500/40"
            >
              {LANGUAGE_OPTIONS.map((opt) => (
                <option key={opt.id} value={opt.id}>
                  {opt.label}
                </option>
              ))}
            </select>
          </label>

          <button
            type="button"
            onClick={handleCopy}
            className="rounded-lg border border-white/15 bg-white/5 px-2.5 py-1 text-xs font-medium text-slate-200 transition hover:bg-white/10"
          >
            {copied ? 'Copied!' : 'Copy'}
          </button>
          <button
            type="button"
            onClick={handleReset}
            className="rounded-lg border border-amber-500/30 bg-amber-500/10 px-2.5 py-1 text-xs font-medium text-amber-100 transition hover:bg-amber-500/20"
          >
            Reset Boilerplate
          </button>
          <button
            type="button"
            onClick={handleRun}
            disabled={!canRun || runLoading || submitLoading}
            title={
              canRun
                ? 'Run candidate code against public test cases'
                : 'No public tests available for this challenge'
            }
            className="inline-flex items-center gap-1.5 rounded-lg border border-emerald-500/40 bg-emerald-600/90 px-3 py-1 text-xs font-semibold text-white shadow-lg shadow-emerald-900/30 transition hover:bg-emerald-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {runLoading ? (
              <>
                <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Running…</span>
              </>
            ) : (
              <>
                <span>▶ Run Public Tests</span>
              </>
            )}
          </button>

          {/* Final Solution Submission */}
          <button
            type="button"
            onClick={handleSubmit}
            disabled={submitLoading || runLoading}
            className="inline-flex items-center gap-1.5 rounded-lg border border-cyan-500/40 bg-gradient-to-r from-cyan-600 to-blue-600 px-3 py-1 text-xs font-semibold text-white shadow-lg shadow-cyan-900/30 transition hover:from-cyan-500 hover:to-blue-500 disabled:cursor-not-allowed disabled:opacity-40"
          >
            {submitLoading ? (
              <>
                <svg className="h-3.5 w-3.5 animate-spin" viewBox="0 0 24 24" fill="none">
                  <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
                  <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v8H4z" />
                </svg>
                <span>Evaluating…</span>
              </>
            ) : (
              <span>Submit Solution</span>
            )}
          </button>
        </div>
      </div>

      {/* Monaco Code Editor */}
      <div className="relative isolate h-[min(480px,48vh)] min-h-[340px] w-full flex-1 [&_.monaco-editor]:pointer-events-auto [&_.monaco-mouse-cursor-text]:pointer-events-auto">
        <Editor
          height="100%"
          language={monacoLang}
          theme="vs-dark"
          value={currentCode}
          onChange={handleCodeChange}
          onMount={handleMount}
          options={editorOptions}
          loading={
            <div className="flex h-full min-h-[340px] items-center justify-center bg-[#1e1e1e] text-sm text-slate-400">
              Loading editor environment…
            </div>
          }
        />
      </div>

      {/* Submission Success Dialog / Banner */}
      {submissionEval && (
        <div className="border-t border-cyan-500/30 bg-cyan-950/40 p-3">
          <div className="flex flex-wrap items-center justify-between gap-2">
            <div className="flex items-center gap-2">
              <span className="flex h-6 w-6 items-center justify-center rounded-full bg-cyan-500/20 text-xs font-bold text-cyan-300">
                ✓
              </span>
              <div>
                <p className="text-xs font-semibold text-cyan-100">Coding Solution Evaluated & Persisted</p>
                <p className="text-[11px] text-cyan-200/80">
                  Overall Score: <strong className="text-cyan-300">{submissionEval.overall_coding_score}/100</strong> · Public: {submissionEval.public_tests_passed}/{submissionEval.public_tests_total} · Hidden: {submissionEval.hidden_tests_passed}/{submissionEval.hidden_tests_total}
                </p>
              </div>
            </div>
            <span className="rounded-md bg-cyan-500/20 px-2 py-0.5 font-mono text-[10px] text-cyan-200">
              Total Runtime: {submissionEval.execution_time_total_ms}ms · Peak Mem: {(submissionEval.peak_memory_kb / 1024).toFixed(1)}MB
            </span>
          </div>
        </div>
      )}

      {/* Bottom Panel: Interactive Test Cases & Results */}
      <div className="shrink-0 border-t border-white/10 bg-[#16161e] p-3">
        {/* Test Case Tab Bar */}
        <div className="mb-2.5 flex flex-wrap items-center justify-between gap-2">
          <div className="flex items-center gap-1.5 overflow-x-auto pb-0.5">
            {publicTestCases.map((tc, idx) => {
              const res = runResult?.results?.[idx];
              return (
                <button
                  key={idx}
                  type="button"
                  onClick={() => setActiveTab(idx)}
                  className={`flex items-center gap-1.5 rounded-lg border px-2.5 py-1 text-xs font-medium transition ${
                    activeTab === idx
                      ? 'border-emerald-500/40 bg-emerald-950/40 text-emerald-200'
                      : 'border-white/10 bg-white/5 text-slate-400 hover:border-white/20 hover:text-slate-200'
                  }`}
                >
                  <span>{tc.description || `Case ${idx + 1}`}</span>
                  {res && (
                    <span
                      className={`h-2 w-2 rounded-full ${
                        res.passed ? 'bg-emerald-400' : 'bg-red-400'
                      }`}
                      title={res.passed ? 'Test Passed' : 'Test Failed'}
                    />
                  )}
                </button>
              );
            })}
          </div>
          {summaryBadge}
        </div>

        {/* Global Errors */}
        {runError && (
          <div className="mb-2 rounded-lg border border-red-500/30 bg-red-950/40 p-2.5 text-xs text-red-100">
            <p className="font-semibold">Execution Error / Timeout</p>
            <p className="mt-0.5 text-red-200/90">{runError}</p>
          </div>
        )}

        {submitError && (
          <div className="mb-2 rounded-lg border border-red-500/30 bg-red-950/40 p-2.5 text-xs text-red-100">
            <p className="font-semibold">Submission Error</p>
            <p className="mt-0.5 text-red-200/90">{submitError}</p>
          </div>
        )}

        {/* Compilation Error Details */}
        {runResult && !runResult.compile_success && runResult.compile_output ? (
          <div className="mb-2 rounded-lg border border-red-500/20 bg-black/50 p-3">
            <p className="mb-1 text-[11px] font-semibold uppercase tracking-wider text-red-300">
              Compilation / Syntax Diagnostic:
            </p>
            <pre className="max-h-36 overflow-auto font-mono text-[11px] leading-relaxed text-red-100/95">
              {runResult.compile_output}
            </pre>
          </div>
        ) : null}

        {/* Active Test Case Detail */}
        {publicTestCases.length > 0 && publicTestCases[activeTab] ? (
          (() => {
            const tc = publicTestCases[activeTab];
            const result = runResult?.results?.[activeTab];
            return (
              <div className="space-y-2 rounded-lg border border-white/10 bg-black/30 p-3 text-xs">
                <div className="flex flex-wrap items-center justify-between gap-2 border-b border-white/5 pb-2">
                  <div className="flex items-center gap-2">
                    <span className="font-semibold text-slate-200">
                      {tc.description || `Test Case ${activeTab + 1}`}
                    </span>
                    {result && (
                      <span
                        className={`rounded px-1.5 py-0.5 font-mono text-[10px] font-bold ${
                          result.passed
                            ? 'bg-emerald-500/20 text-emerald-300'
                            : 'bg-red-500/20 text-red-300'
                        }`}
                      >
                        {result.passed ? 'PASSED' : 'FAILED'}
                      </span>
                    )}
                  </div>
                  {result && (
                    <span className="font-mono text-[10px] text-slate-400">
                      exit code: {result.exit_code}
                    </span>
                  )}
                </div>

                {result?.error && (
                  <div className="rounded bg-red-950/30 p-2 font-mono text-[11px] text-red-200">
                    <span className="font-semibold">Error: </span>
                    {result.error}
                  </div>
                )}

                <div className="grid gap-2 sm:grid-cols-2">
                  <div>
                    <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-slate-400">
                      Standard Input (stdin)
                    </p>
                    <pre className="max-h-24 overflow-auto rounded border border-white/5 bg-black/50 p-2 font-mono text-[11px] text-slate-200">
                      {tc.stdin || '<empty>'}
                    </pre>
                  </div>
                  <div>
                    <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-slate-400">
                      Expected Output
                    </p>
                    <pre className="max-h-24 overflow-auto rounded border border-white/5 bg-black/50 p-2 font-mono text-[11px] text-emerald-300/90">
                      {tc.expected_stdout || '<empty>'}
                    </pre>
                  </div>
                </div>

                {result && (
                  <div className="mt-2 border-t border-white/5 pt-2">
                    <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-slate-400">
                      Your Program Output (stdout)
                    </p>
                    <pre
                      className={`max-h-28 overflow-auto rounded border p-2 font-mono text-[11px] ${
                        result.passed
                          ? 'border-emerald-500/20 bg-emerald-950/20 text-emerald-100'
                          : 'border-red-500/20 bg-red-950/20 text-red-100'
                      }`}
                    >
                      {result.actual_stdout || '<no output produced>'}
                    </pre>
                  </div>
                )}

                {result?.stderr ? (
                  <div className="mt-2 border-t border-white/5 pt-2">
                    <p className="mb-1 font-mono text-[10px] uppercase tracking-wider text-amber-400/80">
                      Stderr / Diagnostics
                    </p>
                    <pre className="max-h-24 overflow-auto rounded border border-amber-500/20 bg-amber-950/20 p-2 font-mono text-[11px] text-amber-100">
                      {result.stderr}
                    </pre>
                  </div>
                ) : null}
              </div>
            );
          })()
        ) : (
          <p className="text-[11px] text-slate-500">
            No public test cases configured for this question. Implement your solution and click &quot;Submit Solution&quot;.
          </p>
        )}
      </div>
    </div>
  );
}
