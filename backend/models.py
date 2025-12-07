from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str
    date: datetime
    amount: float
    merchant_name: str
    category: List[str]
    payment_channel: str
    pending: bool


class Trigger(BaseModel):
    type: str
    category: Optional[str] = None
    merchant: Optional[str] = None
    this_month: Optional[float] = None
    last_month: Optional[float] = None
    average: Optional[float] = None
    percent_change: Optional[float] = None
    dollar_change: Optional[float] = None
    top_merchants: Optional[List[str]] = None
    visit_count: Optional[int] = None
    savings_rate: Optional[float] = None
    weekend_spend: Optional[float] = None
    weekday_spend: Optional[float] = None
    raw_data: Optional[dict] = None


class TransactionSummary(BaseModel):
    """Summary of a transaction for display in insight details"""
    date: str
    merchant: str
    amount: float
    category: str


class InsightDetails(BaseModel):
    """Detailed breakdown of calculations and reasoning behind an insight"""
    calculation_method: str  # Description of the calculation method used
    raw_values: dict  # The raw numbers used in the calculation
    timeframe: str  # The timeframe analyzed (e.g., "Last 6 months", "This week vs last week")
    comparison_context: str  # Additional context about what was compared
    transactions: List[TransactionSummary]  # The actual transactions used in this calculation


class Insight(BaseModel):
    id: str
    type: Literal["win", "alert", "anomaly"]
    emoji: str
    headline: str
    description: str
    timestamp: str
    priority_score: float
    trigger_type: str
    details: Optional[InsightDetails] = None  # Detailed calculation breakdown


class AggregatedStats(BaseModel):
    spending_by_category_this_month: dict
    spending_by_category_last_month: dict
    spending_by_category_3mo_average: dict
    spending_by_merchant_this_month: dict
    spending_by_day_of_week: dict
    total_income_this_month: float
    total_spending_this_month: float
    total_spending_last_month: float


# Goal Forecasting Models

class MonthlyProjection(BaseModel):
    """Individual month in the forecast path"""
    month: str  # Format: "2024-05"
    cumulative: float  # Expected cumulative savings at this point
    lower: float  # Pessimistic bound (80% confidence)
    upper: float  # Optimistic bound (80% confidence)


class GoalRecommendation(BaseModel):
    """Specific spending cut suggestion to help reach goal"""
    action: str  # e.g., "Reduce dining out by 25%"
    category: str  # Category to cut (e.g., "DINING")
    monthly_savings: float  # Expected savings per month
    impact: str  # Description of impact (e.g., "Closes gap with $12 buffer")


class GapAnalysis(BaseModel):
    """Analysis of shortfall when goal is off-track"""
    shortfall: float  # Total amount short of goal
    monthly_gap: float  # Additional savings needed per month
    required_monthly_savings: float  # Total needed per month to hit goal
    current_monthly_savings: float  # Current average monthly savings


class GoalProjection(BaseModel):
    """Forecast projection data"""
    expected_total: float  # Expected cumulative at deadline
    optimistic_total: float  # Upper bound at deadline
    pessimistic_total: float  # Lower bound at deadline
    expected_monthly_savings: float  # Average monthly savings rate
    confidence_level: str  # e.g., "80%"


class Goal(BaseModel):
    """User's savings goal"""
    id: str
    goal_name: str
    target_amount: float
    deadline: str  # ISO date string
    current_savings: float = 0.0
    priority_level: Optional[Literal["high", "medium", "low"]] = "medium"
    created_at: str  # ISO datetime string
    user_id: Optional[str] = "default_user"  # For future multi-user support

    # Income information for savings calculation
    monthly_income: float  # User's monthly income
    income_type: Optional[Literal["fixed", "variable"]] = "fixed"  # Income stability


class GoalForecast(BaseModel):
    """Complete forecast for a goal with status and recommendations"""
    goal_name: str
    target_amount: float
    current_savings: float
    deadline: str
    months_remaining: float

    projection: GoalProjection

    status: Literal["very_likely", "likely", "possible", "unlikely"]
    probability: str  # e.g., "90%+ chance", "60-80% chance"
    on_track: bool

    gap_analysis: Optional[GapAnalysis] = None
    recommendations: List[GoalRecommendation] = []
    forecast_path: List[MonthlyProjection] = []
