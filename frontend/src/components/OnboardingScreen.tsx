'use client';

import { useState } from 'react';
import Logo from './Logo';
import LoadingAnimation from './LoadingAnimation';

export default function OnboardingScreen() {
  const [isLoading, setIsLoading] = useState(false);

  const handleConnectBank = () => {
    // TODO: Integrate with Plaid Link
    alert('Plaid Link integration coming soon!');
  };

  const handleLoadDemo = () => {
    setIsLoading(true);
    // Simulate loading demo data
    setTimeout(() => {
      setIsLoading(false);
      // TODO: Navigate to dashboard with demo data
      alert('Demo data loaded! Dashboard coming soon.');
    }, 4000);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-teal-700">
        <LoadingAnimation />
      </div>
    );
  }

  return (
    <div className="min-h-screen flex items-center justify-center bg-gradient-to-br from-slate-900 via-blue-900 to-teal-700 p-4">
      <div className="flex flex-col items-center text-center max-w-3xl">
        {/* Logo */}
        <div className="scale-125 mb-4">
          <Logo />
        </div>

        {/* Welcome Message */}
        <h1 className="text-5xl md:text-6xl lg:text-7xl font-bold text-white mb-12 leading-tight drop-shadow-2xl" style={{ textShadow: '0 0 40px rgba(94, 234, 212, 0.3)' }}>
          Let&apos;s take control of your finances, together.
        </h1>

        {/* Main CTA Button with pulsing animation */}
        <button
          onClick={handleConnectBank}
          className="relative group mb-6 w-full max-w-lg"
        >
          {/* Pulsing glow effect */}
          <div className="absolute -inset-2 bg-teal-400 rounded-full opacity-75 group-hover:opacity-100 blur-lg animate-pulse"></div>

          {/* Button content */}
          <div className="relative flex items-center justify-center gap-3 px-10 py-6 bg-teal-500 hover:bg-teal-600 rounded-full text-white font-bold text-2xl transition-colors shadow-2xl">
            Connect Your Bank Securely

            {/* Plaid badge */}
            <svg
              width="32"
              height="32"
              viewBox="0 0 24 24"
              fill="none"
              className="flex-shrink-0"
            >
              <rect width="24" height="24" rx="4" fill="white" />
              <path
                d="M12 6L6 9V15L12 18L18 15V9L12 6Z"
                fill="#000"
                opacity="0.8"
              />
            </svg>
          </div>
        </button>

        {/* Security micro-copy */}
        <p className="text-teal-100 text-base md:text-lg mb-10 flex items-center gap-3 flex-wrap justify-center">
          <span className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M5 9V7a5 5 0 0110 0v2a2 2 0 012 2v5a2 2 0 01-2 2H5a2 2 0 01-2-2v-5a2 2 0 012-2zm8-2v2H7V7a3 3 0 016 0z" clipRule="evenodd" />
            </svg>
            Read-only access
          </span>
          <span className="text-xl">•</span>
          <span className="flex items-center gap-2">
            <svg className="w-5 h-5" fill="currentColor" viewBox="0 0 20 20">
              <path fillRule="evenodd" d="M2.166 4.999A11.954 11.954 0 0010 1.944 11.954 11.954 0 0017.834 5c.11.65.166 1.32.166 2.001 0 5.225-3.34 9.67-8 11.317C5.34 16.67 2 12.225 2 7c0-.682.057-1.35.166-2.001zm11.541 3.708a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z" clipRule="evenodd" />
            </svg>
            Bank-level encryption
          </span>
          <span className="text-xl">•</span>
          <span>Disconnect anytime</span>
        </p>

        {/* Demo data link */}
        <button
          onClick={handleLoadDemo}
          className="text-teal-200 hover:text-white text-lg font-medium underline underline-offset-4 transition-colors hover:scale-105 transform"
        >
          Or load demo data
        </button>
      </div>
    </div>
  );
}
