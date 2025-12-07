'use client';

import React from 'react';
import {
  AreaChart,
  Area,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ReferenceLine,
  Line
} from 'recharts';

interface MonthlyProjection {
  month: string;
  cumulative: number;
  lower: number;
  upper: number;
}

interface GapAnalysis {
  shortfall: number;
  monthly_gap: number;
  required_monthly_savings: number;
  current_monthly_savings: number;
}

interface Projection {
  expected_monthly_savings: number;
  expected_total: number;
  optimistic_total: number;
  pessimistic_total: number;
}

interface CompetingGoal {
  goal_name: string;
  target_amount: number;
  deadline: string;
  required_monthly_savings: number;
  priority_level: string;
}

interface CompetitionAnalysis {
  total_available_savings: number;
  competing_goals: CompetingGoal[];
  total_committed_savings: number;
  remaining_available_savings: number;
  is_overcommitted: boolean;
  overcommitment_amount: number;
}

interface GoalProgressChartProps {
  forecastPath: MonthlyProjection[];
  targetAmount: number;
  currentSavings: number;
  deadline: string;
  status: 'very_likely' | 'likely' | 'possible' | 'unlikely';
  goalName: string;
  projection: Projection;
  gapAnalysis?: GapAnalysis | null;
  monthlyIncome: number;
  competitionAnalysis?: CompetitionAnalysis | null;
  currentGoalPriority?: string;
}

export default function GoalProgressChart({
  forecastPath,
  targetAmount,
  currentSavings,
  deadline,
  status,
  goalName,
  projection,
  gapAnalysis,
  monthlyIncome,
  competitionAnalysis,
  currentGoalPriority
}: GoalProgressChartProps) {
  // Format month for better readability
  const formatMonthLabel = (monthStr: string) => {
    if (monthStr === 'Now') return 'Now';
    const date = new Date(monthStr + '-01');
    return date.toLocaleDateString('en-US', { month: 'short', year: '2-digit' });
  };

  // Prepare data for chart
  const chartData = [
    {
      month: 'Now',
      displayMonth: 'Now',
      cumulative: currentSavings,
      lower: currentSavings,
      upper: currentSavings,
      isActual: true
    },
    ...forecastPath.map(point => ({
      month: point.month,
      displayMonth: formatMonthLabel(point.month),
      cumulative: point.cumulative,
      lower: point.lower,
      upper: point.upper,
      isActual: false
    }))
  ];

  // Color scheme based on status
  const colorScheme = {
    very_likely: {
      area: '#22c55e20',
      line: '#22c55e',
      name: 'On Track',
      emoji: '🎯',
      message: 'You\'re on pace to reach your goal!'
    },
    likely: {
      area: '#22c55e20',
      line: '#22c55e',
      name: 'On Track',
      emoji: '✅',
      message: 'Looking good! You\'re likely to hit your target.'
    },
    possible: {
      area: '#f59e0b20',
      line: '#f59e0b',
      name: 'At Risk',
      emoji: '⚠️',
      message: 'You might reach your goal, but it\'s tight.'
    },
    unlikely: {
      area: '#ef444420',
      line: '#ef4444',
      name: 'Off Track',
      emoji: '📉',
      message: 'At current pace, you won\'t reach your goal.'
    }
  };

  const colors = colorScheme[status];

  // Calculate end projection
  const finalProjection = chartData[chartData.length - 1];
  const gap = targetAmount - finalProjection.cumulative;
  const gapPercent = ((gap / targetAmount) * 100).toFixed(0);

  // Calculate spending breakdown
  // Step 1: Get actual average monthly spending from transaction history
  // When competition exists, total_available_savings = income - avg_spending_from_history
  // When no competition, expected_monthly_savings = income - avg_spending_from_history
  const totalAvailableSavings = competitionAnalysis
    ? competitionAnalysis.total_available_savings
    : projection.expected_monthly_savings;

  const avgMonthlySpending = monthlyIncome - totalAvailableSavings;

  const requiredMonthlySavings = gapAnalysis?.required_monthly_savings || 0;
  const requiredMonthlySpending = monthlyIncome - requiredMonthlySavings;

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  // Custom dot component - makes dots more visible and interactive
  const CustomDot = (props: any) => {
    const { cx, cy, payload } = props;

    return (
      <g>
        {/* Outer ring for better visibility */}
        <circle
          cx={cx}
          cy={cy}
          r={7}
          fill="white"
          stroke={colors.line}
          strokeWidth={2}
          style={{ cursor: 'pointer' }}
        />
        {/* Inner dot */}
        <circle
          cx={cx}
          cy={cy}
          r={4}
          fill={colors.line}
          style={{ cursor: 'pointer' }}
        />
      </g>
    );
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      const isNow = data.isActual;
      return (
        <div className="bg-white p-4 border-2 border-gray-300 rounded-lg shadow-xl max-w-xs">
          <p className="font-bold text-base mb-3 text-gray-900">
            {isNow ? '📍 Right Now' : `📅 ${data.displayMonth}`}
          </p>
          {isNow ? (
            <div className="space-y-2">
              <p className="text-sm text-gray-700">
                <span className="font-semibold">Current savings:</span>
              </p>
              <p className="text-2xl font-bold text-green-600">
                ${data.cumulative.toLocaleString()}
              </p>
            </div>
          ) : (
            <div className="space-y-2">
              <div className="bg-green-50 p-2 rounded">
                <p className="text-xs text-gray-600 mb-1">Most Likely</p>
                <p className="text-xl font-bold text-green-700">
                  ${data.cumulative.toLocaleString()}
                </p>
              </div>
              <div className="text-xs text-gray-600 space-y-1">
                <p>📈 Best case: <span className="font-semibold">${data.upper.toLocaleString()}</span></p>
                <p>📉 Worst case: <span className="font-semibold">${data.lower.toLocaleString()}</span></p>
              </div>
              <p className="text-xs text-gray-500 italic mt-2 pt-2 border-t border-gray-200">
                This shows where you'll be if you keep spending like you have been
              </p>
            </div>
          )}
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full">
      {/* Plain English Summary */}
      <div className="mb-6 p-4 rounded-lg" style={{ backgroundColor: colors.area }}>
        <div className="flex items-start gap-3">
          <span className="text-3xl">{colors.emoji}</span>
          <div className="flex-1">
            <h3 className="text-lg font-bold text-gray-900 mb-1">{goalName}</h3>
            <p className="text-sm font-medium text-gray-700 mb-2">{colors.message}</p>
            <div className="text-xs text-gray-600 space-y-1">
              <p>💰 Target: <span className="font-semibold">${targetAmount.toLocaleString()}</span> by {new Date(deadline).toLocaleDateString('en-US', { month: 'short', day: 'numeric', year: 'numeric' })}</p>
              <p>📊 Expected by deadline: <span className="font-semibold">${finalProjection.cumulative.toLocaleString()}</span></p>
              {gap > 0 ? (
                <p className="text-red-600">📉 Short by: <span className="font-semibold">${Math.abs(gap).toLocaleString()} ({gapPercent}%)</span></p>
              ) : (
                <p className="text-green-600">✨ Exceeding goal by: <span className="font-semibold">${Math.abs(gap).toLocaleString()}</span></p>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Transparency Section - Why This Happens */}
      <div className="mb-6 p-5 bg-gradient-to-r from-gray-50 to-gray-100 border-l-4 border-gray-400 rounded-lg">
        <h4 className="text-md font-bold text-gray-900 mb-3 flex items-center gap-2">
          <span>🔍</span>
          <span>Here's Why {status === 'very_likely' || status === 'likely' ? "You're On Track" : "You're Off Track"}</span>
        </h4>

        <div className="space-y-4">
          {/* Step-by-Step Calculation */}
          <div className="bg-white p-4 rounded-lg shadow-sm border-2 border-gray-300">
            <p className="text-sm font-bold text-gray-900 mb-4">💰 Step-by-Step: Your Available Money for THIS Goal</p>

            <div className="space-y-3 text-sm">
              {/* Step 1: Income */}
              <div className="flex justify-between items-center pb-2">
                <div>
                  <span className="font-semibold text-gray-900">Step 1:</span>
                  <span className="text-gray-700 ml-2">Your monthly income</span>
                </div>
                <span className="font-bold text-green-600 text-lg">${monthlyIncome.toLocaleString()}</span>
              </div>

              {/* Step 2: Spending */}
              <div className="flex justify-between items-center pb-2 border-t border-gray-200 pt-2">
                <div>
                  <span className="font-semibold text-gray-900">Step 2:</span>
                  <span className="text-gray-700 ml-2">Your average monthly spending</span>
                  <div className="text-xs text-gray-500 ml-16">(based on your transaction history)</div>
                </div>
                <span className="font-bold text-red-600 text-lg">-${avgMonthlySpending.toLocaleString()}</span>
              </div>

              {/* Subtotal */}
              <div className="flex justify-between items-center pb-2 bg-blue-50 p-2 rounded">
                <span className="font-semibold text-blue-900">= Money left over (before other goals)</span>
                <span className="font-bold text-blue-700 text-lg">${totalAvailableSavings.toLocaleString()}</span>
              </div>

              {/* Step 3: Higher Priority Goals (if any) */}
              {competitionAnalysis && competitionAnalysis.competing_goals.length > 0 && (
                <>
                  <div className="border-t-2 border-gray-400 pt-3 mt-2">
                    <div className="mb-2">
                      <span className="font-semibold text-gray-900">Step 3:</span>
                      <span className="text-gray-700 ml-2">Money committed to HIGHER priority goals</span>
                      <div className="text-xs text-gray-500 ml-16">(these goals get funded first based on priority)</div>
                    </div>

                    {/* List only higher priority goals */}
                    <div className="ml-16 space-y-1 mb-2">
                      {competitionAnalysis.competing_goals
                        .filter((g) => {
                          const priorityOrder: { [key: string]: number } = {"high": 0, "medium": 1, "low": 2};
                          const currentPriority = priorityOrder[currentGoalPriority?.toLowerCase() || "medium"];
                          const competingPriority = priorityOrder[g.priority_level.toLowerCase()];
                          return competingPriority < currentPriority;
                        })
                        .map((g, idx) => (
                          <div key={idx} className="flex justify-between text-xs text-red-700">
                            <span>• {g.goal_name} ({g.priority_level.toUpperCase()} priority)</span>
                            <span className="font-semibold">-${g.required_monthly_savings.toLocaleString()}/mo</span>
                          </div>
                        ))
                      }
                    </div>

                    <div className="flex justify-between items-center">
                      <span className="font-semibold text-gray-700 ml-16">Total committed:</span>
                      <span className="font-bold text-red-600 text-lg">-${competitionAnalysis.total_committed_savings.toLocaleString()}</span>
                    </div>
                  </div>

                  {/* Final Result - Calculate fresh to ensure accuracy */}
                  {(() => {
                    const actuallyAvailable = totalAvailableSavings - competitionAnalysis.total_committed_savings;
                    return (
                      <div className="flex justify-between items-center pb-2 bg-purple-100 border-2 border-purple-400 p-3 rounded">
                        <span className="font-bold text-purple-900">= Actually available for THIS goal</span>
                        <span className={`font-bold text-xl ${actuallyAvailable > 0 ? 'text-green-600' : 'text-red-600'}`}>
                          ${actuallyAvailable.toLocaleString()}/mo
                        </span>
                      </div>
                    );
                  })()}

                  {competitionAnalysis.is_overcommitted && (
                    <div className="mt-2 p-3 bg-red-50 border-l-4 border-red-500 text-sm text-red-800">
                      <p className="font-bold">⚠️ You don't have enough money for this goal!</p>
                      <p className="text-xs mt-1">Higher-priority goals already need more than you can save. You're short by ${competitionAnalysis.overcommitment_amount.toLocaleString()}/month.</p>
                    </div>
                  )}
                </>
              )}

              {/* If no competition, show simple result */}
              {(!competitionAnalysis || competitionAnalysis.competing_goals.length === 0) && (
                <div className="flex justify-between items-center pb-2 bg-green-100 border-2 border-green-400 p-3 rounded">
                  <span className="font-bold text-green-900">= Available for THIS goal</span>
                  <span className="font-bold text-green-700 text-xl">${totalAvailableSavings.toLocaleString()}/mo</span>
                </div>
              )}
            </div>
          </div>

          {/* What You Need (if off track) - ONLY if not explained above */}
          {gapAnalysis && gap > 0 && (
            <div className="bg-amber-50 border border-amber-200 p-4 rounded-lg">
              <p className="text-sm font-bold text-amber-900 mb-3">🎯 To Hit Your Goal by Deadline</p>
              <div className="space-y-2 text-sm">
                <div className="flex justify-between items-center">
                  <span className="text-amber-800">This goal needs per month:</span>
                  <span className="font-bold text-amber-900 text-lg">${requiredMonthlySavings.toLocaleString()}</span>
                </div>
                <div className="flex justify-between items-center">
                  <span className="text-amber-800">You currently have available:</span>
                  <span className={`font-bold ${competitionAnalysis ? 'text-purple-700' : 'text-blue-700'}`}>
                    ${competitionAnalysis ? competitionAnalysis.remaining_available_savings.toLocaleString() : totalAvailableSavings.toLocaleString()}
                  </span>
                </div>
                <div className="border-t border-amber-300 pt-2 mt-2"></div>
                <div className="flex justify-between items-center">
                  <span className="text-amber-900 font-semibold">Gap:</span>
                  <span className="font-bold text-lg text-red-600">
                    ${(requiredMonthlySavings - (competitionAnalysis ? competitionAnalysis.remaining_available_savings : totalAvailableSavings)).toLocaleString()}/mo short
                  </span>
                </div>
              </div>
            </div>
          )}
        </div>
      </div>

      {/* Chart Title */}
      <div className="mb-3">
        <h4 className="text-md font-semibold text-gray-800">How Your Savings Will Grow</h4>
        <p className="text-xs text-gray-500">Based on your current spending patterns</p>
      </div>

      <ResponsiveContainer width="100%" height={420}>
        <AreaChart
          data={chartData}
          margin={{ top: 20, right: 60, left: 10, bottom: 20 }}
        >
          <defs>
            <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.line} stopOpacity={0.3} />
              <stop offset="95%" stopColor={colors.line} stopOpacity={0.05} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="displayMonth"
            tick={{ fill: '#6b7280', fontSize: 11 }}
            tickLine={{ stroke: '#e5e7eb' }}
            height={50}
          />

          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: '#6b7280', fontSize: 11 }}
            tickLine={{ stroke: '#e5e7eb' }}
            width={60}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Goal target line */}
          <ReferenceLine
            y={targetAmount}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            strokeWidth={2}
            label={{
              value: `🎯 ${formatCurrency(targetAmount)} Goal`,
              position: 'right',
              fill: '#374151',
              fontSize: 11,
              fontWeight: 'bold'
            }}
          />

          {/* Deadline vertical line */}
          <ReferenceLine
            x={formatMonthLabel(new Date(deadline).toISOString().slice(0, 7))}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{
              value: '⏰ Deadline',
              position: 'top',
              fill: '#374151',
              fontSize: 11,
              fontWeight: 'bold'
            }}
          />

          {/* Confidence band (area between upper and lower bounds) */}
          <Area
            type="monotone"
            dataKey="upper"
            stackId="1"
            stroke="none"
            fill="url(#confidenceBand)"
          />
          <Area
            type="monotone"
            dataKey="lower"
            stackId="1"
            stroke="none"
            fill="white"
          />

          {/* Expected path line */}
          <Line
            type="monotone"
            dataKey="cumulative"
            stroke={colors.line}
            strokeWidth={3}
            dot={<CustomDot />}
            activeDot={{ r: 8, strokeWidth: 3, fill: colors.line, stroke: 'white' }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Legend - User Friendly */}
      <div className="mt-6 space-y-4">
        <div className="grid grid-cols-1 md:grid-cols-3 gap-3 text-sm">
          <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <div className={`w-4 h-4 rounded-full mt-0.5 flex-shrink-0`} style={{ backgroundColor: colors.line }}></div>
            <div>
              <p className="font-semibold text-gray-900">Dots on Line</p>
              <p className="text-xs text-gray-600">Hover to see exact amounts</p>
            </div>
          </div>
          <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <div className="w-4 h-4 rounded mt-0.5 flex-shrink-0" style={{ backgroundColor: colors.area }}></div>
            <div>
              <p className="font-semibold text-gray-900">Shaded Area</p>
              <p className="text-xs text-gray-600">Range of possible outcomes</p>
            </div>
          </div>
          <div className="flex items-start gap-2 p-3 bg-gray-50 rounded-lg">
            <div className={`w-6 h-0.5 border-t-2 border-dashed border-gray-400 mt-2 flex-shrink-0`}></div>
            <div>
              <p className="font-semibold text-gray-900">Dashed Lines</p>
              <p className="text-xs text-gray-600">Your goal & deadline</p>
            </div>
          </div>
        </div>

        {/* What This Means Section */}
        <div className="p-4 bg-blue-50 border border-blue-200 rounded-lg">
          <h5 className="font-semibold text-sm text-blue-900 mb-2">💡 How to Read This Chart</h5>
          <ul className="text-xs text-blue-800 space-y-1.5">
            <li>• <strong>The line going up?</strong> That's good! You're saving money over time.</li>
            <li>• <strong>The shaded area</strong> shows best-case and worst-case scenarios based on your spending patterns.</li>
            <li>• <strong>Goal is to cross the dashed line</strong> (your target) before the deadline.</li>
            <li>• <strong>👆 Hover over the dots</strong> to see exactly how much you'll have saved by that month (with best/worst case scenarios).</li>
          </ul>
        </div>
      </div>
    </div>
  );
}
