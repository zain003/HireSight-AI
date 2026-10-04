/**
 * Candidate Register Page
 * Luxury Executive Split Layout for Candidate Profile Creation
 */
import Head from 'next/head';
import Link from 'next/link';
import { Sparkles, CheckCircle2, ShieldCheck, Zap, Award, ArrowLeft, BrainCircuit } from 'lucide-react';
import RegisterForm from '@/components/Auth/RegisterForm';

export default function RegisterPage() {
  return (
    <>
      <Head>
        <title>Create Candidate Profile — HireSIGHT AI</title>
      </Head>

      <div className="relative flex min-h-screen items-center justify-center bg-[#F8FAFC] px-4 py-8 sm:px-6 lg:px-8">
        {/* Background Ambient Glows */}
        <div className="pointer-events-none absolute top-0 right-1/4 h-[500px] w-[500px] rounded-full bg-indigo-100/60 blur-3xl" />
        <div className="pointer-events-none absolute bottom-0 left-1/4 h-[400px] w-[400px] rounded-full bg-violet-100/50 blur-3xl" />

        <div className="relative z-10 w-full max-w-5xl overflow-hidden rounded-3xl border border-slate-200/90 bg-white shadow-2xl">
          <div className="grid lg:grid-cols-12">
            {/* Left Column: Hero Brand Showcase */}
            <div className="hidden flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-950 p-10 text-white lg:col-span-5 lg:flex">
              <div>
                {/* Brand Logo */}
                <div className="flex items-center gap-3">
                  <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-indigo-600 font-black text-white shadow-md shadow-indigo-600/30">
                    H
                  </div>
                  <div>
                    <span className="text-xl font-extrabold tracking-tight text-white">
                      Hire<span className="text-indigo-400">SIGHT</span>
                    </span>
                    <span className="block text-[10px] font-semibold uppercase tracking-wider text-slate-400">
                      Candidate Onboarding
                    </span>
                  </div>
                </div>

                <div className="mt-12 space-y-4">
                  <span className="inline-flex items-center gap-1.5 rounded-full border border-indigo-400/30 bg-indigo-500/15 px-3 py-1 text-xs font-bold uppercase tracking-wider text-indigo-300">
                    <Sparkles className="h-3.5 w-3.5" />
                    <span>Free Candidate Access</span>
                  </span>
                  <h1 className="text-2xl font-black leading-tight sm:text-3xl">
                    Showcase Your Real Technical Mastery.
                  </h1>
                  <p className="text-xs leading-relaxed text-slate-300">
                    Register in under 2 minutes. Upload your resume, match with high-growth engineering roles, and undergo structured, unbiased AI evaluations.
                  </p>
                </div>
              </div>

              {/* Feature Value Props */}
              <div className="space-y-3 pt-8 border-t border-white/10">
                <div className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-3.5">
                  <Zap className="h-5 w-5 text-indigo-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-bold text-white">Instant Resume Skill Extraction</p>
                    <p className="text-[11px] text-slate-400">Automatic O*NET competency benchmark matching.</p>
                  </div>
                </div>

                <div className="flex items-start gap-3 rounded-xl border border-white/10 bg-white/5 p-3.5">
                  <Award className="h-5 w-5 text-emerald-400 shrink-0 mt-0.5" />
                  <div>
                    <p className="text-xs font-bold text-white">Single-Source Recruiter Dossier</p>
                    <p className="text-[11px] text-slate-400">Your results are formatted into an explainable hiring report.</p>
                  </div>
                </div>

                <div className="flex items-center justify-between pt-2 text-[11px] text-slate-400">
                  <span>Zero Evaluation Bias</span>
                  <Link href="/login" className="text-indigo-400 hover:text-indigo-300 font-semibold underline">
                    Already registered? Sign In →
                  </Link>
                </div>
              </div>
            </div>

            {/* Right Column: Form Area */}
            <div className="flex flex-col justify-between p-6 sm:p-10 lg:col-span-7">
              {/* Top Navigation */}
              <div className="mb-4 flex items-center justify-between">
                <Link
                  href="/"
                  className="inline-flex items-center gap-1.5 text-xs font-bold text-slate-500 transition hover:text-slate-900"
                >
                  <ArrowLeft className="h-3.5 w-3.5" />
                  <span>Back to Home</span>
                </Link>

                <div className="flex items-center gap-2 lg:hidden">
                  <span className="text-base font-extrabold text-slate-900">
                    Hire<span className="text-indigo-600">SIGHT</span>
                  </span>
                </div>
              </div>

              {/* RegisterForm Component */}
              <div className="my-auto">
                <RegisterForm />
              </div>

              {/* Footer text */}
              <div className="mt-4 text-center text-[11px] text-slate-400">
                Protected by reCAPTCHA and standard industry encryption protocols.
              </div>
            </div>
          </div>
        </div>
      </div>
    </>
  );
}
