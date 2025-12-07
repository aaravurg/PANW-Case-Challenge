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


class SpendingBreakdown(BaseModel):
    """Breakdown of spending by necessity"""
    monthly_necessary: float  # Average monthly necessary spending (rent, utilities, groceries, etc.)
    monthly_discretionary: float  # Average monthly discretionary spending (dining, entertainment, etc.)
    monthly_total: float  # Total average monthly spending
    necessary_percent: float  # Percentage that is necessary
    discretionary_percent: float  # Percentage that is discretionary
    max_realistic_cuts: float  # Maximum amount that can realistically be cut (70% of discretionary)

class RealisticAnalysis(BaseModel):
    """Analysis of whether goal is realistically achievable"""
    is_achievable: bool  # Can goal be reached with realistic cuts?
    achievability: str  # "realistic", "difficult", or "unrealistic"
    necessary_spending: float  # Monthly necessary spending
    discretionary_spending: float  # Monthly discretionary spending
    required_cuts: float  # How much spending needs to be cut
    max_realistic_cuts: float  # Maximum realistic cuts possible
    target_discretionary: float  # What discretionary spending should be
    shortfall: float  # Shortfall if not achievable

class CompetingGoal(BaseModel):
    """Information about another active goal competing for savings"""
    goal_name: str
    target_amount: float
    deadline: str
    required_monthly_savings: float
    priority_level: str

class GoalCompetitionAnalysis(BaseModel):
    """Analysis of how this goal competes with other active goals"""
    total_available_savings: float  # Total monthly savings capacity (Income - Spending)
    competing_goals: List[CompetingGoal]  # Other active goals
    total_committed_savings: float  # Savings already committed to other goals
    remaining_available_savings: float  # Savings left after other goals
    is_overcommitted: bool  # Are you trying to save more than you have?
    overcommitment_amount: float  # How much over-committed (if any)

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
    is_active: Optional[bool] = True  # Whether this goal is currently active

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
    spending_breakdown: Optional[SpendingBreakdown] = None  # Breakdown by necessity
    realistic_analysis: Optional[RealisticAnalysis] = None  # Realistic achievability
    competition_analysis: Optional[GoalCompetitionAnalysis] = None  # Competition with other goals
    recommendations: List[GoalRecommendation] = []
    forecast_path: List[MonthlyProjection] = []


# Subscription Detection Models

class PriceIncrease(BaseModel):
    """Information about a detected price increase"""
    old_price: float
    new_price: float
    percent_change: float
    detected_date: str  # ISO date string


class SubscriptionCharge(BaseModel):
    """Individual charge within a subscription"""
    date: str  # ISO date string
    amount: float


class Subscription(BaseModel):
    """Detected recurring subscription"""
    merchant_name: str  # Normalized merchant name
    original_merchant_name: str  # Original merchant name from transactions
    frequency: str  # "weekly", "bi-weekly", "monthly", "quarterly", "annual"
    frequency_days: int  # Average interval in days

    # Amount information
    current_amount: float  # Most recent charge amount
    average_amount: float  # Historical average amount
    min_amount: float  # Minimum charge seen
    max_amount: float  # Maximum charge seen

    # Transaction history
    first_charge_date: str  # ISO date string
    last_charge_date: str  # ISO date string
    next_predicted_date: Optional[str] = None  # ISO date string
    transaction_count: int  # Number of charges detected
    charges: List[SubscriptionCharge] = []  # All detected charges

    # Cost normalization
    monthly_cost: float  # Normalized to monthly cost
    annual_cost: float  # Normalized to annual cost

    # Detection metrics
    confidence_score: float  # 0-100 confidence in detection
    interval_regularity: float  # Coefficient of variation (lower = more regular)
    amount_consistency: float  # Coefficient of variation (lower = more consistent)

    # Status flags
    is_gray_charge: bool = False  # Potentially forgotten/sneaky subscription
    has_price_increase: bool = False  # Recently increased in price
    is_trial_conversion: bool = False  # Recently converted from trial
    needs_attention: bool = False  # Any flag requiring user attention

    # Optional price increase details
    price_increase: Optional[PriceIncrease] = None


class SubscriptionSummary(BaseModel):
    """Summary of all detected subscriptions"""
    total_subscriptions: int
    total_monthly_cost: float
    total_annual_cost: float
    gray_charges_count: int
    price_increases_count: int
    trial_conversions_count: int
    subscriptions: List[Subscription]
