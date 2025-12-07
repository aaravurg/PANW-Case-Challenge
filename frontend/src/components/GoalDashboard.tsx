'use client';

import React, { useState, useEffect } from 'react';
import GoalProgressChart from './GoalProgressChart';
import GoalProgressRing from './GoalProgressRing';
import GoalRecommendations from './GoalRecommendations';
import GoalCreationForm from './GoalCreationForm';

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

interface GoalForecast {
  goal_name: string;
  target_amount: number;
  current_savings: number;
  deadline: string;
  months_remaining: number;
  projection: {
    expected_total: number;
    optimistic_total: number;
    pessimistic_total: number;
    expected_monthly_savings: number;
    confidence_level: string;
  };
  status: 'very_likely' | 'likely' | 'possible' | 'unlikely';
  probability: string;
  on_track: boolean;
  gap_analysis: {
    shortfall: number;
    monthly_gap: number;
    required_monthly_savings: number;
    current_monthly_savings: number;
  } | null;
  competition_analysis?: {
    total_available_savings: number;
    competing_goals: Array<{
      goal_name: string;
      target_amount: number;
      deadline: string;
      required_monthly_savings: number;
      priority_level: string;
    }>;
    total_committed_savings: number;
    remaining_available_savings: number;
    is_overcommitted: boolean;
    overcommitment_amount: number;
  } | null;
  recommendations: Array<{
    action: string;
    category: string;
    monthly_savings: number;
    impact: string;
  }>;
  forecast_path: Array<{
    month: string;
    cumulative: number;
    lower: number;
    upper: number;
  }>;
}

export default function GoalDashboard() {
  const [goals, setGoals] = useState<Goal[]>([]);
  const [selectedGoalId, setSelectedGoalId] = useState<string | null>(null);
  const [forecast, setForecast] = useState<GoalForecast | null>(null);
  const [showCreateForm, setShowCreateForm] = useState(false);
  const [loading, setLoading] = useState(true);
  const [forecastLoading, setForecastLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const API_BASE_URL = 'http://localhost:8000';

  // Load goals on mount
  useEffect(() => {
    loadGoals();
  }, []);

  // Load forecast when a goal is selected
  useEffect(() => {
    if (selectedGoalId) {
      loadForecast(selectedGoalId);
    } else {
      setForecast(null);
    }
  }, [selectedGoalId]);

  const loadGoals = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await fetch(`${API_BASE_URL}/api/goals`);

      if (!response.ok) {
        throw new Error('Failed to load goals');
      }

      const data = await response.json();

      // Sort goals by deadline (closest deadline first)
      const sortedGoals = data.sort((a: Goal, b: Goal) => {
        return new Date(a.deadline).getTime() - new Date(b.deadline).getTime();
      });

      setGoals(sortedGoals);

      // Auto-select first goal if none selected (will be the one with closest deadline)
      if (sortedGoals.length > 0 && !selectedGoalId) {
        setSelectedGoalId(sortedGoals[0].id);
      }
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to load goals');
      console.error('Error loading goals:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadForecast = async (goalId: string) => {
    try {
      setForecastLoading(true);
      const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}/forecast`);

      if (!response.ok) {
        throw new Error('Failed to load forecast');
      }

      const data = await response.json();
      setForecast(data);
    } catch (err) {
      console.error('Error loading forecast:', err);
      setError(err instanceof Error ? err.message : 'Failed to load forecast');
    } finally {
      setForecastLoading(false);
    }
  };

  const handleCreateGoal = async (goalData: any) => {
    try {
      const params = new URLSearchParams({
        goal_name: goalData.goal_name,
        target_amount: goalData.target_amount.toString(),
        deadline: goalData.deadline,
        current_savings: goalData.current_savings.toString(),
        priority_level: goalData.priority_level,
        monthly_income: goalData.monthly_income.toString(),
        income_type: goalData.income_type
      });

      const response = await fetch(`${API_BASE_URL}/api/goals?${params}`, {
        method: 'POST',
      });

      if (!response.ok) {
        throw new Error('Failed to create goal');
      }

      const newGoal = await response.json();

      // Refresh goals list
      await loadGoals();

      // Select the newly created goal
      setSelectedGoalId(newGoal.id);

      // Hide the form
      setShowCreateForm(false);
    } catch (err) {
      console.error('Error creating goal:', err);
      throw err;
    }
  };

  const handleDeleteGoal = async (goalId: string) => {
    if (!confirm('Are you sure you want to delete this goal?')) {
      return;
    }

    try {
      const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete goal');
      }

      // Clear selection if deleted goal was selected
      if (selectedGoalId === goalId) {
        setSelectedGoalId(null);
      }

      // Refresh goals list
      await loadGoals();
    } catch (err) {
      console.error('Error deleting goal:', err);
      setError(err instanceof Error ? err.message : 'Failed to delete goal');
    }
  };

  const selectedGoal = goals.find(g => g.id === selectedGoalId);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-96">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Loading goals...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-7xl mx-auto p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900">Savings Goals</h1>
          <p className="text-gray-600 mt-1">Track and forecast your financial goals</p>
        </div>
        <button
          onClick={() => setShowCreateForm(!showCreateForm)}
          className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
        >
          {showCreateForm ? 'Cancel' : '+ New Goal'}
        </button>
      </div>

      {error && (
        <div className="bg-red-50 border border-red-200 rounded-lg p-4">
          <p className="text-red-800">{error}</p>
        </div>
      )}

      {/* Create Goal Form */}
      {showCreateForm && (
        <GoalCreationForm
          onSubmit={handleCreateGoal}
          onCancel={() => setShowCreateForm(false)}
        />
      )}

      {/* Goals List */}
      {goals.length === 0 && !showCreateForm ? (
        <div className="bg-gray-50 border-2 border-dashed border-gray-300 rounded-lg p-12 text-center">
          <svg className="w-16 h-16 text-gray-400 mx-auto mb-4" fill="none" viewBox="0 0 24 24" stroke="currentColor">
            <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z" />
          </svg>
          <h3 className="text-lg font-semibold text-gray-900 mb-2">No goals yet</h3>
          <p className="text-gray-600 mb-4">Create your first savings goal to get started!</p>
          <button
            onClick={() => setShowCreateForm(true)}
            className="bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors"
          >
            Create Your First Goal
          </button>
        </div>
      ) : (
        <div className="grid grid-cols-12 gap-6">
          {/* Goals Sidebar */}
          <div className="col-span-12 lg:col-span-3">
            <div className="bg-white border border-gray-200 rounded-lg p-4">
              <h3 className="font-semibold text-gray-900 mb-3">
                Your Goals
                <span className="ml-2 text-xs font-normal text-gray-500">
                  ({goals.length})
                </span>
              </h3>
              <div className="space-y-2 max-h-[calc(100vh-250px)] overflow-y-auto">
                {goals.map((goal, index) => {
                  // Calculate days until deadline
                  const today = new Date();
                  const deadline = new Date(goal.deadline);
                  const daysUntil = Math.ceil((deadline.getTime() - today.getTime()) / (1000 * 60 * 60 * 24));

                  // Determine urgency color
                  const getUrgencyColor = () => {
                    if (daysUntil < 30) return 'text-red-600';
                    if (daysUntil < 90) return 'text-orange-600';
                    return 'text-gray-600';
                  };

                  return (
                    <button
                      key={goal.id}
                      onClick={() => setSelectedGoalId(goal.id)}
                      className={`w-full text-left p-3 rounded-lg border transition-all ${
                        selectedGoalId === goal.id
                          ? 'bg-blue-50 border-blue-300 shadow-sm'
                          : 'border-gray-200 hover:border-gray-300 hover:shadow-sm'
                      }`}
                    >
                      <div className="flex items-start justify-between mb-1">
                        <div className="font-medium text-gray-900 text-sm flex-1">
                          {goal.goal_name}
                        </div>
                        {index === 0 && (
                          <span className="ml-2 px-2 py-0.5 bg-blue-100 text-blue-700 text-xs font-medium rounded">
                            Next
                          </span>
                        )}
                      </div>
                      <div className="text-xs font-semibold text-gray-700 mb-1">
                        ${goal.target_amount.toLocaleString()}
                      </div>
                      <div className={`text-xs ${getUrgencyColor()} font-medium`}>
                        {daysUntil > 0 ? (
                          <>
                            {daysUntil} day{daysUntil !== 1 ? 's' : ''} until deadline
                          </>
                        ) : (
                          <>Deadline passed</>
                        )}
                      </div>
                      <div className="text-xs text-gray-500 mt-0.5">
                        {new Date(goal.deadline).toLocaleDateString('en-US', {
                          month: 'short',
                          day: 'numeric',
                          year: 'numeric'
                        })}
                      </div>
                    </button>
                  );
                })}
              </div>
            </div>
          </div>

          {/* Main Content */}
          <div className="col-span-12 lg:col-span-9">
            {selectedGoal && forecast ? (
              <div className="space-y-6">
                {/* Goal Header */}
                <div className="bg-white border border-gray-200 rounded-lg p-6">
                  <div className="flex items-start justify-between">
                    <div>
                      <h2 className="text-2xl font-bold text-gray-900">{forecast.goal_name}</h2>
                      <p className="text-gray-600 mt-1">
                        {forecast.months_remaining} months remaining until{' '}
                        {new Date(forecast.deadline).toLocaleDateString()}
                      </p>
                    </div>
                    <button
                      onClick={() => handleDeleteGoal(selectedGoal.id)}
                      className="text-red-600 hover:text-red-700 text-sm font-medium"
                    >
                      Delete Goal
                    </button>
                  </div>
                </div>

                {/* Progress Ring and Chart */}
                <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
                  <div className="bg-white border border-gray-200 rounded-lg p-6 flex items-center justify-center">
                    <GoalProgressRing
                      currentSavings={forecast.current_savings}
                      targetAmount={forecast.target_amount}
                      status={forecast.status}
                    />
                  </div>

                  <div className="lg:col-span-2 bg-white border border-gray-200 rounded-lg p-6">
                    <GoalProgressChart
                      forecastPath={forecast.forecast_path}
                      targetAmount={forecast.target_amount}
                      currentSavings={forecast.current_savings}
                      deadline={forecast.deadline}
                      status={forecast.status}
                      goalName={forecast.goal_name}
                      projection={forecast.projection}
                      gapAnalysis={forecast.gap_analysis}
                      monthlyIncome={selectedGoal?.monthly_income || 0}
                      competitionAnalysis={forecast.competition_analysis}
                      currentGoalPriority={selectedGoal?.priority_level || 'medium'}
                    />
                  </div>
                </div>

                {/* Recommendations */}
                <GoalRecommendations
                  recommendations={forecast.recommendations}
                  gapAnalysis={forecast.gap_analysis}
                  onTrack={forecast.on_track}
                />
              </div>
            ) : forecastLoading ? (
              <div className="bg-white border border-gray-200 rounded-lg p-12">
                <div className="text-center">
                  <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
                  <p className="text-gray-600">Generating forecast...</p>
                </div>
              </div>
            ) : (
              <div className="bg-white border border-gray-200 rounded-lg p-12 text-center">
                <p className="text-gray-600">Select a goal to view its forecast</p>
              </div>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
