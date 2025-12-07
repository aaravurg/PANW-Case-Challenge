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

interface GoalProgressChartProps {
  forecastPath: MonthlyProjection[];
  targetAmount: number;
  currentSavings: number;
  deadline: string;
  status: 'very_likely' | 'likely' | 'possible' | 'unlikely';
  goalName: string;
}

export default function GoalProgressChart({
  forecastPath,
  targetAmount,
  currentSavings,
  deadline,
  status,
  goalName
}: GoalProgressChartProps) {
  // Prepare data for chart
  const chartData = [
    {
      month: 'Now',
      cumulative: currentSavings,
      lower: currentSavings,
      upper: currentSavings,
      isActual: true
    },
    ...forecastPath.map(point => ({
      month: point.month,
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
      name: 'On Track'
    },
    likely: {
      area: '#22c55e20',
      line: '#22c55e',
      name: 'On Track'
    },
    possible: {
      area: '#f59e0b20',
      line: '#f59e0b',
      name: 'At Risk'
    },
    unlikely: {
      area: '#ef444420',
      line: '#ef4444',
      name: 'Off Track'
    }
  };

  const colors = colorScheme[status];

  // Format currency
  const formatCurrency = (value: number) => {
    if (value >= 1000) {
      return `$${(value / 1000).toFixed(1)}k`;
    }
    return `$${value.toFixed(0)}`;
  };

  // Custom tooltip
  const CustomTooltip = ({ active, payload, label }: any) => {
    if (active && payload && payload.length) {
      const data = payload[0].payload;
      return (
        <div className="bg-white p-3 border border-gray-200 rounded-lg shadow-lg">
          <p className="font-semibold text-sm mb-2">{label}</p>
          <div className="space-y-1 text-xs">
            <p className="text-green-600">
              Expected: <span className="font-semibold">${data.cumulative.toFixed(2)}</span>
            </p>
            <p className="text-gray-600">
              Optimistic: <span className="font-semibold">${data.upper.toFixed(2)}</span>
            </p>
            <p className="text-gray-600">
              Pessimistic: <span className="font-semibold">${data.lower.toFixed(2)}</span>
            </p>
          </div>
        </div>
      );
    }
    return null;
  };

  return (
    <div className="w-full h-full">
      <div className="mb-4">
        <h3 className="text-lg font-semibold text-gray-900">{goalName} - Projection</h3>
        <p className="text-sm text-gray-600">
          Forecast through {new Date(deadline).toLocaleDateString()}
        </p>
      </div>

      <ResponsiveContainer width="100%" height={400}>
        <AreaChart
          data={chartData}
          margin={{ top: 10, right: 30, left: 0, bottom: 0 }}
        >
          <defs>
            <linearGradient id="confidenceBand" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor={colors.line} stopOpacity={0.3} />
              <stop offset="95%" stopColor={colors.line} stopOpacity={0.05} />
            </linearGradient>
          </defs>

          <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />

          <XAxis
            dataKey="month"
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
          />

          <YAxis
            tickFormatter={formatCurrency}
            tick={{ fill: '#6b7280', fontSize: 12 }}
            tickLine={{ stroke: '#e5e7eb' }}
          />

          <Tooltip content={<CustomTooltip />} />

          {/* Goal target line */}
          <ReferenceLine
            y={targetAmount}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            strokeWidth={2}
            label={{
              value: `Goal: ${formatCurrency(targetAmount)}`,
              position: 'right',
              fill: '#6b7280',
              fontSize: 12
            }}
          />

          {/* Deadline vertical line */}
          <ReferenceLine
            x={new Date(deadline).toISOString().slice(0, 7)}
            stroke="#9ca3af"
            strokeDasharray="5 5"
            label={{
              value: 'Deadline',
              position: 'top',
              fill: '#6b7280',
              fontSize: 12
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
            dot={{ fill: colors.line, r: 4 }}
            activeDot={{ r: 6 }}
          />
        </AreaChart>
      </ResponsiveContainer>

      {/* Legend */}
      <div className="mt-4 flex items-center justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <div className={`w-3 h-3 rounded-full`} style={{ backgroundColor: colors.line }}></div>
          <span className="text-gray-700">Expected Path</span>
        </div>
        <div className="flex items-center gap-2">
          <div className="w-6 h-3 rounded" style={{ backgroundColor: colors.area }}></div>
          <span className="text-gray-700">Confidence Range (80%)</span>
        </div>
        <div className="flex items-center gap-2">
          <div className={`w-6 h-0.5 border-t-2 border-dashed border-gray-400`}></div>
          <span className="text-gray-700">Goal Target</span>
        </div>
      </div>
    </div>
  );
}
