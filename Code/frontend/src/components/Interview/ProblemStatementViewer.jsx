import React, { useState, useMemo } from 'react';
import { Code2, Terminal, ShieldCheck, Lightbulb, FileText, CheckCircle2, Copy, Check, Info } from 'lucide-react';

/**
 * Formats inline markdown like `code`, **bold**, etc. into React nodes with high-contrast styling.
 */
function renderInlineFormattedText(text, isLight = false) {
  if (!text) return null;
  // Split by inline code `...`, bold **...**, and standalone keywords
  const parts = [];
  const regex = /(`[^`]+`|\*\*[^*]+\*\*)/g;
  let lastIdx = 0;
  let match;

  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIdx) {
      parts.push(text.substring(lastIdx, match.index));
    }
    const token = match[0];
    if (token.startsWith('`') && token.endsWith('`')) {
      const code = token.slice(1, -1);
      parts.push(
        <code
          key={match.index}
          className={`mx-0.5 rounded-md px-1.5 py-0.5 font-mono text-[12px] font-semibold ${
            isLight
              ? 'border border-indigo-200 bg-indigo-50 text-indigo-700'
              : 'border border-indigo-400/30 bg-indigo-950/60 text-indigo-200'
          }`}
        >
          {code}
        </code>
      );
    } else if (token.startsWith('**') && token.endsWith('**')) {
      const bold = token.slice(2, -2);
      const isAllowed = /allowed/i.test(bold);
      const isRejected = /rejected/i.test(bold);
      if (isAllowed) {
        parts.push(
          <span
            key={match.index}
            className={`inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-bold ${
              isLight
                ? 'border border-emerald-300 bg-emerald-50 text-emerald-700'
                : 'border border-emerald-400/30 bg-emerald-500/20 text-emerald-300'
            }`}
          >
            {bold}
          </span>
        );
      } else if (isRejected) {
        parts.push(
          <span
            key={match.index}
            className={`inline-flex items-center rounded px-1.5 py-0.5 text-[11px] font-bold ${
              isLight
                ? 'border border-red-300 bg-red-50 text-red-700'
                : 'border border-red-400/30 bg-red-500/20 text-red-300'
            }`}
          >
            {bold}
          </span>
        );
      } else {
        parts.push(
          <strong key={match.index} className={`font-semibold ${isLight ? 'text-slate-900' : 'text-white'}`}>
            {bold}
          </strong>
        );
      }
    }
    lastIdx = regex.lastIndex;
  }
  if (lastIdx < text.length) {
    parts.push(text.substring(lastIdx));
  }
  return parts;
}

export default function ProblemStatementViewer({ challenge, difficultyBadge, theme = 'light' }) {
  const isLight = theme === 'light';
  const [activeTab, setActiveTab] = useState('description');
  const [copiedInputIdx, setCopiedInputIdx] = useState(null);

  const rawStatement = challenge?.problem_statement || '';

  // Parse raw markdown statement into structured logical blocks
  const parsedData = useMemo(() => {
    if (!rawStatement) {
      return {
        descriptionLines: [],
        inputFormatLines: [],
        outputFormatLines: [],
        constraintLines: [],
        goalLines: [],
        parsedSampleTests: [],
      };
    }

    const lines = rawStatement.split('\n');
    let currentSection = 'description'; // description, input_format, output_format, constraints, goal, sample_tests

    const descriptionLines = [];
    const inputFormatLines = [];
    const outputFormatLines = [];
    const constraintLines = [];
    const goalLines = [];
    const sampleTestLines = [];

    const knownLangs = new Set(['python', 'javascript', 'typescript', 'cpp', 'c++', 'java', 'golang', 'rust', 'c']);
    const challengeTitleLower = (challenge?.title || '').trim().toLowerCase();

    let isHeaderLeadingPhase = true;

    for (const rawLine of lines) {
      const trimmed = rawLine.trim();
      const lower = trimmed.toLowerCase();

      // Skip redundant leading title & language list lines at the very top
      if (isHeaderLeadingPhase) {
        if (!trimmed) continue;
        if (
          lower === 'problem statement' ||
          lower === 'problem statement:' ||
          lower === challengeTitleLower ||
          lower === `problem statement: ${challengeTitleLower}` ||
          knownLangs.has(lower)
        ) {
          continue;
        }
        isHeaderLeadingPhase = false;
      }

      // Check section headers
      if (lower.startsWith('**input format') || lower.startsWith('input format') || lower.startsWith('### input format')) {
        currentSection = 'input_format';
        continue;
      }
      if (lower.startsWith('**output format') || lower.startsWith('output format') || lower.startsWith('### output format')) {
        currentSection = 'output_format';
        continue;
      }
      if (lower.startsWith('**constraints') || lower.startsWith('constraints:') || lower.startsWith('### constraints')) {
        currentSection = 'constraints';
        continue;
      }
      if (lower.startsWith('**goal') || lower.startsWith('goal:') || lower.startsWith('### goal') || lower.startsWith('**task') || lower.startsWith('task:')) {
        currentSection = 'goal';
        continue;
      }
      if (
        lower.startsWith('public sample test') ||
        lower.startsWith('sample test cases') ||
        lower.startsWith('**sample test cases') ||
        lower.startsWith('### sample test cases')
      ) {
        currentSection = 'sample_tests';
        continue;
      }

      if (currentSection === 'description') {
        descriptionLines.push(rawLine);
      } else if (currentSection === 'input_format') {
        inputFormatLines.push(rawLine);
      } else if (currentSection === 'output_format') {
        outputFormatLines.push(rawLine);
      } else if (currentSection === 'constraints') {
        constraintLines.push(rawLine);
      } else if (currentSection === 'goal') {
        goalLines.push(rawLine);
      } else if (currentSection === 'sample_tests') {
        sampleTestLines.push(rawLine);
      }
    }

    // Try to parse sample tests from sampleTestLines if challenge.public_test_cases is empty
    const parsedSampleTests = [];
    if (sampleTestLines.length > 0) {
      let curDesc = '';
      let curStdin = [];
      let curStdout = [];
      let readingMode = 'none'; // 'none', 'stdin', 'stdout'

      for (const line of sampleTestLines) {
        const tr = line.trim();
        const low = tr.toLowerCase();
        if (!tr) continue;

        if (low.startsWith('stdin') || low.startsWith('input:')) {
          readingMode = 'stdin';
          continue;
        }
        if (low.startsWith('expected stdout') || low.startsWith('stdout:') || low.startsWith('output:')) {
          readingMode = 'stdout';
          continue;
        }
        if (readingMode === 'none' || (readingMode === 'stdout' && !low.startsWith('allowed') && !low.startsWith('rejected') && tr.includes(' '))) {
          if (curStdin.length > 0 && curStdout.length > 0) {
            parsedSampleTests.push({
              description: curDesc || `Sample Test Case ${parsedSampleTests.length + 1}`,
              stdin: curStdin.join('\n').trim(),
              expected_stdout: curStdout.join('\n').trim(),
            });
            curStdin = [];
            curStdout = [];
          }
          curDesc = tr;
          readingMode = 'none';
          continue;
        }

        if (readingMode === 'stdin') {
          curStdin.push(tr);
        } else if (readingMode === 'stdout') {
          curStdout.push(tr);
        }
      }

      if (curStdin.length > 0 && curStdout.length > 0) {
        parsedSampleTests.push({
          description: curDesc || `Sample Test Case ${parsedSampleTests.length + 1}`,
          stdin: curStdin.join('\n').trim(),
          expected_stdout: curStdout.join('\n').trim(),
        });
      }
    }

    return {
      descriptionLines,
      inputFormatLines,
      outputFormatLines,
      constraintLines,
      goalLines,
      parsedSampleTests,
    };
  }, [rawStatement, challenge?.title]);

  const handleCopyInput = (stdin, idx) => {
    try {
      navigator.clipboard.writeText(stdin);
      setCopiedInputIdx(idx);
      setTimeout(() => setCopiedInputIdx(null), 2000);
    } catch { }
  };

  const publicTests = useMemo(() => {
    if (Array.isArray(challenge?.public_test_cases) && challenge.public_test_cases.length > 0) {
      return challenge.public_test_cases;
    }
    return parsedData.parsedSampleTests;
  }, [challenge?.public_test_cases, parsedData.parsedSampleTests]);

  return (
    <div
      className={`space-y-4 rounded-2xl p-5 shadow-xl backdrop-blur-xl transition-colors ${
        isLight
          ? 'border border-slate-200/90 bg-white text-slate-800 shadow-slate-200/50 ring-1 ring-slate-900/5'
          : 'border border-white/10 bg-slate-900/80 text-slate-100 shadow-2xl ring-1 ring-white/5'
      }`}
    >
      {/* Title & Language Bar */}
      <div
        className={`flex flex-wrap items-center justify-between gap-3 border-b pb-4 ${
          isLight ? 'border-slate-100' : 'border-white/10'
        }`}
      >
        <div>
          <div className="flex items-center gap-2 mb-1">
            <span
              className={`inline-flex items-center gap-1 rounded-md px-2 py-0.5 text-[10px] font-bold uppercase tracking-wider ${
                isLight
                  ? 'border border-emerald-300 bg-emerald-50 text-emerald-700'
                  : 'border border-emerald-400/30 bg-emerald-500/15 text-emerald-300'
              }`}
            >
              <Code2 className="h-3 w-3" />
              Coding Problem
            </span>
            {difficultyBadge && (
              <span
                className={`rounded-md px-2 py-0.5 text-[10px] font-medium ${
                  isLight
                    ? 'border border-amber-200 bg-amber-50 text-amber-800'
                    : 'border border-amber-400/30 bg-amber-500/10 text-amber-200'
                }`}
              >
                {difficultyBadge}
              </span>
            )}
          </div>
          <h2
            className={`text-xl font-bold tracking-tight sm:text-2xl ${
              isLight ? 'text-slate-900' : 'text-white'
            }`}
          >
            {challenge?.title || 'Algorithmic Challenge'}
          </h2>
        </div>

        {Array.isArray(challenge?.recommended_languages) && challenge.recommended_languages.length > 0 && (
          <div className="flex flex-wrap items-center gap-1.5">
            {challenge.recommended_languages.map((l) => (
              <span
                key={l}
                className={`rounded-lg border px-2.5 py-1 font-mono text-[11px] font-medium uppercase shadow-xs ${
                  isLight
                    ? 'border-slate-200 bg-slate-100 text-slate-700'
                    : 'border-white/10 bg-[#0B1120] text-slate-300'
                }`}
              >
                {l}
              </span>
            ))}
          </div>
        )}
      </div>

      {/* Navigation Tabs */}
      <div
        className={`flex flex-wrap items-center gap-2 border-b pb-2 text-xs ${
          isLight ? 'border-slate-100' : 'border-white/10'
        }`}
      >
        <button
          type="button"
          onClick={() => setActiveTab('description')}
          className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 font-medium transition ${
            activeTab === 'description'
              ? isLight
                ? 'border border-indigo-200 bg-indigo-50 text-indigo-700 shadow-xs font-semibold'
                : 'border border-indigo-500/40 bg-indigo-500/15 text-indigo-200 shadow-sm'
              : isLight
                ? 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          }`}
        >
          <FileText className="h-3.5 w-3.5" />
          <span>Description & Rules</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('io')}
          className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 font-medium transition ${
            activeTab === 'io'
              ? isLight
                ? 'border border-indigo-200 bg-indigo-50 text-indigo-700 shadow-xs font-semibold'
                : 'border border-indigo-500/40 bg-indigo-500/15 text-indigo-200 shadow-sm'
              : isLight
                ? 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          }`}
        >
          <Terminal className="h-3.5 w-3.5" />
          <span>I/O Format & Specs</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('tests')}
          className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 font-medium transition ${
            activeTab === 'tests'
              ? isLight
                ? 'border border-indigo-200 bg-indigo-50 text-indigo-700 shadow-xs font-semibold'
                : 'border border-indigo-500/40 bg-indigo-500/15 text-indigo-200 shadow-sm'
              : isLight
                ? 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          }`}
        >
          <CheckCircle2 className="h-3.5 w-3.5" />
          <span>Sample Tests ({publicTests.length})</span>
        </button>

        <button
          type="button"
          onClick={() => setActiveTab('all')}
          className={`flex items-center gap-1.5 rounded-xl px-3 py-1.5 font-medium transition ${
            activeTab === 'all'
              ? isLight
                ? 'border border-indigo-200 bg-indigo-50 text-indigo-700 shadow-xs font-semibold'
                : 'border border-indigo-500/40 bg-indigo-500/15 text-indigo-200 shadow-sm'
              : isLight
                ? 'text-slate-500 hover:bg-slate-100 hover:text-slate-800'
                : 'text-slate-400 hover:bg-white/5 hover:text-slate-200'
          }`}
        >
          <Info className="h-3.5 w-3.5" />
          <span>Full Document</span>
        </button>
      </div>

      {/* TAB CONTENT: DESCRIPTION & RULES */}
      {(activeTab === 'description' || activeTab === 'all') && (
        <div className="space-y-4">
          <div
            className={`rounded-xl border p-4 space-y-3 ${
              isLight ? 'border-slate-200/80 bg-slate-50/80' : 'border-white/5 bg-[#0B1120]/60'
            }`}
          >
            <h3
              className={`text-xs font-bold uppercase tracking-wider flex items-center gap-2 ${
                isLight ? 'text-indigo-700' : 'text-indigo-300'
              }`}
            >
              <Lightbulb className={`h-4 w-4 ${isLight ? 'text-indigo-600' : 'text-indigo-400'}`} />
              Problem Overview & Business Logic
            </h3>
            <div
              className={`space-y-2 text-sm leading-relaxed ${
                isLight ? 'text-slate-700' : 'text-slate-200'
              }`}
            >
              {parsedData.descriptionLines.map((line, idx) => {
                const trimmed = line.trim();
                if (!trimmed) return <div key={idx} className="h-1" />;

                // If bullet point
                if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                  return (
                    <div key={idx} className="flex items-start gap-2 pl-2">
                      <span
                        className={`mt-1.5 h-1.5 w-1.5 rounded-full shrink-0 ${
                          isLight ? 'bg-indigo-600' : 'bg-indigo-400'
                        }`}
                      />
                      <p className={isLight ? 'flex-1 text-slate-700' : 'flex-1 text-slate-300'}>
                        {renderInlineFormattedText(trimmed.slice(2), isLight)}
                      </p>
                    </div>
                  );
                }

                // If formula or code block line
                if (trimmed.includes('= min(') || trimmed.startsWith('timestamp user_id')) {
                  return (
                    <div
                      key={idx}
                      className={`my-2 rounded-lg border p-3 font-mono text-xs shadow-inner ${
                        isLight
                          ? 'border-indigo-200 bg-indigo-50/70 text-indigo-900'
                          : 'border-indigo-500/30 bg-[#060a14] text-indigo-200'
                      }`}
                    >
                      {renderInlineFormattedText(trimmed, isLight)}
                    </div>
                  );
                }

                return (
                  <p key={idx} className={isLight ? 'text-slate-700' : 'text-slate-300'}>
                    {renderInlineFormattedText(line, isLight)}
                  </p>
                );
              })}
            </div>
          </div>

          {parsedData.goalLines.length > 0 && (
            <div
              className={`rounded-xl border p-3.5 text-xs space-y-1 ${
                isLight
                  ? 'border-emerald-200 bg-emerald-50/90 text-emerald-800'
                  : 'border-emerald-500/20 bg-emerald-950/20 text-emerald-200'
              }`}
            >
              <span
                className={`font-bold uppercase tracking-wider flex items-center gap-1.5 ${
                  isLight ? 'text-emerald-800' : 'text-emerald-300'
                }`}
              >
                <CheckCircle2 className="h-3.5 w-3.5" />
                Target Objective:
              </span>
              <p className={`leading-relaxed ${isLight ? 'text-slate-700' : 'text-slate-300'}`}>
                {parsedData.goalLines.map((l, i) => (
                  <span key={i}>{renderInlineFormattedText(l, isLight)} </span>
                ))}
              </p>
            </div>
          )}
        </div>
      )}

      {/* TAB CONTENT: INPUT / OUTPUT FORMAT */}
      {(activeTab === 'io' || activeTab === 'all') && (
        <div className="space-y-4">
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {/* Input Format Box */}
            <div
              className={`rounded-xl border p-4 space-y-2.5 ${
                isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]'
              }`}
            >
              <div
                className={`flex items-center gap-2 font-bold text-xs uppercase tracking-wider ${
                  isLight ? 'text-slate-800' : 'text-slate-300'
                }`}
              >
                <Terminal className={`h-4 w-4 ${isLight ? 'text-sky-600' : 'text-sky-400'}`} />
                <span>Standard Input (stdin)</span>
              </div>
              <div
                className={`space-y-2 text-xs leading-relaxed ${
                  isLight ? 'text-slate-700' : 'text-slate-300'
                }`}
              >
                {parsedData.inputFormatLines.length > 0 ? (
                  parsedData.inputFormatLines.map((line, idx) => {
                    const trimmed = line.trim();
                    if (!trimmed) return <div key={idx} className="h-0.5" />;
                    if (trimmed.startsWith('- ') || trimmed.startsWith('* ')) {
                      return (
                        <div key={idx} className="flex items-start gap-1.5 pl-1">
                          <span
                            className={`mt-1 h-1 w-1 rounded-full shrink-0 ${
                              isLight ? 'bg-sky-600' : 'bg-sky-400'
                            }`}
                          />
                          <span className={isLight ? 'text-slate-700' : 'text-slate-300'}>
                            {renderInlineFormattedText(trimmed.slice(2), isLight)}
                          </span>
                        </div>
                      );
                    }
                    if (trimmed.includes('_') || trimmed.includes('C R N') || /^\w+(\s+\w+)+$/.test(trimmed)) {
                      return (
                        <pre
                          key={idx}
                          className={`rounded border p-2 font-mono text-[11px] ${
                            isLight
                              ? 'bg-white border-slate-200 text-sky-800'
                              : 'bg-black/60 border-white/5 text-sky-200'
                          }`}
                        >
                          {trimmed}
                        </pre>
                      );
                    }
                    return <p key={idx}>{renderInlineFormattedText(line, isLight)}</p>;
                  })
                ) : (
                  <p className={isLight ? 'text-slate-500' : 'text-slate-400'}>
                    Read input parameters directly from standard input (stdin).
                  </p>
                )}
              </div>
            </div>

            {/* Output Format Box */}
            <div
              className={`rounded-xl border p-4 space-y-2.5 ${
                isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]'
              }`}
            >
              <div
                className={`flex items-center gap-2 font-bold text-xs uppercase tracking-wider ${
                  isLight ? 'text-slate-800' : 'text-slate-300'
                }`}
              >
                <CheckCircle2 className={`h-4 w-4 ${isLight ? 'text-emerald-600' : 'text-emerald-400'}`} />
                <span>Standard Output (stdout)</span>
              </div>
              <div
                className={`space-y-2 text-xs leading-relaxed ${
                  isLight ? 'text-slate-700' : 'text-slate-300'
                }`}
              >
                {parsedData.outputFormatLines.length > 0 ? (
                  parsedData.outputFormatLines.map((line, idx) => (
                    <p key={idx}>{renderInlineFormattedText(line, isLight)}</p>
                  ))
                ) : (
                  <p className={isLight ? 'text-slate-500' : 'text-slate-400'}>
                    Print the result of each event or query to standard output (stdout).
                  </p>
                )}
              </div>
            </div>
          </div>

          {/* Constraints Callout */}
          <div
            className={`rounded-xl border p-4 space-y-2 text-xs ${
              isLight ? 'border-slate-200 bg-slate-50/70' : 'border-white/10 bg-[#0B1120]/70'
            }`}
          >
            <div
              className={`flex items-center gap-2 font-semibold uppercase tracking-wider text-[11px] ${
                isLight ? 'text-slate-800' : 'text-slate-300'
              }`}
            >
              <ShieldCheck className={`h-4 w-4 ${isLight ? 'text-amber-600' : 'text-amber-400'}`} />
              <span>Constraints & Complexity Bounds</span>
            </div>
            {challenge?.constraints ? (
              <p
                className={`font-mono leading-relaxed rounded p-2 border ${
                  isLight
                    ? 'bg-white border-slate-200 text-slate-800'
                    : 'bg-black/40 border-white/5 text-slate-300'
                }`}
              >
                {challenge.constraints}
              </p>
            ) : null}
            {parsedData.constraintLines.length > 0 && (
              <ul className={`space-y-1 ${isLight ? 'text-slate-600' : 'text-slate-400'}`}>
                {parsedData.constraintLines.map((l, i) => {
                  const trimmed = l.trim();
                  if (!trimmed) return null;
                  return (
                    <li key={i} className="flex items-start gap-1.5">
                      <span
                        className={`mt-1.5 h-1 w-1 rounded-full shrink-0 ${
                          isLight ? 'bg-amber-500' : 'bg-amber-400'
                        }`}
                      />
                      <span>{renderInlineFormattedText(trimmed.replace(/^[-*]\s*/, ''), isLight)}</span>
                    </li>
                  );
                })}
              </ul>
            )}
          </div>
        </div>
      )}

      {/* TAB CONTENT: PUBLIC SAMPLE TEST CASES */}
      {(activeTab === 'tests' || activeTab === 'all') && (
        <div className="space-y-3">
          <div className="flex items-center justify-between">
            <p
              className={`text-xs font-bold uppercase tracking-wider ${
                isLight ? 'text-slate-600' : 'text-slate-400'
              }`}
            >
              Public Sample Test Cases ({publicTests.length})
            </p>
          </div>

          {publicTests.length > 0 ? (
            <div className="space-y-3">
              {publicTests.map((tc, idx) => (
                <div
                  key={idx}
                  className={`rounded-xl border p-4 text-xs space-y-2 shadow-xs ${
                    isLight ? 'border-slate-200 bg-slate-50' : 'border-white/10 bg-[#0B1120]'
                  }`}
                >
                  <div
                    className={`flex items-center justify-between font-semibold ${
                      isLight ? 'text-slate-800' : 'text-slate-300'
                    }`}
                  >
                    <span className="flex items-center gap-2">
                      <span
                        className={`flex h-5 w-5 items-center justify-center rounded-full text-[10px] font-bold ${
                          isLight
                            ? 'bg-indigo-100 text-indigo-700'
                            : 'bg-indigo-500/20 text-indigo-300'
                        }`}
                      >
                        {idx + 1}
                      </span>
                      {tc.description || `Sample Test Case ${idx + 1}`}
                    </span>
                    <button
                      type="button"
                      onClick={() => handleCopyInput(tc.stdin, idx)}
                      className={`inline-flex items-center gap-1 rounded border px-2 py-0.5 text-[10px] transition ${
                        isLight
                          ? 'border-slate-200 bg-white text-slate-600 hover:text-slate-900 hover:bg-slate-100'
                          : 'border-white/10 text-slate-400 hover:text-white hover:bg-white/5'
                      }`}
                    >
                      {copiedInputIdx === idx ? (
                        <Check className="h-3 w-3 text-emerald-500" />
                      ) : (
                        <Copy className="h-3 w-3" />
                      )}
                      <span>{copiedInputIdx === idx ? 'Copied' : 'Copy Stdin'}</span>
                    </button>
                  </div>

                  <div className="grid grid-cols-1 sm:grid-cols-2 gap-3 pt-1">
                    <div
                      className={`rounded-lg border p-2.5 ${
                        isLight ? 'bg-white border-slate-200' : 'bg-black/60 border-white/5'
                      }`}
                    >
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-slate-500' : 'text-slate-500'
                        }`}
                      >
                        Input (stdin)
                      </span>
                      <pre
                        className={`font-mono text-[11px] overflow-x-auto whitespace-pre-wrap ${
                          isLight ? 'text-slate-800' : 'text-slate-200'
                        }`}
                      >
                        {tc.stdin}
                      </pre>
                    </div>

                    <div
                      className={`rounded-lg border p-2.5 ${
                        isLight
                          ? 'bg-emerald-50/50 border-emerald-200'
                          : 'bg-black/60 border-white/5'
                      }`}
                    >
                      <span
                        className={`text-[10px] font-bold uppercase tracking-wider block mb-1 ${
                          isLight ? 'text-emerald-700' : 'text-emerald-400'
                        }`}
                      >
                        Expected Output (stdout)
                      </span>
                      <pre
                        className={`font-mono text-[11px] overflow-x-auto whitespace-pre-wrap ${
                          isLight ? 'text-emerald-900' : 'text-emerald-300'
                        }`}
                      >
                        {tc.expected_stdout}
                      </pre>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p
              className={`text-xs italic p-3 rounded-xl border ${
                isLight
                  ? 'bg-slate-50 text-slate-500 border-slate-200'
                  : 'bg-[#0B1120] text-slate-500 border-white/5'
              }`}
            >
              No public sample test cases configured. Implement your solution based on the problem statement and click &quot;Run Public Tests&quot; or &quot;Submit Solution&quot;.
            </p>
          )}
        </div>
      )}
    </div>
  );
}
