'use client';

import React, { useState } from 'react';

interface GoalCreationFormProps {
  onSubmit: (goalData: {
    goal_name: string;
    target_amount: number;
    deadline: string;
    current_savings: number;
    priority_level: string;
    monthly_income: number;
    income_type: string;
  }) => Promise<void>;
  onCancel?: () => void;
}

export default function GoalCreationForm({ onSubmit, onCancel }: GoalCreationFormProps) {
  const [formData, setFormData] = useState({
    goal_name: '',
    target_amount: '',
    deadline: '',
    current_savings: '',
    priority_level: 'medium',
    monthly_income: '',
    income_type: 'fixed'
  });

  const [errors, setErrors] = useState<Record<string, string>>({});
  const [isSubmitting, setIsSubmitting] = useState(false);

  const validateForm = (): boolean => {
    const newErrors: Record<string, string> = {};

    // Validate goal name
    if (!formData.goal_name.trim()) {
      newErrors.goal_name = 'Goal name is required';
    } else if (formData.goal_name.length > 100) {
      newErrors.goal_name = 'Goal name must be less than 100 characters';
    }

    // Validate target amount
    const targetAmount = parseFloat(formData.target_amount);
    if (!formData.target_amount) {
      newErrors.target_amount = 'Target amount is required';
    } else if (isNaN(targetAmount) || targetAmount <= 0) {
      newErrors.target_amount = 'Target amount must be greater than 0';
    } else if (targetAmount > 10000000) {
      newErrors.target_amount = 'Target amount must be less than $10,000,000';
    }

    // Validate deadline
    if (!formData.deadline) {
      newErrors.deadline = 'Deadline is required';
    } else {
      const deadlineDate = new Date(formData.deadline);
      const today = new Date();
      today.setHours(0, 0, 0, 0);

      if (deadlineDate <= today) {
        newErrors.deadline = 'Deadline must be in the future';
      }

      // Check if deadline is too far in the future (e.g., 10 years)
      const maxDate = new Date();
      maxDate.setFullYear(maxDate.getFullYear() + 10);
      if (deadlineDate > maxDate) {
        newErrors.deadline = 'Deadline cannot be more than 10 years from now';
      }
    }

    // Validate current savings
    if (formData.current_savings) {
      const currentSavings = parseFloat(formData.current_savings);
      if (isNaN(currentSavings) || currentSavings < 0) {
        newErrors.current_savings = 'Current savings must be 0 or greater';
      }

      // Check if current savings already exceeds target
      if (currentSavings >= targetAmount) {
        newErrors.current_savings = 'Current savings cannot exceed target amount';
      }
    }

    // Validate monthly income
    const monthlyIncome = parseFloat(formData.monthly_income);
    if (!formData.monthly_income) {
      newErrors.monthly_income = 'Monthly income is required for forecasting';
    } else if (isNaN(monthlyIncome) || monthlyIncome <= 0) {
      newErrors.monthly_income = 'Monthly income must be greater than 0';
    } else if (monthlyIncome > 10000000) {
      newErrors.monthly_income = 'Monthly income must be less than $10,000,000';
    }

    setErrors(newErrors);
    return Object.keys(newErrors).length === 0;
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();

    if (!validateForm()) {
      return;
    }

    setIsSubmitting(true);

    try {
      await onSubmit({
        goal_name: formData.goal_name.trim(),
        target_amount: parseFloat(formData.target_amount),
        deadline: formData.deadline,
        current_savings: formData.current_savings ? parseFloat(formData.current_savings) : 0,
        priority_level: formData.priority_level,
        monthly_income: parseFloat(formData.monthly_income),
        income_type: formData.income_type
      });

      // Reset form on success
      setFormData({
        goal_name: '',
        target_amount: '',
        deadline: '',
        current_savings: '',
        priority_level: 'medium',
        monthly_income: '',
        income_type: 'fixed'
      });
    } catch (error) {
      console.error('Error creating goal:', error);
    } finally {
      setIsSubmitting(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));

    // Clear error for this field when user starts typing
    if (errors[name]) {
      setErrors(prev => {
        const newErrors = { ...prev };
        delete newErrors[name];
        return newErrors;
      });
    }
  };

  return (
    <form onSubmit={handleSubmit} className="space-y-6">
      <div className="bg-white rounded-lg border border-gray-200 p-6">
        <h3 className="text-lg font-semibold text-gray-900 mb-4">Create New Goal</h3>

        {/* Goal Name */}
        <div className="mb-4">
          <label htmlFor="goal_name" className="block text-sm font-medium text-gray-700 mb-1">
            Goal Name <span className="text-red-500">*</span>
          </label>
          <input
            type="text"
            id="goal_name"
            name="goal_name"
            value={formData.goal_name}
            onChange={handleChange}
            placeholder="e.g., Tesla Down Payment, Vacation Fund"
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.goal_name ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.goal_name && (
            <p className="mt-1 text-sm text-red-600">{errors.goal_name}</p>
          )}
        </div>

        {/* Target Amount */}
        <div className="mb-4">
          <label htmlFor="target_amount" className="block text-sm font-medium text-gray-700 mb-1">
            Target Amount <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-4 top-2 text-gray-500">$</span>
            <input
              type="number"
              id="target_amount"
              name="target_amount"
              value={formData.target_amount}
              onChange={handleChange}
              placeholder="5000"
              step="0.01"
              min="0"
              className={`w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.target_amount ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.target_amount && (
            <p className="mt-1 text-sm text-red-600">{errors.target_amount}</p>
          )}
        </div>

        {/* Deadline */}
        <div className="mb-4">
          <label htmlFor="deadline" className="block text-sm font-medium text-gray-700 mb-1">
            Deadline <span className="text-red-500">*</span>
          </label>
          <input
            type="date"
            id="deadline"
            name="deadline"
            value={formData.deadline}
            onChange={handleChange}
            className={`w-full px-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
              errors.deadline ? 'border-red-500' : 'border-gray-300'
            }`}
          />
          {errors.deadline && (
            <p className="mt-1 text-sm text-red-600">{errors.deadline}</p>
          )}
        </div>

        {/* Current Savings (Optional) */}
        <div className="mb-4">
          <label htmlFor="current_savings" className="block text-sm font-medium text-gray-700 mb-1">
            Current Savings (Optional)
          </label>
          <div className="relative">
            <span className="absolute left-4 top-2 text-gray-500">$</span>
            <input
              type="number"
              id="current_savings"
              name="current_savings"
              value={formData.current_savings}
              onChange={handleChange}
              placeholder="1200"
              step="0.01"
              min="0"
              className={`w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.current_savings ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.current_savings && (
            <p className="mt-1 text-sm text-red-600">{errors.current_savings}</p>
          )}
        </div>

        {/* Monthly Income */}
        <div className="mb-4">
          <label htmlFor="monthly_income" className="block text-sm font-medium text-gray-700 mb-1">
            Monthly Income <span className="text-red-500">*</span>
          </label>
          <div className="relative">
            <span className="absolute left-4 top-2 text-gray-500">$</span>
            <input
              type="number"
              id="monthly_income"
              name="monthly_income"
              value={formData.monthly_income}
              onChange={handleChange}
              placeholder="5000"
              step="0.01"
              min="0"
              className={`w-full pl-8 pr-4 py-2 border rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent ${
                errors.monthly_income ? 'border-red-500' : 'border-gray-300'
              }`}
            />
          </div>
          {errors.monthly_income && (
            <p className="mt-1 text-sm text-red-600">{errors.monthly_income}</p>
          )}
          <p className="mt-1 text-xs text-gray-500">
            Used to forecast your savings based on spending patterns
          </p>
        </div>

        {/* Income Type */}
        <div className="mb-4">
          <label htmlFor="income_type" className="block text-sm font-medium text-gray-700 mb-1">
            Income Type
          </label>
          <select
            id="income_type"
            name="income_type"
            value={formData.income_type}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="fixed">Fixed (Salary/Stable Income)</option>
            <option value="variable">Variable (Freelance/Commission)</option>
          </select>
          <p className="mt-1 text-xs text-gray-500">
            Variable income adds extra uncertainty to forecasts
          </p>
        </div>

        {/* Priority Level */}
        <div className="mb-6">
          <label htmlFor="priority_level" className="block text-sm font-medium text-gray-700 mb-1">
            Priority Level
          </label>
          <select
            id="priority_level"
            name="priority_level"
            value={formData.priority_level}
            onChange={handleChange}
            className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
          >
            <option value="high">High</option>
            <option value="medium">Medium</option>
            <option value="low">Low</option>
          </select>
        </div>

        {/* Form Actions */}
        <div className="flex gap-3">
          <button
            type="submit"
            disabled={isSubmitting}
            className={`flex-1 bg-blue-600 text-white px-6 py-2 rounded-lg font-medium hover:bg-blue-700 transition-colors ${
              isSubmitting ? 'opacity-50 cursor-not-allowed' : ''
            }`}
          >
            {isSubmitting ? 'Creating...' : 'Create Goal'}
          </button>

          {onCancel && (
            <button
              type="button"
              onClick={onCancel}
              disabled={isSubmitting}
              className="px-6 py-2 border border-gray-300 text-gray-700 rounded-lg font-medium hover:bg-gray-50 transition-colors"
            >
              Cancel
            </button>
          )}
        </div>
      </div>
    </form>
  );
}
