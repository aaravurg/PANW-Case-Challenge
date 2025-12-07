'use client';

import React from 'react';

interface Recommendation {
  action: string;
  category: string;
  monthly_savings: number;
  impact: string;
}

interface GapAnalysis {
  shortfall: number;
  monthly_gap: number;
  required_monthly_savings: number;
  current_monthly_savings: number;
}

interface GoalRecommendationsProps {
  recommendations: Recommendation[];
  gapAnalysis: GapAnalysis | null;
  onTrack: boolean;
}

export default function GoalRecommendations({
  recommendations,
  gapAnalysis,
  onTrack
}: GoalRecommendationsProps) {
  if (onTrack) {
    return (
      <div className="bg-green-50 border border-green-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-green-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-green-900 mb-1">
              You're on track!
            </h3>
            <p className="text-sm text-green-800">
              Based on your current savings rate, you're likely to reach this goal by the deadline. Keep up the great work!
            </p>
          </div>
        </div>
      </div>
    );
  }

  if (!gapAnalysis || !recommendations || recommendations.length === 0) {
    return (
      <div className="bg-yellow-50 border border-yellow-200 rounded-lg p-6">
        <div className="flex items-start gap-3">
          <div className="flex-shrink-0">
            <svg className="w-6 h-6 text-yellow-600" fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M12 9v2m0 4h.01m-6.938 4h13.856c1.54 0 2.502-1.667 1.732-3L13.732 4c-.77-1.333-2.694-1.333-3.464 0L3.34 16c-.77 1.333.192 3 1.732 3z" />
            </svg>
          </div>
          <div>
            <h3 className="text-lg font-semibold text-yellow-900 mb-1">
              You're off track
            </h3>
            <p className="text-sm text-yellow-800">
              Your current savings rate may not be enough to reach this goal. Consider increasing your savings or adjusting the target.
            </p>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Gap Analysis Summary */}
      <div className="bg-orange-50 border border-orange-200 rounded-lg p-4">
        <h3 className="text-lg font-semibold text-orange-900 mb-3">
          Spending Adjustments Needed
        </h3>

        <div className="grid grid-cols-2 gap-4 mb-4">
          <div>
            <p className="text-xs text-orange-700 mb-1">Total Shortfall</p>
            <p className="text-xl font-bold text-orange-900">
              ${gapAnalysis.shortfall.toLocaleString()}
            </p>
          </div>
          <div>
            <p className="text-xs text-orange-700 mb-1">Additional Savings Needed/Month</p>
            <p className="text-xl font-bold text-orange-900">
              ${gapAnalysis.monthly_gap.toLocaleString()}
            </p>
          </div>
        </div>

        <div className="bg-white rounded p-3 border border-orange-200">
          <div className="flex justify-between items-center text-sm">
            <span className="text-gray-600">Current monthly savings:</span>
            <span className="font-semibold text-gray-900">
              ${gapAnalysis.current_monthly_savings.toLocaleString()}
            </span>
          </div>
          <div className="flex justify-between items-center text-sm mt-1">
            <span className="text-gray-600">Required monthly savings:</span>
            <span className="font-semibold text-orange-900">
              ${gapAnalysis.required_monthly_savings.toLocaleString()}
            </span>
          </div>
        </div>
      </div>

      {/* Recommendations */}
      <div className="bg-white border border-gray-200 rounded-lg p-4">
        <h4 className="text-md font-semibold text-gray-900 mb-3">
          Recommended Actions
        </h4>

        <p className="text-sm text-gray-600 mb-4">
          Here are specific ways to close the gap and reach your goal:
        </p>

        <div className="space-y-3">
          {recommendations.map((rec, index) => (
            <div
              key={index}
              className="border border-gray-200 rounded-lg p-4 hover:border-blue-300 transition-colors"
            >
              <div className="flex items-start justify-between gap-4">
                <div className="flex-1">
                  <div className="flex items-center gap-2 mb-2">
                    <div className="flex-shrink-0 w-6 h-6 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-xs font-bold">
                      {index + 1}
                    </div>
                    <h5 className="font-semibold text-gray-900">{rec.action}</h5>
                  </div>

                  <div className="ml-8 space-y-1">
                    <p className="text-sm text-gray-600">
                      Category: <span className="font-medium">{rec.category}</span>
                    </p>
                    <p className="text-sm text-green-600 font-medium">
                      Saves ${rec.monthly_savings.toFixed(2)}/month
                    </p>
                    <p className="text-xs text-gray-500 italic">
                      {rec.impact}
                    </p>
                  </div>
                </div>

                <div className="flex-shrink-0">
                  <div className="bg-green-100 text-green-700 px-3 py-1 rounded-full text-sm font-semibold">
                    +${rec.monthly_savings.toFixed(0)}
                  </div>
                </div>
              </div>
            </div>
          ))}
        </div>

        <div className="mt-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
          <p className="text-sm text-blue-900">
            <span className="font-semibold">💡 Tip:</span> Start with the easiest changes first.
            Small adjustments can make a big difference over time!
          </p>
        </div>
      </div>
    </div>
  );
}
