"""
Goal Forecasting Service using Facebook Prophet for time series prediction
with fallback to linear projection for edge cases

KEY INSIGHT:
We forecast SPENDING (what varies), not savings (which we don't have historical data for).
Then we derive savings using: Savings = Income - Predicted Spending

WHY THIS APPROACH:
- Historical data: We have spending from credit card transactions ✅
- No historical data: We don't have income or savings history ❌
- Solution: User provides monthly income, we forecast spending variability

HOW CONFIDENCE INTERVALS WORK:
Prophet gives us spending predictions with confidence intervals:
  - yhat: Expected spending
  - yhat_lower: Low spending (optimistic case)
  - yhat_upper: High spending (pessimistic case)

When converting to savings, intervals are INVERTED:
  - Expected savings = Income - Expected spending
  - Optimistic savings = Income - Lower spending  (spend less = save more)
  - Pessimistic savings = Income - Higher spending (spend more = save less)

VARIABLE INCOME HANDLING:
For users with variable income, we add uncertainty to income as well:
  - Optimistic scenario: Higher income (110%) + Lower spending
  - Pessimistic scenario: Lower income (85%) + Higher spending
  - This compounds the confidence intervals appropriately
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import List, Tuple, Optional
import warnings

from models import (
    Transaction, Goal, GoalForecast, GoalProjection,
    MonthlyProjection, GapAnalysis
)

# Try to import Prophet, but gracefully handle if not installed
PROPHET_AVAILABLE = False
try:
    from prophet import Prophet
    PROPHET_AVAILABLE = True
    warnings.filterwarnings('ignore', category=FutureWarning)
    warnings.filterwarnings('ignore', message='.*cmdstanpy.*')
except ImportError:
    print("Prophet not available, will use linear fallback for forecasting")


class GoalForecaster:
    """
    Forecasts whether a user will reach their savings goal based on
    transaction history using Prophet or linear projection
    """

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """Convert transactions to DataFrame"""
        data = []
        for t in self.transactions:
            data.append({
                'date': t.date,
                'amount': t.amount,
                'category': t.category[0] if t.category else 'OTHER',
                'merchant_name': t.merchant_name
            })

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        return df

    def calculate_monthly_spending(self) -> pd.DataFrame:
        """
        Calculate monthly SPENDING (absolute value) from transaction history.
        This is what Prophet will forecast.

        Returns DataFrame with columns: month_date, spending
        """
        if self.df.empty:
            return pd.DataFrame(columns=['month_date', 'spending'])

        # Create a copy for monthly aggregation
        df = self.df.copy()

        # Extract year-month for grouping
        df['year_month'] = df['date'].dt.to_period('M')

        # Filter only negative amounts (expenses)
        spending_df = df[df['amount'] < 0].copy()

        # Group by month and sum spending (take absolute value)
        monthly_spending = spending_df.groupby('year_month')['amount'].sum().reset_index()

        # Convert period back to timestamp (first day of month)
        monthly_spending['month_date'] = monthly_spending['year_month'].dt.to_timestamp()

        # Convert to positive spending amounts
        monthly_spending['spending'] = abs(monthly_spending['amount'])

        # Exclude current incomplete month
        current_month = pd.Timestamp.now().to_period('M')
        monthly_spending = monthly_spending[monthly_spending['year_month'] < current_month]

        return monthly_spending[['month_date', 'spending']].sort_values('month_date')

    def _use_prophet_forecast(
        self,
        historical_data: pd.DataFrame,
        months_ahead: int
    ) -> Tuple[pd.DataFrame, bool]:
        """
        Use Prophet for forecasting SPENDING if available and data is sufficient

        Returns: (forecast_df, success)
        """
        if not PROPHET_AVAILABLE:
            print("   ❌ Prophet library not available")
            return None, False

        if len(historical_data) < 4:
            print(f"   ❌ Insufficient data: {len(historical_data)} months (need 4+)")
            return None, False

        try:
            # Prepare data for Prophet (needs 'ds' and 'y' columns)
            prophet_df = historical_data.copy()
            prophet_df = prophet_df.rename(columns={'month_date': 'ds', 'spending': 'y'})

            print(f"   🤖 Initializing Prophet model...")
            # Initialize Prophet with conservative settings
            model = Prophet(
                yearly_seasonality=False,  # Not enough data for yearly patterns
                weekly_seasonality=False,  # Monthly data doesn't need weekly
                daily_seasonality=False,
                interval_width=0.80,  # 80% confidence intervals
                changepoint_prior_scale=0.05  # Conservative - stable behavior
            )

            # Fit model
            print(f"   🔬 Training model on {len(prophet_df)} months of data...")
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")
                model.fit(prophet_df)

            # Create future dataframe
            future_dates = model.make_future_dataframe(
                periods=months_ahead,
                freq='MS'  # Month start frequency
            )

            # Generate forecast
            print(f"   📈 Generating {months_ahead}-month forecast...")
            forecast = model.predict(future_dates)
            return forecast, True

        except Exception as e:
            print(f"Prophet forecasting failed: {e}")
            return None, False

    def _use_linear_fallback(
        self,
        historical_data: pd.DataFrame,
        months_ahead: int
    ) -> pd.DataFrame:
        """
        Simple linear projection fallback when Prophet is unavailable
        Forecasts SPENDING, not savings
        """
        # Calculate average monthly spending
        avg_monthly_spending = historical_data['spending'].mean()
        std_monthly_spending = historical_data['spending'].std()

        # If no variability data, use 20% of mean as std
        if pd.isna(std_monthly_spending) or std_monthly_spending == 0:
            std_monthly_spending = abs(avg_monthly_spending * 0.2)

        # Create future dates
        last_date = historical_data['month_date'].max()
        future_dates = [
            last_date + relativedelta(months=i)
            for i in range(1, months_ahead + 1)
        ]

        # Create forecast dataframe
        forecast_data = []
        for date in future_dates:
            forecast_data.append({
                'ds': date,
                'yhat': avg_monthly_spending,
                'yhat_lower': avg_monthly_spending - std_monthly_spending,
                'yhat_upper': avg_monthly_spending + std_monthly_spending
            })

        return pd.DataFrame(forecast_data)

    def generate_forecast(
        self,
        goal: Goal
    ) -> Tuple[pd.DataFrame, float, bool]:
        """
        Generate forecast for a goal by:
        1. Forecasting monthly SPENDING using Prophet
        2. Converting to SAVINGS using user's income: Savings = Income - Spending
        3. Inverting confidence intervals (lower spending = higher savings)

        Returns: (savings_forecast_df, avg_monthly_savings, used_prophet)
        """
        # Get historical monthly spending
        historical_spending = self.calculate_monthly_spending()

        if historical_spending.empty or len(historical_spending) < 2:
            raise ValueError(
                "Insufficient transaction history. Need at least 2 months of data."
            )

        # Calculate months until deadline
        deadline_date = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
        today = datetime.now()
        months_remaining = (
            (deadline_date.year - today.year) * 12 +
            deadline_date.month - today.month
        )

        if months_remaining < 1:
            months_remaining = 1

        # Try Prophet first, fall back to linear if needed
        # This forecasts SPENDING
        print(f"\n📊 Forecasting with {len(historical_spending)} months of historical data...")
        spending_forecast, used_prophet = self._use_prophet_forecast(
            historical_spending,
            months_remaining + 2  # Forecast a bit beyond deadline
        )

        if not used_prophet or spending_forecast is None:
            print("⚠️  Using LINEAR FALLBACK (Prophet unavailable or insufficient data)")
            spending_forecast = self._use_linear_fallback(
                historical_spending,
                months_remaining + 2
            )
        else:
            print("✅ Using FACEBOOK PROPHET ML model for forecasting")

        # Convert spending forecast to savings forecast
        # KEY INSIGHT: Savings = Income - Spending
        # Confidence intervals are INVERTED:
        #   - Lower spending (yhat_lower) → Higher savings (optimistic)
        #   - Higher spending (yhat_upper) → Lower savings (pessimistic)

        income = goal.monthly_income

        # Add income uncertainty for variable income
        if goal.income_type == "variable":
            income_buffer = 0.15  # 15% variance for variable income
            optimistic_income = income * 1.10
            pessimistic_income = income * 0.85
        else:
            optimistic_income = income
            pessimistic_income = income

        # Convert to savings with proper interval inversion
        savings_forecast = spending_forecast.copy()

        # Expected savings = income - expected spending
        savings_forecast['yhat'] = income - spending_forecast['yhat']

        # INVERTED: Optimistic savings = higher income - lower spending
        savings_forecast['yhat_upper'] = optimistic_income - spending_forecast['yhat_lower']

        # INVERTED: Pessimistic savings = lower income - higher spending
        savings_forecast['yhat_lower'] = pessimistic_income - spending_forecast['yhat_upper']

        # Calculate average monthly savings from historical data
        avg_monthly_spending = historical_spending['spending'].mean()
        avg_monthly_savings = income - avg_monthly_spending

        return savings_forecast, avg_monthly_savings, used_prophet

    def calculate_cumulative_projection(
        self,
        forecast: pd.DataFrame,
        current_savings: float,
        start_date: datetime
    ) -> pd.DataFrame:
        """
        Calculate cumulative savings over time from forecast

        Returns DataFrame with: date, cumulative, cumulative_lower, cumulative_upper
        """
        # Filter to future dates only
        future_forecast = forecast[forecast['ds'] > start_date].copy()

        # Calculate cumulative sums
        future_forecast['cumulative'] = current_savings + future_forecast['yhat'].cumsum()
        future_forecast['cumulative_lower'] = current_savings + future_forecast['yhat_lower'].cumsum()
        future_forecast['cumulative_upper'] = current_savings + future_forecast['yhat_upper'].cumsum()

        return future_forecast[['ds', 'cumulative', 'cumulative_lower', 'cumulative_upper']]

    def assess_probability(
        self,
        target_amount: float,
        expected_total: float,
        optimistic_total: float,
        pessimistic_total: float
    ) -> Tuple[str, str, bool]:
        """
        Assess probability of reaching goal

        Returns: (status, probability_text, on_track)
        """
        if pessimistic_total >= target_amount:
            return "very_likely", "90%+ chance", True
        elif expected_total >= target_amount:
            return "likely", "60-80% chance", True
        elif optimistic_total >= target_amount:
            return "possible", "30-50% chance", False
        else:
            return "unlikely", "<30% chance", False

    def analyze_gap(
        self,
        goal: Goal,
        expected_total: float,
        avg_monthly_savings: float,
        months_remaining: float
    ) -> Optional[GapAnalysis]:
        """
        Analyze shortfall if goal is off track

        Returns GapAnalysis if off-track, None if on-track
        """
        shortfall = goal.target_amount - expected_total

        if shortfall <= 0:
            return None

        monthly_gap = shortfall / months_remaining if months_remaining > 0 else shortfall
        required_monthly_savings = (
            (goal.target_amount - goal.current_savings) / months_remaining
            if months_remaining > 0
            else goal.target_amount - goal.current_savings
        )

        return GapAnalysis(
            shortfall=round(shortfall, 2),
            monthly_gap=round(monthly_gap, 2),
            required_monthly_savings=round(required_monthly_savings, 2),
            current_monthly_savings=round(avg_monthly_savings, 2)
        )

    def create_forecast_path(
        self,
        cumulative_projection: pd.DataFrame,
        deadline: datetime
    ) -> List[MonthlyProjection]:
        """
        Create the forecast path for visualization

        Returns list of MonthlyProjection objects
        """
        forecast_path = []

        for _, row in cumulative_projection.iterrows():
            # Stop at deadline
            if row['ds'] > deadline:
                break

            forecast_path.append(MonthlyProjection(
                month=row['ds'].strftime('%Y-%m'),
                cumulative=round(row['cumulative'], 2),
                lower=round(row['cumulative_lower'], 2),
                upper=round(row['cumulative_upper'], 2)
            ))

        return forecast_path

    def forecast_goal(self, goal: Goal) -> GoalForecast:
        """
        Complete forecast generation for a goal

        Returns GoalForecast with all analysis and recommendations
        """
        # Generate forecast
        forecast_df, avg_monthly_savings, used_prophet = self.generate_forecast(goal)

        # Calculate deadline info
        deadline_date = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
        today = datetime.now()
        months_remaining = (
            (deadline_date.year - today.year) * 12 +
            deadline_date.month - today.month
        )
        months_remaining = max(months_remaining, 0.5)  # At least half a month

        # Calculate cumulative projections
        cumulative_proj = self.calculate_cumulative_projection(
            forecast_df,
            goal.current_savings,
            today
        )

        # Find values at deadline
        deadline_row = cumulative_proj[
            cumulative_proj['ds'] <= deadline_date
        ].iloc[-1] if len(cumulative_proj) > 0 else None

        if deadline_row is None:
            raise ValueError("Could not generate projection to deadline")

        expected_total = deadline_row['cumulative']
        optimistic_total = deadline_row['cumulative_upper']
        pessimistic_total = deadline_row['cumulative_lower']

        # Assess probability
        status, probability, on_track = self.assess_probability(
            goal.target_amount,
            expected_total,
            optimistic_total,
            pessimistic_total
        )

        # Analyze gap if needed
        gap_analysis = self.analyze_gap(
            goal,
            expected_total,
            avg_monthly_savings,
            months_remaining
        )

        # Create forecast path
        forecast_path = self.create_forecast_path(cumulative_proj, deadline_date)

        # Create projection summary
        projection = GoalProjection(
            expected_total=round(expected_total, 2),
            optimistic_total=round(optimistic_total, 2),
            pessimistic_total=round(pessimistic_total, 2),
            expected_monthly_savings=round(avg_monthly_savings, 2),
            confidence_level="80%"
        )

        # Build complete forecast
        return GoalForecast(
            goal_name=goal.goal_name,
            target_amount=goal.target_amount,
            current_savings=goal.current_savings,
            deadline=goal.deadline,
            months_remaining=round(months_remaining, 1),
            projection=projection,
            status=status,
            probability=probability,
            on_track=on_track,
            gap_analysis=gap_analysis,
            recommendations=[],  # Will be filled by recommendation engine
            forecast_path=forecast_path
        )
