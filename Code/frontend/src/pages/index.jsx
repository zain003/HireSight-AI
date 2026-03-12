/**
 * Landing Page — HireSIGHT AI
 */
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import authService from '@/services/authService';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    if (authService.isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-white relative">
      {/* ── Hero Section ── */}
      <section className="border-b border-deep-night/[0.08] bg-gradient-to-br from-deep-night via-royal-plum to-neon-violet">
        <div className="container mx-auto px-6 py-16 md:py-24">
          <div className="grid md:grid-cols-2 gap-10 items-center">
            {/* Left: Text */}
            <div className="text-white space-y-7">
              <div className="inline-flex items-center gap-2 px-4 py-2 border border-white/20 bg-white/5">
                <span className="w-2 h-2 bg-neon-glow" />
                <span className="text-xs tracking-[0.22em] uppercase text-white/70">
                  Structured AI Interview Screening
                </span>
              </div>

              <h1 className="text-4xl md:text-5xl lg:text-6xl font-semibold leading-tight tracking-tight">
                Let AI interview your
                <span className="block text-neon-glow-light text-neon-glow">
                  next candidate.
                </span>
              </h1>

              <p className="text-base md:text-lg text-white/75 max-w-xl leading-relaxed">
                HireSIGHT reads resumes, matches skills to job posts, and
                prepares an interview that is laser‑focused on what the role
                actually needs.
              </p>

              <div className="flex flex-wrap gap-4">
                <a
                  href="/register"
                  className="neon-btn px-8 py-3 text-sm font-semibold tracking-wide"
                >
                  Get Started
                </a>
                <a
                  href="/login"
                  className="px-8 py-3 text-sm font-semibold tracking-wide text-white border border-white/30 bg-transparent hover:bg-white/10"
                >
                  Candidate Sign In
                </a>
                <a
                  href="/admin-login"
                  className="px-8 py-3 text-sm font-semibold tracking-wide text-white border border-neon-glow bg-neon-glow/10 hover:bg-neon-glow/20"
                >
                  Admin Console
                </a>
              </div>
            </div>

            {/* Right: Boxy illustration of AI interview with robot image */}
            <div className="bg-surface-subtle border border-white/10 md:border-deep-night/20 p-6 md:p-8">
              <div className="mb-4 overflow-hidden border border-deep-night/20 bg-white">
                <img
                  src={`${process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000'}/uploads/img1.png`}
                  alt="AI robot interviewing a candidate"
                  className="w-full h-48 object-cover"
                />
              </div>
              <div className="flex justify-between text-xs text-text-muted mb-4">
                <span>AI Interview Room</span>
                <span>Realtime skill‑based screening</span>
              </div>
              <div className="grid grid-cols-5 gap-4">
                {/* Robot interviewer */}
                <div className="col-span-2 border border-deep-night/20 bg-white flex flex-col justify-between p-4">
                  <div className="flex items-center gap-2 mb-3">
                    <div className="w-8 h-8 border border-deep-night/40 bg-surface-subtle flex items-center justify-center">
                      <span className="text-xs font-semibold">AI</span>
                    </div>
                    <div>
                      <p className="text-xs font-medium text-deep-night">Robot Interviewer</p>
                      <p className="text-[10px] text-text-muted">Skill‑aware questions</p>
                    </div>
                  </div>
                  <div className="space-y-2 text-[11px]">
                    <div className="border border-deep-night/10 bg-surface-subtle px-2 py-1">
                      “Tell me about a project where you deployed a model in
                      production.”
                    </div>
                    <div className="border border-deep-night/10 bg-surface-subtle px-2 py-1">
                      “How do you monitor data drift in an ML system?”
                    </div>
                  </div>
                </div>

                {/* Candidate */}
                <div className="col-span-3 border border-deep-night/20 bg-white p-4 flex flex-col">
                  <div className="flex items-center justify-between mb-3">
                    <div className="flex items-center gap-2">
                      <div className="w-8 h-8 border border-deep-night/40 bg-surface-subtle" />
                      <div>
                        <p className="text-xs font-medium text-deep-night">Candidate</p>
                        <p className="text-[10px] text-text-muted">AI Engineer</p>
                      </div>
                    </div>
                    <span className="text-[11px] text-text-muted">
                      Match score: <span className="text-neon-glow-light">82%</span>
                    </span>
                  </div>
                  <div className="grid grid-cols-2 gap-2 text-[11px] mb-3">
                    <div className="border border-deep-night/10 bg-surface-subtle px-2 py-1">
                      Python · TensorFlow · NLP
                    </div>
                    <div className="border border-deep-night/10 bg-surface-subtle px-2 py-1">
                      Model deployment · MLOps
                    </div>
                  </div>
                  <div className="mt-auto text-[11px] text-text-muted">
                    Questions generated from required skills of “AI Engineer”
                    job post.
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* ── How it works ── */}
      <section className="py-16 bg-white">
        <div className="container mx-auto px-6">
          <h2 className="text-2xl md:text-3xl font-semibold text-deep-night text-center mb-4">
            A simple, structured pipeline
          </h2>
          <p className="text-text-muted text-center mb-12 max-w-xl mx-auto text-sm">
            From job post to interview questions, every step is aligned with
            the role you&apos;re hiring or applying for.
          </p>

          <div className="grid md:grid-cols-3 gap-6 max-w-5xl mx-auto">
            {[
              {
                label: '01',
                title: 'Job requirements first',
                desc: 'Admin creates a job post; HireSIGHT extracts a clean list of required skills from the description.',
              },
              {
                label: '02',
                title: 'Resume intelligence',
                desc: 'Your resume is parsed with BERT‑NER and ontology rules to build a structured skill profile.',
              },
              {
                label: '03',
                title: 'Match & eligibility',
                desc: 'Only when your skills match ≥ 70% of the job requirements are you marked as interview‑ready.',
              },
            ].map((step, i) => (
              <div
                key={step.label}
                className="border border-deep-night/[0.08] bg-surface-subtle p-6 flex flex-col gap-3"
              >
                <div className="flex items-center justify-between text-xs text-text-muted">
                  <span className="px-2 py-1 border border-deep-night/20 text-[11px] tracking-[0.18em] uppercase">
                    Step {step.label}
                  </span>
                  <span className="w-8 h-px bg-deep-night/15" />
                </div>
                <h3 className="text-base font-semibold text-deep-night">
                  {step.title}
                </h3>
                <p className="text-xs text-text-muted leading-relaxed">
                  {step.desc}
                </p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer ── */}
      <footer className="py-8 text-center border-t border-deep-night/[0.06] bg-surface-subtle">
        <p className="text-text-muted text-xs">
          © 2026 <span className="font-semibold text-deep-night">HireSIGHT AI</span>. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
