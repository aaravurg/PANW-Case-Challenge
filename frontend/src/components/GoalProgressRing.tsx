'use client';

import React from 'react';

interface GoalProgressRingProps {
  currentSavings: number;
  targetAmount: number;
  status: 'very_likely' | 'likely' | 'possible' | 'unlikely';
  size?: number;
  strokeWidth?: number;
}

export default function GoalProgressRing({
  currentSavings,
  targetAmount,
  status,
  size = 200,
  strokeWidth = 16
}: GoalProgressRingProps) {
  // Calculate progress percentage
  const progressPercent = Math.min((currentSavings / targetAmount) * 100, 100);

  // Circle calculations
  const radius = (size - strokeWidth) / 2;
  const circumference = 2 * Math.PI * radius;
  const strokeDashoffset = circumference - (progressPercent / 100) * circumference;

  // Color scheme based on status
  const colorScheme = {
    very_likely: {
      solid: '#22c55e',
      gradient: '#16a34a',
      background: '#22c55e20'
    },
    likely: {
      solid: '#22c55e',
      gradient: '#16a34a',
      background: '#22c55e20'
    },
    possible: {
      solid: '#f59e0b',
      gradient: '#d97706',
      background: '#f59e0b20'
    },
    unlikely: {
      solid: '#ef4444',
      gradient: '#dc2626',
      background: '#ef444420'
    }
  };

  const colors = colorScheme[status];

  return (
    <div className="flex flex-col items-center justify-center">
      <div className="relative" style={{ width: size, height: size }}>
        <svg
          width={size}
          height={size}
          className="transform -rotate-90"
        >
          {/* Background circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colors.background}
            strokeWidth={strokeWidth}
          />

          {/* Progress circle */}
          <circle
            cx={size / 2}
            cy={size / 2}
            r={radius}
            fill="none"
            stroke={colors.solid}
            strokeWidth={strokeWidth}
            strokeDasharray={circumference}
            strokeDashoffset={strokeDashoffset}
            strokeLinecap="round"
            className="transition-all duration-1000 ease-out"
            style={{
              filter: 'drop-shadow(0 0 8px rgba(0, 0, 0, 0.1))'
            }}
          />
        </svg>

        {/* Center text */}
        <div className="absolute inset-0 flex flex-col items-center justify-center">
          <div className="text-3xl font-bold text-gray-900">
            {progressPercent.toFixed(0)}%
          </div>
          <div className="text-sm text-gray-600 mt-1">
            ${currentSavings.toLocaleString()}
          </div>
          <div className="text-xs text-gray-500">
            of ${targetAmount.toLocaleString()}
          </div>
        </div>
      </div>

      {/* Status indicator */}
      <div className="mt-4">
        <div
          className="px-4 py-2 rounded-full text-sm font-medium"
          style={{
            backgroundColor: colors.background,
            color: colors.solid
          }}
        >
          {status === 'very_likely' && '90%+ Chance'}
          {status === 'likely' && '60-80% Chance'}
          {status === 'possible' && '30-50% Chance'}
          {status === 'unlikely' && '<30% Chance'}
        </div>
      </div>
    </div>
  );
}
