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
    <div className="min-h-screen bg-white relative overflow-hidden">
      {/* ── Hero Section ── */}
      <section className="relative min-h-[92vh] flex items-center justify-center">
        {/* Dark gradient background */}
        <div className="absolute inset-0 bg-gradient-to-br from-deep-night via-royal-plum to-neon-violet" />

        {/* Animated glow orbs */}
        <div className="absolute top-1/4 left-1/4 w-96 h-96 bg-neon-glow/10 rounded-full blur-3xl animate-glow-pulse" />
        <div className="absolute bottom-1/4 right-1/4 w-80 h-80 bg-neon-glow-light/8 rounded-full blur-3xl animate-glow-pulse" style={{ animationDelay: '1.5s' }} />
        <div className="absolute top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 w-[600px] h-[600px] bg-neon-violet/5 rounded-full blur-3xl" />

        {/* Grid pattern overlay */}
        <div
          className="absolute inset-0 opacity-[0.03]"
          style={{
            backgroundImage: `linear-gradient(rgba(255,255,255,.1) 1px, transparent 1px),
                              linear-gradient(90deg, rgba(255,255,255,.1) 1px, transparent 1px)`,
            backgroundSize: '60px 60px',
          }}
        />

        {/* Content */}
        <div className="relative z-10 container mx-auto px-6 text-center animate-fade-in">
          {/* Badge */}
          <div className="inline-flex items-center gap-2 px-4 py-1.5 mb-8 rounded-full border border-white/10 bg-white/5 backdrop-blur-md">
            <span className="w-2 h-2 rounded-full bg-neon-glow animate-glow-pulse" />
            <span className="text-sm text-white/70 tracking-wide">AI-Powered Interview Platform</span>
          </div>

          <h1 className="text-5xl md:text-7xl font-extrabold text-white mb-6 leading-tight tracking-tight">
            Hire<span className="text-neon-glow-light text-neon-glow">SIGHT</span>{' '}
            <span className="text-white/90">AI</span>
          </h1>

          <p className="text-lg md:text-xl text-white/60 mb-12 max-w-2xl mx-auto leading-relaxed font-light">
            Upload your resume, receive personalized interview questions, and
            practice with AI-powered feedback — all in one platform.
          </p>

          {/* CTAs */}
          <div className="flex gap-4 justify-center flex-wrap">
            <a
              href="/register"
              className="neon-btn px-8 py-3.5 rounded-xl font-semibold text-base tracking-wide"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-8 py-3.5 rounded-xl font-semibold text-base tracking-wide text-white border border-white/15 bg-white/5 backdrop-blur-sm hover:bg-white/10 hover:border-white/25"
            >
              Sign In
            </a>
          </div>
        </div>
      </section>

      {/* ── Features ── */}
      <section className="relative py-24 bg-white">
        {/* subtle top gradient bleed */}
        <div className="absolute top-0 left-0 right-0 h-32 bg-gradient-to-b from-deep-night/[0.02] to-transparent" />

        <div className="container mx-auto px-6">
          <h2 className="text-3xl md:text-4xl font-bold text-center text-deep-night mb-4">
            How It Works
          </h2>
          <p className="text-text-muted text-center mb-16 max-w-lg mx-auto">
            Three simple steps to ace your next interview
          </p>

          <div className="grid md:grid-cols-3 gap-8 max-w-5xl mx-auto">
            {[
              {
                icon: '📄',
                title: 'Upload Resume',
                desc: 'AI extracts your skills and experience automatically',
                delay: '0s',
              },
              {
                icon: '🎯',
                title: 'Get Questions',
                desc: 'Personalized interview questions based on your profile',
                delay: '0.15s',
              },
              {
                icon: '💡',
                title: 'Practice & Improve',
                desc: 'AI-powered feedback to ace your interviews',
                delay: '0.3s',
              },
            ].map((f, i) => (
              <div
                key={i}
                className="group relative p-8 rounded-2xl bg-white border border-deep-night/[0.06] shadow-card hover:shadow-card-hover hover:border-neon-violet/20 transition-all duration-300 text-center animate-slide-up"
                style={{ animationDelay: f.delay }}
              >
                {/* Neon accent line */}
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-12 h-0.5 bg-gradient-to-r from-transparent via-neon-violet to-transparent rounded-full opacity-0 group-hover:opacity-100 transition-opacity duration-300" />

                <div className="text-5xl mb-5">{f.icon}</div>
                <h3 className="text-xl font-semibold text-deep-night mb-2">{f.title}</h3>
                <p className="text-text-muted text-sm leading-relaxed">{f.desc}</p>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ── Footer accent ── */}
      <footer className="py-8 text-center border-t border-deep-night/[0.06]">
        <p className="text-text-muted text-sm">
          © 2026 <span className="font-semibold text-deep-night">HireSIGHT AI</span>. All rights reserved.
        </p>
      </footer>
    </div>
  );
}
