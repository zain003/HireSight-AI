import Link from 'next/link';
import { Moon, Sparkles } from 'lucide-react';

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/jobs', label: 'Jobs' },
  { href: '/apply', label: 'Apply' },
  { href: '/profile', label: 'Profile' },
];

export default function CandidateHeader({ activePath, user, onLogout }) {
  const initial = user?.username?.charAt(0)?.toUpperCase() || 'U';

  return (
    <header className="sticky top-0 z-50 border-b border-slate-200/80 bg-white/95 backdrop-blur-md shadow-xs">
      <div className="max-w-7xl mx-auto flex flex-wrap items-center justify-between gap-4 px-4 sm:px-6 lg:px-8 py-3.5">
        {/* Brand Logo */}
        <Link href="/dashboard" className="flex items-center gap-2.5 group">
          <div className="flex h-9 w-9 items-center justify-center rounded-xl bg-gradient-to-tr from-blue-600 to-indigo-600 text-white shadow-sm transition-transform group-hover:scale-105">
            <Sparkles className="h-5 w-5" />
          </div>
          <span className="text-lg font-bold tracking-tight text-slate-900">
            Hire<span className="text-indigo-600">Sight</span>
          </span>
        </Link>

        {/* Navigation Tabs */}
        <nav className="order-3 w-full sm:order-2 sm:w-auto">
          <div className="flex flex-wrap items-center gap-1.5">
            {navItems.map((item) => {
              const active = activePath === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-xl px-3.5 py-1.5 text-xs sm:text-sm font-medium transition-all ${
                    active
                      ? 'bg-indigo-50 text-indigo-700 font-semibold shadow-2xs border border-indigo-100/80'
                      : 'text-slate-600 hover:bg-slate-100/80 hover:text-slate-900'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>

        {/* User Capsule & Actions */}
        <div className="order-2 flex items-center gap-3 sm:order-3">
          <button
            type="button"
            className="flex h-8 w-8 items-center justify-center rounded-xl text-slate-400 hover:bg-slate-100 hover:text-slate-700 transition"
            aria-label="Toggle theme"
            title="Theme"
          >
            <Moon className="h-4 w-4" />
          </button>

          <div className="hidden items-center gap-2 sm:flex">
            <div className="flex h-7 w-7 items-center justify-center rounded-full bg-blue-700 text-xs font-bold text-white shadow-xs">
              {initial}
            </div>
            <span className="text-xs sm:text-sm font-medium text-slate-800">
              {user?.username || 'User'}
            </span>
          </div>

          <button
            type="button"
            onClick={onLogout}
            className="rounded-xl border border-slate-200 bg-white px-3 py-1.5 text-xs font-semibold text-slate-700 hover:bg-slate-50 transition shadow-2xs"
          >
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
