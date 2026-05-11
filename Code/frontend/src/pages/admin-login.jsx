/**
 * Admin Login Page
 */
import AdminLoginForm from '@/components/Auth/AdminLoginForm';

export default function AdminLoginPage() {
  return (
    <div className="relative flex min-h-screen items-center justify-center overflow-hidden bg-slate-100 px-4 py-10">
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_top_right,_rgba(220,38,38,0.1),_transparent_35%)]" />
      <div className="absolute inset-0 bg-[radial-gradient(circle_at_bottom_left,_rgba(15,23,42,0.12),_transparent_45%)]" />
      <div className="relative z-10 w-full max-w-5xl overflow-hidden rounded-3xl border border-slate-200 bg-white shadow-2xl">
        <div className="grid md:grid-cols-2">
          <div className="hidden h-full flex-col justify-between bg-gradient-to-br from-slate-950 via-slate-900 to-indigo-900 p-10 text-white md:flex">
            <div>
              <a href="/" className="inline-block text-2xl font-extrabold">
                Hire<span className="text-indigo-300">SIGHT</span>
              </a>
              <h1 className="mt-8 text-3xl font-bold leading-tight">
                Secure admin access
              </h1>
              <p className="mt-4 text-sm leading-relaxed text-slate-300">
                Manage job postings, candidate pipeline, and interview analytics from the control center.
              </p>
            </div>
            <div>
              <ul className="space-y-3 text-sm text-slate-300">
                <li className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">Role and requirement management</li>
                <li className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">Candidate screening oversight</li>
                <li className="rounded-lg border border-white/10 bg-white/5 px-3 py-2">Interview quality and performance tracking</li>
              </ul>
              <p className="pt-4 text-xs text-slate-400">Restricted administrative area with privileged controls.</p>
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
            <AdminLoginForm />
          </div>
        </div>
      </div>
    </div>
  );
}
