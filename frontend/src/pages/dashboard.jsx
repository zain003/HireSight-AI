/**
 * Dashboard Page
 */
import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import authService from '@/services/authService';
import ResumeUpload from '@/components/Resume/ResumeUpload';

export default function Dashboard() {
  const router = useRouter();
  const [user, setUser] = useState(null);
  const [profile, setProfile] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    if (!authService.isAuthenticated()) {
      router.push('/login');
      return;
    }

    loadUserData();
  }, [router]);

  const loadUserData = async () => {
    try {
      const userData = await authService.getCurrentUser();
      setUser(userData);

      try {
        const profileData = await authService.getProfile();
        setProfile(profileData);
      } catch (err) {
        // Profile doesn't exist yet
        console.log('No profile found');
      }
    } catch (err) {
      console.error('Failed to load user data:', err);
      authService.logout();
    } finally {
      setLoading(false);
    }
  };

  const handleUploadSuccess = (data) => {
    loadUserData(); // Reload profile after upload
  };

  const handleLogout = () => {
    authService.logout();
  };

  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center">
        <div className="text-xl">Loading...</div>
      </div>
    );
  }

  return (
    <div className="min-h-screen bg-gray-100">
      {/* Header */}
      <header className="bg-white shadow">
        <div className="container mx-auto px-4 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-blue-600">HireSIGHT AI</h1>
          <div className="flex items-center gap-4">
            <span className="text-gray-700">Welcome, {user?.username}</span>
            <button
              onClick={handleLogout}
              className="px-4 py-2 bg-red-600 text-white rounded hover:bg-red-700"
            >
              Logout
            </button>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="container mx-auto px-4 py-8">
        <div className="grid md:grid-cols-2 gap-8">
          {/* Profile Card */}
          <div className="bg-white p-6 rounded-lg shadow-md">
            <h2 className="text-xl font-bold mb-4">Your Profile</h2>
            
            {profile ? (
              <div className="space-y-3">
                <div>
                  <p className="text-gray-600 text-sm">Domain</p>
                  <p className="font-semibold">{profile.domain || 'Not set'}</p>
                </div>
                
                {profile.skills && (
                  <div>
                    <p className="text-gray-600 text-sm mb-2">Skills</p>
                    <div className="flex flex-wrap gap-2">
                      {JSON.parse(profile.skills).slice(0, 10).map((skill, index) => (
                        <span
                          key={index}
                          className="px-2 py-1 bg-blue-100 text-blue-800 rounded text-sm"
                        >
                          {skill}
                        </span>
                      ))}
                    </div>
                  </div>
                )}

                <div>
                  <p className="text-gray-600 text-sm">Job Role</p>
                  <p className="font-semibold">{profile.job_role || 'Not set'}</p>
                </div>

                <div>
                  <p className="text-gray-600 text-sm">Difficulty Level</p>
                  <p className="font-semibold">{profile.difficulty_level || 'Not set'}</p>
                </div>

                <a
                  href="/profile"
                  className="inline-block mt-4 px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
                >
                  Edit Profile
                </a>
              </div>
            ) : (
              <p className="text-gray-600">No profile found. Upload your resume to get started!</p>
            )}
          </div>

          {/* Resume Upload */}
          <div>
            <ResumeUpload onUploadSuccess={handleUploadSuccess} />
          </div>
        </div>

        {/* Quick Actions */}
        <div className="mt-8 grid md:grid-cols-3 gap-6">
          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl mb-3">📝</div>
            <h3 className="font-semibold mb-2">Start Interview</h3>
            <p className="text-gray-600 text-sm mb-4">Practice with AI-generated questions</p>
            <button className="px-4 py-2 bg-gray-300 text-gray-600 rounded cursor-not-allowed">
              Coming Soon
            </button>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl mb-3">📊</div>
            <h3 className="font-semibold mb-2">View History</h3>
            <p className="text-gray-600 text-sm mb-4">Check your past interviews</p>
            <button className="px-4 py-2 bg-gray-300 text-gray-600 rounded cursor-not-allowed">
              Coming Soon
            </button>
          </div>

          <div className="bg-white p-6 rounded-lg shadow-md text-center">
            <div className="text-4xl mb-3">⚙️</div>
            <h3 className="font-semibold mb-2">Settings</h3>
            <p className="text-gray-600 text-sm mb-4">Customize your preferences</p>
            <a
              href="/profile"
              className="inline-block px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-700"
            >
              Go to Profile
            </a>
          </div>
        </div>
      </main>
    </div>
  );
}
