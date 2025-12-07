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

      // Show all goals in the sidebar
      setGoals(sortedGoals);
    } catch (err) {
      console.error('Error loading goals:', err);
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
      {/* Financial Illustration */}
      <div className="mb-6">
        <div className="bg-gradient-to-br from-teal-500 to-cyan-600 rounded-2xl p-8 shadow-lg">
          <svg viewBox="0 0 200 140" fill="none" xmlns="http://www.w3.org/2000/svg" className="w-full h-auto">
            {/* Piggy Bank */}
            <ellipse cx="100" cy="110" rx="45" ry="8" fill="white" opacity="0.2"/>
            <ellipse cx="100" cy="80" rx="35" ry="30" fill="white" opacity="0.9"/>
            <circle cx="100" cy="75" r="28" fill="white"/>
            <circle cx="108" cy="72" r="3" fill="#0f766e"/>
            <path d="M85 75 Q80 70, 78 68" stroke="#0f766e" strokeWidth="2" strokeLinecap="round" fill="none"/>
            <ellipse cx="100" cy="95" rx="8" ry="6" fill="#fbbf24"/>
            <rect x="96" y="40" width="8" height="12" rx="4" fill="#fbbf24"/>

            {/* Coins */}
            <g opacity="0.9">
              <circle cx="50" cy="50" r="12" fill="#fbbf24"/>
              <circle cx="50" cy="50" r="10" fill="#fcd34d" stroke="#f59e0b" strokeWidth="1"/>
              <text x="50" y="54" fontSize="10" fill="#92400e" fontWeight="bold" textAnchor="middle">$</text>
            </g>

            <g opacity="0.9">
              <circle cx="150" cy="45" r="10" fill="#fbbf24"/>
              <circle cx="150" cy="45" r="8" fill="#fcd34d" stroke="#f59e0b" strokeWidth="1"/>
              <text x="150" y="48" fontSize="8" fill="#92400e" fontWeight="bold" textAnchor="middle">$</text>
            </g>

            <g opacity="0.9">
              <circle cx="140" cy="95" r="9" fill="#fbbf24"/>
              <circle cx="140" cy="95" r="7" fill="#fcd34d" stroke="#f59e0b" strokeWidth="1"/>
              <text x="140" y="98" fontSize="7" fill="#92400e" fontWeight="bold" textAnchor="middle">$</text>
            </g>

            {/* Growth Chart */}
            <g transform="translate(30, 10)">
              <path d="M0 30 L8 25 L16 28 L24 20 L32 15" stroke="#10b981" strokeWidth="3" strokeLinecap="round" fill="none"/>
              <circle cx="32" cy="15" r="3" fill="#10b981"/>
              <path d="M32 15 L36 10" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
              <path d="M32 15 L38 14" stroke="#10b981" strokeWidth="2" strokeLinecap="round"/>
            </g>
          </svg>
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

      <style jsx>{`
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
      `}</style>
    </aside>
  );
}
