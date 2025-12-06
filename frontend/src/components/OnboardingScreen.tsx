'use client';

import { useState } from 'react';
import Logo from './Logo';
import BankLogin from './BankLogin';
import TransactionPreview from './TransactionPreview';

const banks = [
  { id: 'chase', name: 'Chase', logo: '🏦' },
  { id: 'boa', name: 'Bank of America', logo: '🏛️' },
  { id: 'wells', name: 'Wells Fargo', logo: '🏦' },
  { id: 'capital', name: 'Capital One', logo: '💳' },
  { id: 'citi', name: 'Citi', logo: '🏢' },
  { id: 'usbank', name: 'U.S. Bank', logo: '🏦' },
  { id: 'pnc', name: 'PNC Bank', logo: '🏛️' },
  { id: 'td', name: 'TD Bank', logo: '🏦' },
  { id: 'schwab', name: 'Charles Schwab', logo: '📊' },
  { id: 'ally', name: 'Ally Bank', logo: '💰' },
];

type ModalStep = 'bank-selection' | 'bank-login' | 'transitioning' | 'transaction-preview';

interface OnboardingScreenProps {
  onComplete: () => void;
}

export default function OnboardingScreen({ onComplete }: OnboardingScreenProps) {
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedBank, setSelectedBank] = useState<string | null>(null);
  const [modalStep, setModalStep] = useState<ModalStep>('bank-selection');

  const filteredBanks = banks.filter(bank =>
    bank.name.toLowerCase().includes(searchQuery.toLowerCase())
  );

  const handleBankSelect = (bankId: string) => {
    setSelectedBank(bankId);
    setModalStep('transitioning');
    // Transition to login screen
    setTimeout(() => {
      setModalStep('bank-login');
    }, 1000);
  };

  const handleLoginComplete = () => {
    // Transition to transaction preview
    setModalStep('transaction-preview');
  };

  const handleContinueToDashboard = () => {
    // Handle completion - navigate to dashboard
    setIsModalOpen(false);
    // Small delay for smooth transition
    setTimeout(() => {
      onComplete();
    }, 300);
  };

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

        {/* Connect Button */}
        <button
          onClick={() => setIsModalOpen(true)}
          className="group relative bg-gradient-to-r from-teal-500 to-cyan-500 text-white px-8 py-4 rounded-full font-semibold text-lg shadow-2xl hover:shadow-teal-500/50 transition-all duration-300 hover:scale-105 animate-pulse-glow"
        >
          <div className="flex items-center gap-3">
            {/* Lock Icon */}
            <svg
              className="w-6 h-6"
              fill="none"
              stroke="currentColor"
              viewBox="0 0 24 24"
            >
              <path
                strokeLinecap="round"
                strokeLinejoin="round"
                strokeWidth={2}
                d="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
              />
            </svg>
            <span>Connect Your Bank Securely</span>
          </div>
        </button>

        {/* Security Micro-copy */}
        <p className="mt-4 text-sm text-teal-200/80 flex items-center gap-2">
          <span>Read-only access</span>
          <span className="text-teal-300">•</span>
          <span>Bank-level encryption</span>
          <span className="text-teal-300">•</span>
          <span>Your data stays private</span>
        </p>
      </div>

      {/* Modal */}
      {isModalOpen && (
        <div
          className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-end sm:items-center justify-center p-4 animate-fade-in"
          onClick={() => modalStep === 'bank-selection' && setIsModalOpen(false)}
        >
          <div
            className={`bg-white/10 backdrop-blur-xl rounded-t-3xl sm:rounded-3xl p-6 w-full shadow-2xl border border-white/20 transition-all duration-500 ${
              modalStep === 'transitioning' ? 'animate-bank-selected' : 'animate-slide-up'
            } ${modalStep === 'bank-login' || modalStep === 'transaction-preview' ? 'relative' : ''} ${
              modalStep === 'transaction-preview' ? 'max-w-6xl' : 'max-w-2xl'
            }`}
            onClick={(e) => e.stopPropagation()}
          >
            {modalStep === 'bank-selection' ? (
              <>
                {/* Modal Header */}
                <div className="flex justify-between items-center mb-6">
                  <h2 className="text-2xl font-bold text-white">Select Your Bank</h2>
                  <button
                    onClick={() => setIsModalOpen(false)}
                    className="text-white/60 hover:text-white transition-colors"
                  >
                    <svg className="w-6 h-6" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>

                {/* Search Input */}
                <div className="mb-4">
                  <input
                    type="text"
                    placeholder="Search for your bank..."
                    value={searchQuery}
                    onChange={(e) => setSearchQuery(e.target.value)}
                    className="w-full px-4 py-3 rounded-xl bg-white/10 border border-white/20 text-white placeholder-white/50 focus:outline-none focus:ring-2 focus:ring-teal-400 transition-all"
                  />
                </div>

                {/* Bank List */}
                <div className="max-h-96 overflow-y-auto space-y-2 pr-2 custom-scrollbar">
                  {filteredBanks.map((bank) => (
                    <button
                      key={bank.id}
                      onClick={() => handleBankSelect(bank.id)}
                      className="w-full flex items-center gap-4 p-4 rounded-xl bg-white/5 hover:bg-white/15 border border-white/10 hover:border-white/30 transition-all duration-200 group"
                    >
                      <div className="text-4xl">{bank.logo}</div>
                      <span className="text-white text-lg font-medium group-hover:translate-x-1 transition-transform">
                        {bank.name}
                      </span>
                    </button>
                  ))}
                  {filteredBanks.length === 0 && (
                    <p className="text-white/50 text-center py-8">No banks found</p>
                  )}
                </div>
              </>
            ) : modalStep === 'transitioning' ? (
              /* Bank Selected Animation */
              <div className="flex items-center justify-center py-16">
                <div className="text-8xl animate-grow">
                  {banks.find(b => b.id === selectedBank)?.logo}
                </div>
              </div>
            ) : modalStep === 'bank-login' ? (
              /* Bank Login Screen */
              <BankLogin
                bankName={banks.find(b => b.id === selectedBank)?.name || ''}
                bankLogo={banks.find(b => b.id === selectedBank)?.logo || ''}
                onComplete={handleLoginComplete}
              />
            ) : (
              /* Transaction Preview Screen */
              <TransactionPreview onContinue={handleContinueToDashboard} />
            )}
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes pulse-glow {
          0%, 100% {
            box-shadow: 0 0 20px rgba(20, 184, 166, 0.5);
          }
          50% {
            box-shadow: 0 0 40px rgba(20, 184, 166, 0.8);
          }
        }

        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(100%);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes fade-in {
          from {
            opacity: 0;
          }
          to {
            opacity: 1;
          }
        }

        @keyframes grow {
          0% {
            transform: scale(0.5);
            opacity: 0;
          }
          50% {
            transform: scale(1.2);
          }
          100% {
            transform: scale(1);
            opacity: 1;
          }
        }

        @keyframes bank-selected {
          from {
            transform: scale(1);
          }
          to {
            transform: scale(0.95);
            opacity: 0.8;
          }
        }

        .animate-pulse-glow {
          animation: pulse-glow 2s ease-in-out infinite;
        }

        .animate-slide-up {
          animation: slide-up 0.5s ease-out;
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-grow {
          animation: grow 0.8s ease-out;
        }

        .animate-bank-selected {
          animation: bank-selected 0.5s ease-out forwards;
        }

        .custom-scrollbar::-webkit-scrollbar {
          width: 8px;
        }

        .custom-scrollbar::-webkit-scrollbar-track {
          background: rgba(255, 255, 255, 0.05);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb {
          background: rgba(255, 255, 255, 0.2);
          border-radius: 4px;
        }

        .custom-scrollbar::-webkit-scrollbar-thumb:hover {
          background: rgba(255, 255, 255, 0.3);
        }
      `}</style>
    </div>
  );
}
