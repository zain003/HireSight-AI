import Link from 'next/link';

const navItems = [
  { href: '/dashboard', label: 'Dashboard' },
  { href: '/jobs', label: 'Jobs' },
  { href: '/apply', label: 'Apply' },
  { href: '/profile', label: 'Profile' },
];

export default function CandidateHeader({ activePath, user, onLogout }) {
  return (
    <header className="sticky top-0 z-50 border-b border-white/10 bg-slate-950/90 backdrop-blur">
      <div className="container mx-auto flex flex-wrap items-center justify-between gap-3 px-6 py-4">
        <Link href="/" className="text-xl font-extrabold tracking-tight text-white">
          Hire<span className="text-indigo-300">SIGHT</span>
        </Link>

        <nav className="order-3 w-full sm:order-2 sm:w-auto">
          <div className="flex flex-wrap items-center gap-2">
            {navItems.map((item) => {
              const active = activePath === item.href;
              return (
                <Link
                  key={item.href}
                  href={item.href}
                  className={`rounded-lg px-3 py-1.5 text-sm font-medium transition ${
                    active
                      ? 'bg-indigo-500 text-white'
                      : 'text-slate-300 hover:bg-white/10 hover:text-white'
                  }`}
                >
                  {item.label}
                </Link>
              );
            })}
          </div>
        </nav>

        <div className="order-2 flex items-center gap-3 sm:order-3">
          <div className="hidden items-center gap-2 sm:flex">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-indigo-500 text-xs font-bold text-white">
              {user?.username?.charAt(0)?.toUpperCase() || 'U'}
            </div>
            <span className="text-sm font-medium text-slate-200">{user?.username}</span>
          </div>
          <button
            onClick={onLogout}
            className="rounded-lg border border-white/20 px-3 py-1.5 text-sm font-medium text-slate-200 hover:bg-white/10"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
  );
}
