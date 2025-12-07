/**
 * API Client for Goal Forecasting
 * Provides typed functions for interacting with the backend API
 */

const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

export interface Goal {
  id: string;
  goal_name: string;
  target_amount: number;
  deadline: string;
  current_savings: number;
  priority_level: 'high' | 'medium' | 'low';
  created_at: string;
  user_id?: string;
}

export interface GoalForecast {
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

export interface CreateGoalParams {
  goal_name: string;
  target_amount: number;
  deadline: string;
  current_savings?: number;
  priority_level?: 'high' | 'medium' | 'low';
  user_id?: string;
}

export interface UpdateGoalParams {
  goal_name?: string;
  target_amount?: number;
  deadline?: string;
  current_savings?: number;
  priority_level?: 'high' | 'medium' | 'low';
}

/**
 * Create a new savings goal
 */
export async function createGoal(params: CreateGoalParams): Promise<Goal> {
  const queryParams = new URLSearchParams({
    goal_name: params.goal_name,
    target_amount: params.target_amount.toString(),
    deadline: params.deadline,
    ...(params.current_savings !== undefined && {
      current_savings: params.current_savings.toString()
    }),
    ...(params.priority_level && { priority_level: params.priority_level }),
    ...(params.user_id && { user_id: params.user_id })
  });

  const response = await fetch(`${API_BASE_URL}/api/goals?${queryParams}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to create goal' }));
    throw new Error(error.detail || 'Failed to create goal');
  }

  return response.json();
}

/**
 * Get all goals for a user
 */
export async function getGoals(userId: string = 'default_user'): Promise<Goal[]> {
  const response = await fetch(`${API_BASE_URL}/api/goals?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch goals' }));
    throw new Error(error.detail || 'Failed to fetch goals');
  }

  return response.json();
}

/**
 * Get a specific goal by ID
 */
export async function getGoal(goalId: string, userId: string = 'default_user'): Promise<Goal> {
  const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}?user_id=${userId}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch goal' }));
    throw new Error(error.detail || 'Failed to fetch goal');
  }

  return response.json();
}

/**
 * Get forecast for a specific goal
 */
export async function getGoalForecast(
  goalId: string,
  userId: string = 'default_user'
): Promise<GoalForecast> {
  const response = await fetch(
    `${API_BASE_URL}/api/goals/${goalId}/forecast?user_id=${userId}`
  );

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to fetch forecast' }));
    throw new Error(error.detail || 'Failed to fetch forecast');
  }

  return response.json();
}

/**
 * Update an existing goal
 */
export async function updateGoal(
  goalId: string,
  params: UpdateGoalParams,
  userId: string = 'default_user'
): Promise<Goal> {
  const queryParams = new URLSearchParams({
    user_id: userId,
    ...(params.goal_name && { goal_name: params.goal_name }),
    ...(params.target_amount !== undefined && {
      target_amount: params.target_amount.toString()
    }),
    ...(params.deadline && { deadline: params.deadline }),
    ...(params.current_savings !== undefined && {
      current_savings: params.current_savings.toString()
    }),
    ...(params.priority_level && { priority_level: params.priority_level })
  });

  const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}?${queryParams}`, {
    method: 'PUT',
    headers: {
      'Content-Type': 'application/json',
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to update goal' }));
    throw new Error(error.detail || 'Failed to update goal');
  }

  return response.json();
}

/**
 * Delete a goal
 */
export async function deleteGoal(
  goalId: string,
  userId: string = 'default_user'
): Promise<{ message: string; goal_id: string }> {
  const response = await fetch(`${API_BASE_URL}/api/goals/${goalId}?user_id=${userId}`, {
    method: 'DELETE',
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: 'Failed to delete goal' }));
    throw new Error(error.detail || 'Failed to delete goal');
  }

  return response.json();
}
