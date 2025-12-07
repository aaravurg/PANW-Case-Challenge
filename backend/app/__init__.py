"""
Core application module containing FastAPI app and data models.
"""

# Lazy imports to avoid circular dependencies and missing dependency errors
__all__ = [
    'app',
    'Transaction',
    'Insight',
    'Goal',
    'GoalForecast',
    'GoalProjection',
    'MonthlyProjection',
    'GapAnalysis',
    'SpendingBreakdown',
    'RealisticAnalysis',
    'GoalCompetitionAnalysis',
    'CompetingGoal'
]
