'use client';

import { useState } from 'react';
import EnhancedSidebar from './EnhancedSidebar';
import TransactionPreview from './TransactionPreview';
import AIInsightsFeed from './AIInsightsFeed';
import RightColumnTools from './RightColumnTools';
import GoalDashboard from './GoalDashboard';
import NLCoach from './NLCoach';

export default function Dashboard() {
  const [showTransactions, setShowTransactions] = useState(false);
  const [showGoals, setShowGoals] = useState(false);
  const [showCoach, setShowCoach] = useState(false);

  return (
    <div className="min-h-screen bg-white flex">
      {/* Left Sidebar */}
      <EnhancedSidebar
        onViewTransactions={() => setShowTransactions(true)}
        onViewGoals={() => setShowGoals(true)}
      />

      {/* Main Content Area */}
      <main className="flex-1 flex">
        {/* Center Column - Insights & Activity */}
        <div className="flex-1 p-8 overflow-y-auto">
          <AIInsightsFeed />
        </div>

        {/* Right Panel - Tools & Simulations */}
        <RightColumnTools />
      </main>

      {/* Transaction Modal */}
      {showTransactions && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" onClick={() => setShowTransactions(false)}>
          <div className="bg-white rounded-3xl p-8 w-full max-w-7xl h-[90vh] shadow-2xl border border-gray-200 flex flex-col animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <div className="flex justify-between items-center mb-6 flex-shrink-0">
              <h2 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                All Transactions
              </h2>
              <button
                onClick={() => setShowTransactions(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex-1 overflow-y-auto">
              <TransactionPreview onContinue={() => setShowTransactions(false)} showContinueButton={false} />
            </div>
          </div>
        </div>
      )}

      {/* Goals Dashboard Modal */}
      {showGoals && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" onClick={() => setShowGoals(false)}>
          <div className="bg-gray-50 rounded-3xl w-full max-w-7xl h-[90vh] shadow-2xl border border-gray-200 flex flex-col animate-slide-up overflow-hidden" onClick={(e) => e.stopPropagation()}>
            <div className="bg-white px-8 py-6 border-b border-gray-200 flex-shrink-0">
              <div className="flex justify-between items-center">
                <h2 className="text-3xl font-bold text-gray-900" style={{ fontFamily: 'system-ui, -apple-system, sans-serif' }}>
                  Savings Goals Forecast
                </h2>
                <button
                  onClick={() => setShowGoals(false)}
                  className="text-gray-400 hover:text-gray-600 transition-colors"
                >
                  <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                  </svg>
                </button>
              </div>
            </div>
            <div className="flex-1 overflow-y-auto">
              <GoalDashboard />
            </div>
          </div>
        </div>
      )}

      {/* Natural Language Coach Modal */}
      {showCoach && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4 animate-fade-in" onClick={() => setShowCoach(false)}>
          <div className="w-full max-w-3xl h-[90vh] animate-slide-up" onClick={(e) => e.stopPropagation()}>
            <NLCoach onClose={() => setShowCoach(false)} />
          </div>
        </div>
      )}

      {/* Floating Chat Button */}
      <button
        onClick={() => setShowCoach(true)}
        className="fixed bottom-8 right-8 w-16 h-16 bg-blue-500 hover:bg-blue-600 text-white rounded-full shadow-2xl flex items-center justify-center transition-all hover:scale-110 z-40"
        aria-label="Open Financial Coach"
      >
        <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M8 10h.01M12 10h.01M16 10h.01M9 16H5a2 2 0 01-2-2V6a2 2 0 012-2h14a2 2 0 012 2v8a2 2 0 01-2 2h-5l-5 5v-5z" />
        </svg>
      </button>

      <style jsx>{`
        @keyframes fade-in {
          from { opacity: 0; }
          to { opacity: 1; }
        }

        @keyframes slide-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-fade-in {
          animation: fade-in 0.3s ease-out;
        }

        .animate-slide-up {
          animation: slide-up 0.4s ease-out;
        }
      `}</style>
    </div>
  );
}
