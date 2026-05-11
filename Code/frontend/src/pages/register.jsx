/**
 * Register Page
 */
import RegisterForm from '@/components/Auth/RegisterForm';

export default function RegisterPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-100 px-4 py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(37,99,235,0.15),_transparent_40%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,_rgba(139,92,246,0.12),_transparent_45%)]" />
      <div className="relative z-10 w-full max-w-5xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
        <div className="grid md:grid-cols-2">
          <div className="hidden h-full bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-900 p-10 text-white md:block">
            <div>
              <a href="/" className="inline-block text-2xl font-extrabold">
                Hire<span className="text-indigo-300">SIGHT</span>
              </a>
              <h1 className="mt-8 text-3xl font-bold leading-tight">
                Create your candidate profile
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-slate-300">
                Register once and access resume parsing, role fit scoring, and interview readiness tracking.
              </p>
            </div>
            <div className="mt-8 grid gap-3">
              <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Fast onboarding</p>
                <p className="mt-1 text-sm font-semibold text-indigo-200">Complete your profile in under 2 minutes</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">AI powered</p>
                <p className="mt-1 text-sm font-semibold text-emerald-300">Automatic skill extraction from your resume</p>
              </div>
              <div className="rounded-lg border border-white/10 bg-white/5 px-4 py-3">
                <p className="text-xs uppercase tracking-[0.15em] text-slate-400">Interview ready</p>
                <p className="mt-1 text-sm font-semibold text-amber-300">Get role-fit insights before your first interview</p>
              </div>
            </div>
          </div>
          <div className="p-6 md:p-10">
            <div className="mb-7 flex items-center justify-between text-center md:text-left">
              <a href="/" className="inline-block text-2xl font-extrabold text-slate-900 md:hidden">
                Hire<span className="text-indigo-600">SIGHT</span>
              </a>
              <a href="/" className="text-sm font-medium text-slate-600 hover:text-slate-900">
                Back to Home
              </a>
            </div>
            <RegisterForm />
          </div>
        </div>
      </div>
    </div>
  );
}
