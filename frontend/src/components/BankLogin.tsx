'use client';

import { useState, useEffect } from 'react';

interface BankLoginProps {
  bankName: string;
  bankLogo: string;
  onComplete: () => void;
}

const authMessages = [
  'Verifying credentials...',
  'Establishing secure connection...',
  'Fetching account data...',
];

export default function BankLogin({ bankName, bankLogo, onComplete }: BankLoginProps) {
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [progress, setProgress] = useState(0);
  const [messageIndex, setMessageIndex] = useState(0);

  useEffect(() => {
    if (isLoading) {
      // Progress bar animation
      const progressInterval = setInterval(() => {
        setProgress((prev) => {
          if (prev >= 100) {
            clearInterval(progressInterval);
            return 100;
          }
          return prev + 2;
        });
      }, 30);

      // Cycling messages
      const messageInterval = setInterval(() => {
        setMessageIndex((prev) => (prev + 1) % authMessages.length);
      }, 1000);

      // Complete after ~3 seconds
      const completeTimeout = setTimeout(() => {
        onComplete();
      }, 3000);

      return () => {
        clearInterval(progressInterval);
        clearInterval(messageInterval);
        clearTimeout(completeTimeout);
      };
    }
  }, [isLoading, onComplete]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
  };

  return (
    <div className="animate-slide-in">
      {/* Progress Bar */}
      {isLoading && (
        <div className="absolute top-0 left-0 right-0 h-1 bg-white/10 overflow-hidden rounded-t-3xl">
          <div
            className="h-full bg-gradient-to-r from-teal-400 to-cyan-400 transition-all duration-300"
            style={{ width: `${progress}%` }}
          />
        </div>
      )}

      {/* Bank Logo */}
      <div className="flex flex-col items-center mb-8 mt-4">
        <div className="text-6xl mb-4">{bankLogo}</div>
        <h2 className="text-2xl font-bold text-white">{bankName}</h2>
        <p className="text-sm text-white/60 mt-1">Secure Banking Portal</p>
      </div>

      {!isLoading ? (
        <>
          {/* Login Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            {/* Username Field */}
            <div>
              <label htmlFor="username" className="block text-sm font-medium text-white/80 mb-2">
                Username or Email
              </label>
              <input
                id="username"
                type="text"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                placeholder="Enter your username or email"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all shadow-inner"
                style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)' }}
              />
            </div>

            {/* Password Field */}
            <div>
              <label htmlFor="password" className="block text-sm font-medium text-white/80 mb-2">
                Password
              </label>
              <input
                id="password"
                type="password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder="Enter your password"
                className="w-full px-4 py-3 rounded-xl bg-white/5 border border-white/20 text-white placeholder-white/40 focus:outline-none focus:ring-2 focus:ring-teal-400 focus:border-transparent transition-all shadow-inner"
                style={{ boxShadow: 'inset 0 2px 4px rgba(0, 0, 0, 0.2)' }}
              />
            </div>

            {/* Security Banner */}
            <div className="bg-teal-500/10 border border-teal-400/30 rounded-lg p-3 flex items-start gap-2">
              <svg className="w-5 h-5 text-teal-400 mt-0.5 flex-shrink-0" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z" />
              </svg>
              <p className="text-xs text-teal-200">
                Your credentials are securely encrypted and never stored.
              </p>
            </div>

            {/* Sign In Button */}
            <button
              type="submit"
              className="w-full bg-gradient-to-r from-teal-500 to-cyan-500 text-white py-3 rounded-xl font-semibold text-lg shadow-lg hover:shadow-teal-500/50 hover:scale-[1.02] transition-all duration-200"
            >
              Sign In
            </button>

            {/* Helper Links */}
            <div className="flex items-center justify-center gap-2 text-sm text-white/50">
              <button type="button" className="hover:text-white/70 transition-colors">
                Forgot password?
              </button>
              <span>•</span>
              <button type="button" className="hover:text-white/70 transition-colors">
                Create account
              </button>
            </div>
          </form>
        </>
      ) : (
        /* Loading State */
        <div className="flex flex-col items-center justify-center py-12">
          {/* Spinner */}
          <div className="relative w-16 h-16 mb-6">
            <div className="absolute inset-0 border-4 border-white/20 rounded-full"></div>
            <div className="absolute inset-0 border-4 border-transparent border-t-teal-400 rounded-full animate-spin"></div>
          </div>

          {/* Cycling Messages */}
          <p className="text-white text-lg font-medium animate-pulse">
            {authMessages[messageIndex]}
          </p>
        </div>
      )}

      <style jsx>{`
        @keyframes slide-in {
          from {
            opacity: 0;
            transform: translateX(100%);
          }
          to {
            opacity: 1;
            transform: translateX(0);
          }
        }

        .animate-slide-in {
          animation: slide-in 0.5s ease-out;
        }

        @keyframes spin {
          to {
            transform: rotate(360deg);
          }
        }

        .animate-spin {
          animation: spin 1s linear infinite;
        }
      `}</style>
    </div>
  );
}
