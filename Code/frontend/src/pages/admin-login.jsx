/**
 * Admin Login Page
 */
import AdminLoginForm from '@/components/Auth/AdminLoginForm';

export default function AdminLoginPage() {
  return (
    <div className="min-h-screen bg-white flex items-center justify-center relative overflow-hidden">
      {/* Background subtle decoration */}
      <div className="absolute top-0 right-0 w-96 h-96 bg-neon-violet/[0.03] rounded-full blur-3xl -translate-y-1/2 translate-x-1/2" />
      <div className="absolute bottom-0 left-0 w-80 h-80 bg-neon-glow/[0.02] rounded-full blur-3xl translate-y-1/2 -translate-x-1/2" />

      <div className="relative z-10 w-full max-w-md px-6 animate-fade-in">
        {/* Logo */}
        <div className="text-center mb-8">
          <a href="/" className="inline-block">
            <h1 className="text-3xl font-extrabold text-deep-night tracking-tight">
              Hire<span className="text-neon-glow">SIGHT</span>
            </h1>
          </a>
        </div>
        <AdminLoginForm />
      </div>
    </div>
  );
}
