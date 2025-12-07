'use client';

import { useState, useEffect } from 'react';

interface EnhancedSidebarProps {
  onViewTransactions: () => void;
  onViewGoals?: () => void;
}

interface Goal {
  id: string;
  goal_name: string;
  target_amount: number;
  deadline: string;
  current_savings: number;
  priority_level: string;
  created_at: string;
  monthly_income: number;
  income_type: string;
}

export default function EnhancedSidebar({ onViewTransactions, onViewGoals }: EnhancedSidebarProps) {
  const [showDNAAnalysis, setShowDNAAnalysis] = useState(false);
  const [showImpulseAnalysis, setShowImpulseAnalysis] = useState(false);
  const [impulsePrice, setImpulsePrice] = useState('');
  const [laborHours, setLaborHours] = useState(0);
  const [animatedHours, setAnimatedHours] = useState(0);

  const [goals, setGoals] = useState<Goal[]>([]);
  const API_BASE_URL = 'http://localhost:8000';

  // Load goals from API
  useEffect(() => {
    loadGoals();

    // Refresh goals every 5 seconds to pick up new goals created in the dashboard
    const interval = setInterval(loadGoals, 5000);
    return () => clearInterval(interval);
  }, []);

  const loadGoals = async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/goals`);
      if (!response.ok) {
        throw new Error('Failed to load goals');
      }
      const data = await response.json();

      // Sort goals by deadline (closest first)
      const sortedGoals = data.sort((a: Goal, b: Goal) => {
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      });

      // Take only the first 2 goals for the sidebar
      setGoals(sortedGoals.slice(0, 2));
    } catch (err) {
      console.error('Error loading goals:', err);
    }
  };

  const hourlyWage = 25; // Mock hourly wage

  // Counting animation for labor hours
  useEffect(() => {
    if (laborHours > 0) {
      const duration = 500;
      const steps = 30;
      const increment = laborHours / steps;
      let current = 0;
      let step = 0;

      const timer = setInterval(() => {
        step++;
        current = Math.min(current + increment, laborHours);
        setAnimatedHours(current);

        if (step >= steps) {
          clearInterval(timer);
          setAnimatedHours(laborHours);
        }
      }, duration / steps);

      return () => clearInterval(timer);
    }
  }, [laborHours]);

  const handleImpulseChange = (value: string) => {
    setImpulsePrice(value);
    const price = parseFloat(value);
    if (!isNaN(price) && price > 0) {
      setLaborHours(price / hourlyWage);
    } else {
      setLaborHours(0);
      setAnimatedHours(0);
    }
  };

  const getProgressColor = (progress: number) => {
    if (progress >= 80) return 'stroke-green-500';
    if (progress >= 50) return 'stroke-teal-500';
    return 'stroke-amber-500';
  };

  const getStatusBadge = (progress: number) => {
    if (progress >= 70) return { text: 'On Track', color: 'bg-green-500' };
    return { text: 'Needs Attention', color: 'bg-amber-500' };
  };

  return (
    <aside className="w-80 bg-gradient-to-b from-gray-50 to-white border-r border-gray-200 p-6 overflow-y-auto">
      {/* Financial DNA Card */}
      <div className="mb-6">
        <div className="mb-2">
          <h3 className="text-sm font-semibold text-gray-600 text-center">Financial DNA</h3>
        </div>
        <div
          className="cursor-pointer transition-transform hover:scale-[1.02] active:scale-[0.98]"
          onClick={() => setShowDNAAnalysis(true)}
        >
          <div className="h-48 bg-gradient-to-br from-purple-500 via-pink-500 to-teal-500 rounded-2xl p-6 text-white shadow-xl animate-gradient-shift border-2 border-white/30">
            <div className="flex flex-col items-center justify-center h-full text-center">
              <div className="text-6xl mb-3">🎯</div>
              <h3 className="text-xl font-bold mb-1">The Weekend Warrior</h3>
              <p className="text-sm text-white/80">Your Financial DNA</p>
              <p className="text-xs text-white/60 mt-2">Click to view full analysis</p>
            </div>
          </div>
        </div>
      </div>

      {/* Goal Tracker */}
      <div className="mb-6">
        <div className="flex items-center justify-between mb-4">
          <h3 className="text-lg font-bold text-gray-900">Goal Tracker</h3>
          <div className="flex items-center gap-2">
            <button
              onClick={onViewGoals}
              className="text-teal-600 hover:text-teal-700 transition-colors"
              title="View Goals Dashboard"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
              </svg>
            </button>
            <button
              onClick={onViewGoals}
              className="text-teal-600 hover:text-teal-700 transition-colors"
              title="Add new goal"
            >
              <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 4v16m8-8H4" />
              </svg>
            </button>
          </div>
        </div>

        <div className="space-y-4">
          {goals.length === 0 ? (
            <div className="bg-white rounded-xl p-6 border border-gray-200 shadow-sm text-center">
              <p className="text-gray-500 text-sm mb-3">No goals yet</p>
              <button
                onClick={onViewGoals}
                className="text-teal-600 hover:text-teal-700 font-medium text-sm"
              >
                Create your first goal
              </button>
            </div>
          ) : (
            goals.map((goal, index) => {
              const progress = (goal.current_savings / goal.target_amount) * 100;
              const status = getStatusBadge(progress);
              const radius = 45;
              const circumference = 2 * Math.PI * radius;
              const offset = circumference - (progress / 100) * circumference;

              // Calculate days until deadline
              const today = new Date();
              const deadline = new Date(goal.deadline);
              const daysUntil = Math.ceil((deadline.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

              return (
                <div key={goal.id} className="bg-white rounded-xl p-4 border border-gray-200 shadow-sm hover:shadow-md transition-shadow">
                  <div className="flex items-center gap-4">
                    {/* Progress Ring */}
                    <div className="relative w-24 h-24 flex-shrink-0">
                      <svg className="transform -rotate-90 w-24 h-24">
                        <circle
                          cx="48"
                          cy="48"
                          r={radius}
                          stroke="currentColor"
                          strokeWidth="6"
                          fill="none"
                          className="text-gray-200"
                        />
                        <circle
                          cx="48"
                          cy="48"
                          r={radius}
                          stroke="currentColor"
                          strokeWidth="6"
                          fill="none"
                          strokeDasharray={circumference}
                          strokeDashoffset={offset}
                          className={`${getProgressColor(progress)} transition-all duration-1000 ease-out`}
                          strokeLinecap="round"
                        />
                      </svg>
                      <div className="absolute inset-0 flex items-center justify-center">
                        <span className="text-lg font-bold text-gray-900">{Math.round(progress)}%</span>
                      </div>
                    </div>

                    {/* Goal Info */}
                    <div className="flex-1 min-w-0">
                      <div className="flex items-start justify-between mb-1">
                        <h4 className="font-semibold text-gray-900 truncate">{goal.goal_name}</h4>
                        {index === 0 && (
                          <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded whitespace-nowrap">
                            Next
                          </span>
                        )}
                      </div>
                      <p className="text-sm text-gray-600">
                        ${goal.current_savings.toLocaleString()} / ${goal.target_amount.toLocaleString()}
                      </p>
                      <p className="text-xs text-gray-500 mt-1">
                        {daysUntil > 0 ? (
                          <span className={daysUntil < 30 ? 'text-red-600 font-medium' : daysUntil < 90 ? 'text-orange-600 font-medium' : ''}>
                            {daysUntil} day{daysUntil !== 1 ? 's' : ''} left
                          </span>
                        ) : (
                          <span className="text-red-600 font-medium">Deadline passed</span>
                        )}
                      </p>
                      <div className={`inline-flex items-center gap-1 mt-2 px-2 py-1 rounded-full text-xs font-medium text-white ${status.color} animate-pulse-subtle`}>
                        <span className="w-1.5 h-1.5 bg-white rounded-full"></span>
                        {status.text}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Impulse Interceptor */}
      <div className="bg-gradient-to-br from-teal-50 to-cyan-50 rounded-xl p-4 border border-teal-200">
        <div className="flex items-center justify-between mb-3">
          <h3 className="text-sm font-bold text-gray-900">💡 Impulse Interceptor</h3>
          <button
            onClick={() => setShowImpulseAnalysis(true)}
            className="text-teal-600 hover:text-teal-700 transition-colors"
            title="Expand analysis"
          >
            <svg className="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M4 8V4m0 0h4M4 4l5 5m11-1V4m0 0h-4m4 0l-5 5M4 16v4m0 0h4m-4 0l5-5m11 5l-5-5m5 5v-4m0 4h-4" />
            </svg>
          </button>
        </div>
        <input
          type="number"
          value={impulsePrice}
          onChange={(e) => handleImpulseChange(e.target.value)}
          placeholder="Enter a price..."
          className="w-full px-3 py-2 rounded-lg border border-teal-300 focus:outline-none focus:ring-2 focus:ring-teal-400 bg-white text-sm mb-2"
        />
        {laborHours > 0 && (
          <div className="bg-white rounded-lg p-3 border border-teal-200 animate-slide-down">
            <p className="text-xs text-gray-600 mb-1">That's equivalent to:</p>
            <p className="text-2xl font-bold text-teal-600">
              {animatedHours.toFixed(1)} <span className="text-sm font-normal">hours</span>
            </p>
            <p className="text-xs text-gray-500 mt-1">of your labor time</p>
          </div>
        )}
      </div>

      {/* Navigation */}
      <div className="mt-6 pt-6 border-t border-gray-200">
        <button
          onClick={onViewTransactions}
          className="w-full flex items-center gap-3 px-4 py-3 rounded-lg bg-teal-500 text-white hover:bg-teal-600 transition-colors font-medium text-sm"
        >
          <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2" />
          </svg>
          View All Transactions
        </button>
      </div>

      {/* DNA Analysis Modal */}
      {showDNAAnalysis && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 w-full max-w-6xl h-[85vh] shadow-2xl animate-slide-up overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-900">Financial DNA Analysis</h2>
              <button
                onClick={() => setShowDNAAnalysis(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex items-center justify-center h-[60vh] text-gray-400">
              <p className="text-xl">Analysis content will go here...</p>
            </div>
          </div>
        </div>
      )}

      {/* Impulse Analysis Modal */}
      {showImpulseAnalysis && (
        <div className="fixed inset-0 bg-black/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <div className="bg-white rounded-3xl p-8 w-full max-w-6xl h-[85vh] shadow-2xl animate-slide-up overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h2 className="text-3xl font-bold text-gray-900">Impulse Interceptor Analysis</h2>
              <button
                onClick={() => setShowImpulseAnalysis(false)}
                className="text-gray-400 hover:text-gray-600 transition-colors"
              >
                <svg className="w-8 h-8" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>
            </div>
            <div className="flex items-center justify-center h-[60vh] text-gray-400">
              <p className="text-xl">Impulse analysis content will go here...</p>
            </div>
          </div>
        </div>
      )}

      <style jsx>{`
        @keyframes gradient-shift {
          0%, 100% {
            background-position: 0% 50%;
          }
          50% {
            background-position: 100% 50%;
          }
        }

        .animate-gradient-shift {
          background-size: 200% 200%;
          animation: gradient-shift 8s ease infinite;
        }

        @keyframes pulse-subtle {
          0%, 100% {
            opacity: 1;
          }
          50% {
            opacity: 0.8;
          }
        }

        .animate-pulse-subtle {
          animation: pulse-subtle 2s ease-in-out infinite;
        }

        @keyframes slide-down {
          from {
            opacity: 0;
            transform: translateY(-10px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        .animate-slide-down {
          animation: slide-down 0.3s ease-out;
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

        .animate-slide-up {
          animation: slide-up 0.4s ease-out;
        }
      `}</style>
    </aside>
  );
}
