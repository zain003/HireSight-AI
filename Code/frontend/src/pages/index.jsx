/**
 * Landing Page
 */
import { useRouter } from 'next/router';
import { useEffect } from 'react';
import authService from '@/services/authService';

export default function Home() {
  const router = useRouter();

  useEffect(() => {
    // Redirect to dashboard if already logged in
    if (authService.isAuthenticated()) {
      router.push('/dashboard');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-500 to-purple-600">
      <div className="container mx-auto px-4 py-16">
        <div className="text-center text-white">
          <h1 className="text-5xl font-bold mb-6">
            HireSIGHT AI
          </h1>
          <p className="text-xl mb-8">
            AI-Powered Interview Preparation Platform
          </p>
          <p className="text-lg mb-12 max-w-2xl mx-auto">
            Upload your resume, get personalized interview questions, and practice with AI-powered feedback.
          </p>

          <div className="flex gap-4 justify-center">
            <a
              href="/register"
              className="px-8 py-3 bg-white text-blue-600 rounded-lg font-semibold hover:bg-gray-100 transition"
            >
              Get Started
            </a>
            <a
              href="/login"
              className="px-8 py-3 bg-transparent border-2 border-white text-white rounded-lg font-semibold hover:bg-white hover:text-blue-600 transition"
            >
              Login
            </a>
          </div>
        </div>

        <div className="mt-16 grid md:grid-cols-3 gap-8 text-white">
          <div className="text-center p-6">
            <div className="text-4xl mb-4">📄</div>
            <h3 className="text-xl font-semibold mb-2">Upload Resume</h3>
            <p>AI extracts your skills and experience automatically</p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">🎯</div>
            <h3 className="text-xl font-semibold mb-2">Get Questions</h3>
            <p>Personalized interview questions based on your profile</p>
          </div>
          <div className="text-center p-6">
            <div className="text-4xl mb-4">💡</div>
            <h3 className="text-xl font-semibold mb-2">Practice & Improve</h3>
            <p>AI-powered feedback to ace your interviews</p>
          </div>
        </div>
      </div>
    </div>
  );
}
