'use client';

import { useState, useEffect } from 'react';

interface Insight {
  id: string;
  type: 'win' | 'alert' | 'anomaly';
  emoji: string;
  headline: string;
  description: string;
  timestamp: string;
}

interface SpendingCategory {
  name: string;
  amount: number;
  color: string;
  icon: string;
}

const mockInsights: Insight[] = [
  {
    id: '1',
    type: 'win',
    emoji: '🎉',
    headline: 'Groceries spending down!',
    description: 'You spent 18% less on groceries this month compared to your average. That\'s $127 saved that could go toward your Emergency Fund goal.',
    timestamp: '2 hours ago',
  },
  {
    id: '2',
    type: 'alert',
    emoji: '📺',
    headline: 'Netflix subscription increased',
    description: 'Your Netflix subscription rate increased from $15.99 to $22.99 per month. This adds $84 to your annual entertainment expenses.',
    timestamp: '5 hours ago',
  },
  {
    id: '3',
    type: 'anomaly',
    emoji: '⚠️',
    headline: 'Unusual charge detected',
    description: 'We noticed an unusual $847 charge at United Airlines. This is 3.2x higher than your typical travel spending. Please verify this transaction.',
    timestamp: '1 day ago',
  },
  {
    id: '4',
    type: 'win',
    emoji: '💰',
    headline: 'Income increase detected',
    description: 'Your latest payroll deposit was $245 higher than usual. Consider allocating this extra $245 to your Vacation to Japan goal to reach it faster.',
    timestamp: '2 days ago',
  },
  {
    id: '5',
    type: 'alert',
    emoji: '🔔',
    headline: 'Mortgage payment due soon',
    description: 'Your $1,345 mortgage payment is scheduled for tomorrow. Make sure you have sufficient funds in your checking account.',
    timestamp: '2 days ago',
  },
  {
    id: '6',
    type: 'win',
    emoji: '📊',
    headline: 'Best saving month yet!',
    description: 'You saved $892 this month, which is your highest savings amount in the past 6 months. You\'re on track to exceed your annual savings goal.',
    timestamp: '3 days ago',
  },
];

const spendingCategories: SpendingCategory[] = [
  { name: 'Housing', amount: 1850, color: '#14b8a6', icon: '🏠' },
  { name: 'Transportation', amount: 650, color: '#06b6d4', icon: '🚗' },
  { name: 'Food & Dining', amount: 820, color: '#8b5cf6', icon: '🍔' },
  { name: 'Shopping', amount: 540, color: '#ec4899', icon: '🛍️' },
  { name: 'Entertainment', amount: 320, color: '#f59e0b', icon: '🎮' },
  { name: 'Healthcare', amount: 280, color: '#ef4444', icon: '⚕️' },
  { name: 'Other', amount: 410, color: '#6b7280', icon: '📦' },
];

export default function AIInsightsFeed() {
  const [insights, setInsights] = useState(mockInsights);
  const [dismissedIds, setDismissedIds] = useState<string[]>([]);
  const [visibleInsights, setVisibleInsights] = useState<string[]>([]);
  const [hoveredSegment, setHoveredSegment] = useState<string | null>(null);
  const [chartAnimated, setChartAnimated] = useState(false);

  // Staggered animation effect
  useEffect(() => {
    const timers = insights.map((insight, index) => {
      return setTimeout(() => {
        setVisibleInsights((prev) => [...prev, insight.id]);
      }, index * 100); // 100ms stagger
    });

    return () => timers.forEach(clearTimeout);
  }, [insights]);

  // Animate chart on load
  useEffect(() => {
    const timer = setTimeout(() => {
      setChartAnimated(true);
    }, 500);
    return () => clearTimeout(timer);
  }, []);

  // Get current time and greeting
  const getGreeting = () => {
    const hour = new Date().getHours();
    if (hour < 12) return 'Good morning';
    if (hour < 18) return 'Good afternoon';
    return 'Good evening';
  };

  // Get financial health status
  const getFinancialHealth = () => {
    // Mock logic - could be based on actual financial data
    const healthScore = 75; // 0-100
    if (healthScore >= 70) return { icon: '☀️', status: 'sunny', label: 'Healthy' };
    if (healthScore >= 40) return { icon: '⛅', status: 'partly-cloudy', label: 'Fair' };
    return { icon: '🌧️', status: 'stormy', label: 'Needs Attention' };
  };

  const handleDismiss = (id: string) => {
    setDismissedIds([...dismissedIds, id]);
    setTimeout(() => {
      setInsights(insights.filter((insight) => insight.id !== id));
    }, 300);
  };

  const getBorderColor = (type: string) => {
    switch (type) {
      case 'win':
        return 'border-l-green-500';
      case 'alert':
        return 'border-l-amber-500';
      case 'anomaly':
        return 'border-l-red-400';
      default:
        return 'border-l-gray-300';
    }
  };

  const health = getFinancialHealth();
  const today = new Date().toLocaleDateString('en-US', {
    weekday: 'long',
    month: 'long',
    day: 'numeric'
  });

  // Calculate donut chart segments
  const totalSpending = spendingCategories.reduce((sum, cat) => sum + cat.amount, 0);
  const radius = 110;
  const strokeWidth = 50;
  const center = 140;
  const circumference = 2 * Math.PI * radius;

  let currentAngle = -90; // Start at top
  const segments = spendingCategories.map((category) => {
    const percentage = (category.amount / totalSpending) * 100;
    const angle = (percentage / 100) * 360;
    const startAngle = currentAngle;
    const endAngle = currentAngle + angle;
    currentAngle = endAngle;

    return {
      ...category,
      percentage,
      startAngle,
      endAngle,
    };
  });

  return (
    <div className="max-w-5xl mx-auto">
      {/* Greeting Banner */}
      <div className="mb-8 bg-gradient-to-r from-teal-50 via-cyan-50 to-blue-50 rounded-2xl p-6 border border-teal-200/50">
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-3xl font-bold text-gray-900 mb-1">
              {getGreeting()}, Aarav. Here's your financial pulse.
            </h1>
            <p className="text-gray-600">{today}</p>
          </div>
          <div className="text-right">
            <div className="text-5xl mb-2">{health.icon}</div>
            <p className="text-sm font-medium text-gray-700">{health.label}</p>
          </div>
        </div>
      </div>

      {/* AI Insights Feed */}
      <div className="space-y-4">
        <h2 className="text-2xl font-bold text-gray-900 mb-4">AI Insights</h2>

        {insights.map((insight) => {
          const isVisible = visibleInsights.includes(insight.id);
          const isDismissed = dismissedIds.includes(insight.id);

          return (
            <div
              key={insight.id}
              className={`relative bg-white rounded-2xl p-6 border-l-4 ${getBorderColor(insight.type)} shadow-md hover:shadow-xl hover:-translate-y-1 transition-all duration-300 ${
                isVisible && !isDismissed ? 'animate-slide-in-up opacity-100' : 'opacity-0'
              } ${isDismissed ? 'animate-swipe-out' : ''}`}
            >
              {/* Dismiss Button */}
              <button
                onClick={() => handleDismiss(insight.id)}
                className="absolute top-4 right-4 text-gray-400 hover:text-gray-600 transition-colors"
                title="Dismiss"
              >
                <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M6 18L18 6M6 6l12 12" />
                </svg>
              </button>

              {/* Content */}
              <div className="flex gap-4">
                <div className="text-4xl flex-shrink-0">{insight.emoji}</div>
                <div className="flex-1 pr-8">
                  <h3 className="text-xl font-bold text-gray-900 mb-2">{insight.headline}</h3>
                  <p className="text-gray-700 leading-relaxed">
                    {insight.description.split(/(\$\d+(?:,\d{3})*(?:\.\d{2})?)/g).map((part, index) => {
                      if (part.match(/\$\d+(?:,\d{3})*(?:\.\d{2})?/)) {
                        return (
                          <span key={index} className="font-bold text-teal-600">
                            {part}
                          </span>
                        );
                      }
                      return part;
                    })}
                  </p>
                  <p className="text-sm text-gray-500 mt-3">{insight.timestamp}</p>
                </div>
              </div>

              {/* Action Buttons */}
              <div className="mt-4 flex gap-2">
                <button className="text-sm font-medium text-teal-600 hover:text-teal-700 transition-colors">
                  View Details
                </button>
                <span className="text-gray-300">•</span>
                <button className="text-sm font-medium text-gray-500 hover:text-gray-700 transition-colors">
                  Take Action
                </button>
              </div>
            </div>
          );
        })}

        {/* Spending Breakdown */}
        <div className="mt-12 bg-white rounded-2xl p-8 shadow-md border border-gray-200">
          <h2 className="text-2xl font-bold text-gray-900 mb-6">Spending Breakdown</h2>

          <div className="flex flex-col md:flex-row items-center gap-8">
            {/* Donut Chart */}
            <div className="relative flex-shrink-0">
              <svg width="280" height="280" viewBox="0 0 280 280" className="transform -rotate-90">
                {segments.map((segment, index) => {
                  const startAngle = (segment.startAngle * Math.PI) / 180;
                  const endAngle = (segment.endAngle * Math.PI) / 180;

                  const x1 = center + radius * Math.cos(startAngle);
                  const y1 = center + radius * Math.sin(startAngle);
                  const x2 = center + radius * Math.cos(endAngle);
                  const y2 = center + radius * Math.sin(endAngle);

                  const largeArc = segment.percentage > 50 ? 1 : 0;

                  const pathData = [
                    `M ${center} ${center}`,
                    `L ${x1} ${y1}`,
                    `A ${radius} ${radius} 0 ${largeArc} 1 ${x2} ${y2}`,
                    'Z'
                  ].join(' ');

                  const isHovered = hoveredSegment === segment.name;
                  const scale = isHovered ? 1.05 : 1;
                  const opacity = chartAnimated ? 1 : 0;

                  return (
                    <g key={segment.name}>
                      <path
                        d={pathData}
                        fill={segment.color}
                        opacity={opacity}
                        className="transition-all duration-300 cursor-pointer"
                        style={{
                          transform: isHovered ? `scale(${scale})` : 'scale(1)',
                          transformOrigin: '140px 140px',
                          transitionDelay: `${index * 50}ms`,
                        }}
                        onMouseEnter={() => setHoveredSegment(segment.name)}
                        onMouseLeave={() => setHoveredSegment(null)}
                      />
                    </g>
                  );
                })}

                {/* Center white circle for donut effect */}
                <circle
                  cx={center}
                  cy={center}
                  r={radius - strokeWidth}
                  fill="white"
                />
              </svg>

              {/* Center text */}
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <p className="text-base text-gray-600 mb-1">Total</p>
                <p className="text-3xl font-bold text-gray-900">
                  ${totalSpending.toLocaleString()}
                </p>
              </div>

              {/* Tooltip */}
              {hoveredSegment && (
                <div className="absolute top-1/2 left-1/2 transform -translate-x-1/2 -translate-y-1/2 bg-gray-900 text-white px-4 py-2 rounded-lg shadow-xl pointer-events-none z-10 animate-fade-in">
                  <p className="font-semibold whitespace-nowrap">
                    {segments.find(s => s.name === hoveredSegment)?.name}
                  </p>
                  <p className="text-sm">
                    ${segments.find(s => s.name === hoveredSegment)?.amount.toLocaleString()} ({segments.find(s => s.name === hoveredSegment)?.percentage.toFixed(1)}%)
                  </p>
                </div>
              )}
            </div>

            {/* Legend */}
            <div className="flex-1 grid grid-cols-1 md:grid-cols-2 gap-3">
              {segments.map((segment) => (
                <div
                  key={segment.name}
                  className={`flex items-center gap-3 p-3 rounded-xl border transition-all cursor-pointer ${
                    hoveredSegment === segment.name
                      ? 'bg-gray-50 border-gray-300 shadow-md'
                      : 'border-gray-200'
                  }`}
                  onMouseEnter={() => setHoveredSegment(segment.name)}
                  onMouseLeave={() => setHoveredSegment(null)}
                >
                  <div
                    className="w-4 h-4 rounded-full flex-shrink-0"
                    style={{ backgroundColor: segment.color }}
                  />
                  <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2">
                      <span className="text-lg">{segment.icon}</span>
                      <p className="font-semibold text-gray-900 text-sm truncate">{segment.name}</p>
                    </div>
                    <div className="flex items-center justify-between mt-1">
                      <p className="text-sm text-gray-600">${segment.amount.toLocaleString()}</p>
                      <p className="text-xs text-gray-500">{segment.percentage.toFixed(1)}%</p>
                    </div>
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </div>

      <style jsx>{`
        @keyframes slide-in-up {
          from {
            opacity: 0;
            transform: translateY(20px);
          }
          to {
            opacity: 1;
            transform: translateY(0);
          }
        }

        @keyframes swipe-out {
          to {
            opacity: 0;
            transform: translateX(100%);
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

        .animate-slide-in-up {
          animation: slide-in-up 0.5s ease-out forwards;
        }

        .animate-swipe-out {
          animation: swipe-out 0.3s ease-out forwards;
        }

        .animate-fade-in {
          animation: fade-in 0.2s ease-out;
        }
      `}</style>
    </div>
  );
}
