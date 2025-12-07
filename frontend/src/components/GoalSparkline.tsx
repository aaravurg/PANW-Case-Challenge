'use client';

import React from 'react';
import { BarChart, Bar, ResponsiveContainer, Cell } from 'recharts';

interface MonthlyData {
  month: string;
  amount: number;
}

interface GoalSparklineProps {
  monthlyData: MonthlyData[];
  height?: number;
}

export default function GoalSparkline({ monthlyData, height = 60 }: GoalSparklineProps) {
  if (!monthlyData || monthlyData.length === 0) {
    return (
      <div className="flex items-center justify-center h-16 text-sm text-gray-500">
        No historical data available
      </div>
    );
  }

  // Calculate average for comparison
  const average = monthlyData.reduce((sum, d) => sum + d.amount, 0) / monthlyData.length;

  return (
    <div className="w-full">
      <div className="flex items-center justify-between mb-2">
        <h4 className="text-sm font-medium text-gray-700">Historical Monthly Savings</h4>
        <span className="text-xs text-gray-500">
          Avg: ${average.toFixed(0)}/mo
        </span>
      </div>

      <ResponsiveContainer width="100%" height={height}>
        <BarChart data={monthlyData}>
          <Bar dataKey="amount" radius={[4, 4, 0, 0]}>
            {monthlyData.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.amount >= average ? '#22c55e' : '#94a3b8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>

      <div className="flex items-center justify-between mt-2 text-xs text-gray-500">
        <span>{monthlyData[0]?.month}</span>
        <span>{monthlyData[monthlyData.length - 1]?.month}</span>
      </div>
    </div>
  );
}
