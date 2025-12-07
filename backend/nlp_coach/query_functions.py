"""
Query Functions for Natural Language Coach

These functions are designed to be called by Claude's function calling API
to answer user questions about their financial data.
"""

from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from app.models import Transaction, Goal
from spending.aggregator import DataAggregator
from spending.subscription_detector import SubscriptionDetector
from goals.storage import get_goal_storage
from goals.forecaster import GoalForecaster
import pandas as pd


class QueryEngine:
    """
    Engine for executing natural language queries against transaction data
    """

    def __init__(self, transactions: List[Transaction], goals: List[Goal]):
        """
        Initialize the query engine with transaction and goal data

        Args:
            transactions: List of user transactions
            goals: List of user savings goals
        """
        self.transactions = transactions
        self.goals = goals
        self.aggregator = DataAggregator(transactions)
        self.aggregator.aggregate_all()

        # Create DataFrame for easier querying
        self.df = pd.DataFrame([
            {
                'transaction_id': t.transaction_id,
                'date': pd.to_datetime(t.date),
                'amount': abs(t.amount),  # Use absolute value for spending
                'merchant_name': t.merchant_name,
                'category': t.category[0] if isinstance(t.category, list) and t.category else 'OTHER',
                'is_income': t.amount > 0
            }
            for t in transactions
        ])

    def query_spending(
        self,
        merchant: Optional[str] = None,
        category: Optional[str] = None,
        time_range: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Query total spending filtered by merchant, category, and/or time range.

        Args:
            merchant: Merchant name (will be fuzzy matched)
            category: Spending category (e.g., "DINING", "GROCERIES")
            time_range: Predefined time range - "this_month", "last_month", "this_year",
                       "last_year", "last_30_days", "last_90_days", "all_time"
            start_date: Custom start date in ISO format (e.g., "2025-07-13")
            end_date: Custom end date in ISO format (e.g., "2025-08-27")

        Returns:
            Dict containing:
                - total_amount: Total spending amount
                - transaction_count: Number of transactions
                - average_amount: Average transaction amount
                - time_period: Description of time period
                - comparison_to_average: % difference from average (if applicable)
        """
        # Start with spending transactions only
        df = self.df[~self.df['is_income']].copy()

        # Apply filters
        if merchant:
            # Case-insensitive partial match
            df = df[df['merchant_name'].str.contains(merchant, case=False, na=False)]

        if category:
            # Case-insensitive exact match
            df = df[df['category'].str.upper() == category.upper()]

        # Apply time range filter
        if start_date and end_date:
            # Use custom date range
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        elif time_range:
            # Use predefined time range
            start, end = self._parse_time_range(time_range)
            if start and end:
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = self._format_time_period(time_range, start, end)
        else:
            time_period_desc = "All time"

        # Calculate metrics
        total_amount = float(df['amount'].sum())
        transaction_count = len(df)
        average_amount = float(df['amount'].mean()) if transaction_count > 0 else 0.0

        # Calculate comparison to average (overall or category average)
        comparison_pct = None
        if time_range and time_range not in ['all_time']:
            # Compare to overall average for this filter
            overall_df = self.df[~self.df['is_income']].copy()
            if merchant:
                overall_df = overall_df[overall_df['merchant_name'].str.contains(merchant, case=False, na=False)]
            if category:
                overall_df = overall_df[overall_df['category'].str.upper() == category.upper()]

            overall_avg = float(overall_df['amount'].mean()) if len(overall_df) > 0 else 0.0
            if overall_avg > 0:
                comparison_pct = ((average_amount - overall_avg) / overall_avg) * 100

        return {
            'total_amount': round(total_amount, 2),
            'transaction_count': transaction_count,
            'average_amount': round(average_amount, 2),
            'time_period': time_period_desc,
            'comparison_to_average': round(comparison_pct, 1) if comparison_pct is not None else None
        }

    def get_top_merchants(
        self,
        time_range: Optional[str] = None,
        top_n: int = 5,
        category_filter: Optional[str] = None,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get top merchants by spending amount.

        Args:
            time_range: Predefined time range filter
            top_n: Number of top merchants to return (default: 5)
            category_filter: Optional category filter
            start_date: Custom start date in ISO format
            end_date: Custom end date in ISO format

        Returns:
            Dict containing:
                - merchants: List of top merchants with amounts and percentages
                - total_spending: Total spending in this period
                - time_period: Description of time period
        """
        df = self.df[~self.df['is_income']].copy()

        # Apply category filter
        if category_filter:
            df = df[df['category'].str.upper() == category_filter.upper()]

        # Apply time range filter
        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        elif time_range:
            start, end = self._parse_time_range(time_range)
            if start and end:
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = self._format_time_period(time_range, start, end)
        else:
            time_period_desc = "All time"

        # Group by merchant and calculate totals
        merchant_totals = df.groupby('merchant_name')['amount'].agg(['sum', 'count']).reset_index()
        merchant_totals.columns = ['merchant', 'total', 'count']
        merchant_totals = merchant_totals.sort_values('total', ascending=False).head(top_n)

        total_spending = float(df['amount'].sum())

        merchants = []
        for _, row in merchant_totals.iterrows():
            merchants.append({
                'merchant': row['merchant'],
                'amount': round(float(row['total']), 2),
                'transaction_count': int(row['count']),
                'percentage': round((float(row['total']) / total_spending * 100), 1) if total_spending > 0 else 0
            })

        return {
            'merchants': merchants,
            'total_spending': round(total_spending, 2),
            'time_period': time_period_desc
        }

    def get_top_categories(
        self,
        time_range: Optional[str] = None,
        top_n: int = 5,
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get top categories by spending amount.

        Args:
            time_range: Time range filter
            top_n: Number of top categories to return (default: 5)

        Returns:
            Dict containing:
                - categories: List of top categories with amounts and percentages
                - total_spending: Total spending in this period
                - time_period: Description of time period
        """
        df = self.df[~self.df['is_income']].copy()

        # Apply time range filter
        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        elif time_range:
            start, end = self._parse_time_range(time_range)
            if start and end:
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = self._format_time_period(time_range, start, end)
        else:
            time_period_desc = "All time"

        # Group by category and calculate totals
        category_totals = df.groupby('category')['amount'].agg(['sum', 'count']).reset_index()
        category_totals.columns = ['category', 'total', 'count']
        category_totals = category_totals.sort_values('total', ascending=False).head(top_n)

        total_spending = float(df['amount'].sum())

        categories = []
        for _, row in category_totals.iterrows():
            categories.append({
                'category': row['category'],
                'amount': round(float(row['total']), 2),
                'transaction_count': int(row['count']),
                'percentage': round((float(row['total']) / total_spending * 100), 1) if total_spending > 0 else 0
            })

        return {
            'categories': categories,
            'total_spending': round(total_spending, 2),
            'time_period': time_period_desc
        }

    def compare_spending(
        self,
        period1: str,
        period2: str,
        merchant_filter: Optional[str] = None,
        category_filter: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Compare spending between two time periods.

        Args:
            period1: First time period (e.g., "this_month")
            period2: Second time period (e.g., "last_month")
            merchant_filter: Optional merchant filter
            category_filter: Optional category filter

        Returns:
            Dict containing:
                - period1_amount: Spending in first period
                - period2_amount: Spending in second period
                - dollar_change: Dollar difference
                - percent_change: Percentage change
                - period1_desc: Description of period 1
                - period2_desc: Description of period 2
        """
        # Get spending for period 1
        start1, end1 = self._parse_time_range(period1)
        df1 = self.df[~self.df['is_income']].copy()
        if start1 and end1:
            df1 = df1[(df1['date'] >= start1) & (df1['date'] <= end1)]
        if merchant_filter:
            df1 = df1[df1['merchant_name'].str.contains(merchant_filter, case=False, na=False)]
        if category_filter:
            df1 = df1[df1['category'].str.upper() == category_filter.upper()]
        period1_amount = float(df1['amount'].sum())

        # Get spending for period 2
        start2, end2 = self._parse_time_range(period2)
        df2 = self.df[~self.df['is_income']].copy()
        if start2 and end2:
            df2 = df2[(df2['date'] >= start2) & (df2['date'] <= end2)]
        if merchant_filter:
            df2 = df2[df2['merchant_name'].str.contains(merchant_filter, case=False, na=False)]
        if category_filter:
            df2 = df2[df2['category'].str.upper() == category_filter.upper()]
        period2_amount = float(df2['amount'].sum())

        # Calculate changes
        dollar_change = period1_amount - period2_amount
        percent_change = ((period1_amount - period2_amount) / period2_amount * 100) if period2_amount > 0 else 0

        return {
            'period1_amount': round(period1_amount, 2),
            'period2_amount': round(period2_amount, 2),
            'dollar_change': round(dollar_change, 2),
            'percent_change': round(percent_change, 1),
            'period1_desc': self._format_time_period(period1, start1, end1),
            'period2_desc': self._format_time_period(period2, start2, end2)
        }

    def get_subscriptions(self) -> Dict[str, Any]:
        """
        Get all detected subscriptions with their details.

        Returns:
            Dict containing:
                - total_subscriptions: Count of subscriptions
                - total_monthly_cost: Total monthly cost
                - subscriptions: List of subscriptions
                - gray_charges: Count of gray charges
                - price_increases: Count of price increases
        """
        detector = SubscriptionDetector(self.transactions)
        summary = detector.detect_subscriptions()

        subscriptions = []
        for sub in summary.subscriptions:
            subscriptions.append({
                'merchant': sub.merchant_name,
                'frequency': sub.frequency,
                'current_amount': round(sub.current_amount, 2),
                'monthly_cost': round(sub.monthly_cost, 2),
                'annual_cost': round(sub.annual_cost, 2),
                'is_gray_charge': sub.is_gray_charge,
                'has_price_increase': sub.has_price_increase,
                'needs_attention': sub.needs_attention
            })

        return {
            'total_subscriptions': summary.total_subscriptions,
            'total_monthly_cost': round(summary.total_monthly_cost, 2),
            'total_annual_cost': round(summary.total_annual_cost, 2),
            'subscriptions': subscriptions,
            'gray_charges': summary.gray_charges_count,
            'price_increases': summary.price_increases_count
        }

    def get_goal_progress(self) -> Dict[str, Any]:
        """
        Get progress on all active savings goals.

        Returns:
            Dict containing:
                - total_goals: Number of active goals
                - goals: List of goals with progress information
        """
        goals_list = []

        for goal in self.goals:
            if not goal.is_active:
                continue

            # Calculate simple progress
            progress_pct = (goal.current_savings / goal.target_amount * 100) if goal.target_amount > 0 else 0

            # Parse deadline
            deadline_date = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
            days_remaining = (deadline_date - datetime.now()).days

            goals_list.append({
                'goal_name': goal.goal_name,
                'target_amount': round(goal.target_amount, 2),
                'current_savings': round(goal.current_savings, 2),
                'progress_percent': round(progress_pct, 1),
                'deadline': goal.deadline,
                'days_remaining': days_remaining,
                'priority_level': goal.priority_level
            })

        return {
            'total_goals': len(goals_list),
            'goals': goals_list
        }

    def get_transaction_details(
        self,
        search_type: str = "recent",
        merchant_keyword: Optional[str] = None,
        limit: int = 10
    ) -> Dict[str, Any]:
        """
        Get specific transaction details.

        Args:
            search_type: Type of search - "recent", "largest", or "search"
            merchant_keyword: Keyword to search in merchant names (for search_type="search")
            limit: Number of transactions to return (default: 10)

        Returns:
            Dict containing:
                - transactions: List of matching transactions
                - count: Number of transactions found
        """
        df = self.df[~self.df['is_income']].copy()

        if search_type == "recent":
            df = df.sort_values('date', ascending=False).head(limit)
        elif search_type == "largest":
            df = df.sort_values('amount', ascending=False).head(limit)
        elif search_type == "search" and merchant_keyword:
            df = df[df['merchant_name'].str.contains(merchant_keyword, case=False, na=False)]
            df = df.sort_values('date', ascending=False).head(limit)

        transactions = []
        for _, row in df.iterrows():
            transactions.append({
                'date': row['date'].strftime('%Y-%m-%d'),
                'merchant': row['merchant_name'],
                'amount': round(float(row['amount']), 2),
                'category': row['category']
            })

        return {
            'transactions': transactions,
            'count': len(transactions)
        }

    def get_financial_summary(
        self,
        time_range: Optional[str] = "this_month",
        start_date: Optional[str] = None,
        end_date: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get holistic financial overview for a time period.

        Args:
            time_range: Time period to analyze

        Returns:
            Dict containing:
                - total_income: Total income
                - total_spending: Total spending
                - net_savings: Income - Spending
                - savings_rate: Percentage of income saved
                - category_breakdown: Top spending categories
                - time_period: Description of time period
        """
        # Filter by date range
        df = self.df.copy()

        if start_date and end_date:
            start = pd.to_datetime(start_date)
            end = pd.to_datetime(end_date)
            df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"
        elif time_range:
            start, end = self._parse_time_range(time_range)
            if start and end:
                df = df[(df['date'] >= start) & (df['date'] <= end)]
            time_period_desc = self._format_time_period(time_range, start, end)
        else:
            time_period_desc = "All time"

        # Calculate income and spending
        total_income = float(df[df['is_income']]['amount'].sum())
        total_spending = float(df[~df['is_income']]['amount'].sum())
        net_savings = total_income - total_spending
        savings_rate = (net_savings / total_income * 100) if total_income > 0 else 0

        # Category breakdown
        spending_df = df[~df['is_income']].copy()
        category_totals = spending_df.groupby('category')['amount'].sum().sort_values(ascending=False).head(5)

        category_breakdown = []
        for category, amount in category_totals.items():
            category_breakdown.append({
                'category': category,
                'amount': round(float(amount), 2),
                'percentage': round((float(amount) / total_spending * 100), 1) if total_spending > 0 else 0
            })

        return {
            'total_income': round(total_income, 2),
            'total_spending': round(total_spending, 2),
            'net_savings': round(net_savings, 2),
            'savings_rate': round(savings_rate, 1),
            'category_breakdown': category_breakdown,
            'time_period': time_period_desc
        }

    def _parse_time_range(self, time_range: Optional[str]) -> tuple:
        """
        Parse time range string into start and end dates.

        Args:
            time_range: Time range string

        Returns:
            Tuple of (start_date, end_date)
        """
        if not time_range or time_range == "all_time":
            return None, None

        # Use the latest transaction date as "today" for historical data
        if len(self.df) > 0:
            today = self.df['date'].max()
        else:
            today = pd.Timestamp.now()

        if time_range == "this_month":
            start = today.replace(day=1)
            end = today
        elif time_range == "last_month":
            # Go to first of this month, then back one day to get last month
            first_of_this_month = today.replace(day=1)
            end = first_of_this_month - timedelta(days=1)
            start = end.replace(day=1)
        elif time_range == "this_year":
            start = today.replace(month=1, day=1)
            end = today
        elif time_range == "last_year":
            start = today.replace(year=today.year - 1, month=1, day=1)
            end = today.replace(year=today.year - 1, month=12, day=31)
        elif time_range == "last_30_days":
            start = today - timedelta(days=30)
            end = today
        elif time_range == "last_90_days":
            start = today - timedelta(days=90)
            end = today
        else:
            return None, None

        return start, end

    def _format_time_period(self, time_range: Optional[str], start: Optional[pd.Timestamp], end: Optional[pd.Timestamp]) -> str:
        """Format time period for display"""
        if not time_range or time_range == "all_time":
            return "All time"

        if start and end:
            return f"{start.strftime('%b %d, %Y')} - {end.strftime('%b %d, %Y')}"

        return time_range.replace('_', ' ').title()
