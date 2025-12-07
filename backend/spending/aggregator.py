import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from app.models import Transaction
import json
import re


class DataAggregator:
    """
    Stage 1: Comprehensive data preparation with multi-dimensional aggregation
    Analyzes complete transaction history across all time dimensions
    """

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._create_dataframe()
        self.aggregations = {}
        self.derived_metrics = {}

    def _create_dataframe(self) -> pd.DataFrame:
        """Convert transactions to pandas DataFrame with comprehensive date features"""
        data = []
        for t in self.transactions:
            # Parse categories
            categories = t.category if isinstance(t.category, list) else json.loads(t.category)
            primary_category = categories[0] if categories else 'OTHER'

            # Normalize merchant name
            merchant = self._normalize_merchant(t.merchant_name)

            data.append({
                'transaction_id': t.transaction_id,
                'date': t.date,
                'amount': t.amount,
                'merchant_name': merchant,
                'category': primary_category,
                'payment_channel': t.payment_channel,
                'pending': t.pending
            })

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])

        # Add comprehensive date features
        df['year'] = df['date'].dt.year
        df['quarter'] = df['date'].dt.quarter
        df['month'] = df['date'].dt.month
        df['week'] = df['date'].dt.isocalendar().week
        df['day_of_week'] = df['date'].dt.dayofweek
        df['day_name'] = df['date'].dt.day_name()
        df['is_weekend'] = df['date'].dt.dayofweek >= 5

        # Create period keys for aggregation
        df['year_key'] = df['date'].dt.year.astype(str)
        df['quarter_key'] = df['date'].dt.year.astype(str) + '-Q' + df['date'].dt.quarter.astype(str)
        df['month_key'] = df['date'].dt.to_period('M').astype(str)
        df['week_key'] = df['date'].dt.year.astype(str) + '-W' + df['date'].dt.isocalendar().week.astype(str).str.zfill(2)

        # Separate income and expenses
        df['is_income'] = df['amount'] > 0
        df['abs_amount'] = df['amount'].abs()

        return df

    def _normalize_merchant(self, merchant: str) -> str:
        """Clean and normalize merchant names"""
        if not merchant:
            return "UNKNOWN"

        # Remove common suffixes
        merchant = re.sub(r'\s+(INC|LLC|LTD|CORP|CO|LP)\.?$', '', merchant, flags=re.IGNORECASE)

        # Remove special characters
        merchant = re.sub(r'[^\w\s]', '', merchant)

        # Common merchant normalizations
        normalizations = {
            'AMZN': 'Amazon',
            'AMZ': 'Amazon',
            'AMAZON COM': 'Amazon',
            'STARBUCKS': 'Starbucks',
            'SBX': 'Starbucks',
            'MCDONALDS': 'McDonalds',
            'MCD': 'McDonalds',
            'TARGET': 'Target',
            'TGT': 'Target',
            'WALMART': 'Walmart',
            'WMT': 'Walmart'
        }

        merchant_upper = merchant.upper().strip()
        for key, value in normalizations.items():
            if key in merchant_upper:
                return value

        return merchant.strip().title()

    def aggregate_all(self) -> Dict:
        """Run all aggregations and compute derived metrics"""

        # Multi-dimensional aggregations
        self.aggregations['by_week'] = self._aggregate_by_week()
        self.aggregations['by_month'] = self._aggregate_by_month()
        self.aggregations['by_quarter'] = self._aggregate_by_quarter()
        self.aggregations['by_year'] = self._aggregate_by_year()
        self.aggregations['by_day_of_week'] = self._aggregate_by_day_of_week()
        self.aggregations['by_month_number'] = self._aggregate_by_month_number()
        self.aggregations['by_merchant'] = self._aggregate_by_merchant()
        self.aggregations['by_category'] = self._aggregate_by_category()

        # Compute derived metrics
        self._compute_derived_metrics()

        return {
            'aggregations': self.aggregations,
            'derived_metrics': self.derived_metrics
        }

    def _aggregate_by_week(self) -> Dict:
        """Aggregate by ISO week"""
        spending_df = self.df[~self.df['is_income']].copy()

        weekly = spending_df.groupby('week_key').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={'abs_amount': 'total_spending', 'transaction_id': 'transaction_count'})

        # Category breakdown per week
        weekly_category = spending_df.groupby(['week_key', 'category'])['abs_amount'].sum().unstack(fill_value=0)

        # Merchant breakdown per week
        weekly_merchant = spending_df.groupby(['week_key', 'merchant_name'])['abs_amount'].sum().unstack(fill_value=0)

        return {
            'totals': weekly.to_dict('index'),
            'by_category': weekly_category.to_dict('index'),
            'by_merchant': weekly_merchant.to_dict('index'),
            'sorted_keys': sorted(weekly.index.tolist())
        }

    def _aggregate_by_month(self) -> Dict:
        """Aggregate by calendar month"""
        spending_df = self.df[~self.df['is_income']].copy()
        income_df = self.df[self.df['is_income']].copy()

        monthly_spending = spending_df.groupby('month_key').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={'abs_amount': 'total_spending', 'transaction_id': 'transaction_count'})

        monthly_income = income_df.groupby('month_key')['abs_amount'].sum()

        # Category breakdown per month
        monthly_category = spending_df.groupby(['month_key', 'category'])['abs_amount'].sum().unstack(fill_value=0)

        # Merchant breakdown per month
        monthly_merchant = spending_df.groupby(['month_key', 'merchant_name'])['abs_amount'].sum().unstack(fill_value=0)

        return {
            'totals': monthly_spending.to_dict('index'),
            'income': monthly_income.to_dict(),
            'by_category': monthly_category.to_dict('index'),
            'by_merchant': monthly_merchant.to_dict('index'),
            'sorted_keys': sorted(monthly_spending.index.tolist())
        }

    def _aggregate_by_quarter(self) -> Dict:
        """Aggregate by fiscal quarter"""
        spending_df = self.df[~self.df['is_income']].copy()

        quarterly = spending_df.groupby('quarter_key').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={'abs_amount': 'total_spending', 'transaction_id': 'transaction_count'})

        # Category breakdown per quarter
        quarterly_category = spending_df.groupby(['quarter_key', 'category'])['abs_amount'].sum().unstack(fill_value=0)

        return {
            'totals': quarterly.to_dict('index'),
            'by_category': quarterly_category.to_dict('index'),
            'sorted_keys': sorted(quarterly.index.tolist())
        }

    def _aggregate_by_year(self) -> Dict:
        """Aggregate by calendar year"""
        spending_df = self.df[~self.df['is_income']].copy()

        yearly = spending_df.groupby('year_key').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={'abs_amount': 'total_spending', 'transaction_id': 'transaction_count'})

        # Category breakdown per year
        yearly_category = spending_df.groupby(['year_key', 'category'])['abs_amount'].sum().unstack(fill_value=0)

        return {
            'totals': yearly.to_dict('index'),
            'by_category': yearly_category.to_dict('index'),
            'sorted_keys': sorted(yearly.index.tolist())
        }

    def _aggregate_by_day_of_week(self) -> Dict:
        """Aggregate by day of week across all history"""
        spending_df = self.df[~self.df['is_income']].copy()

        by_day = spending_df.groupby('day_name')['abs_amount'].sum().to_dict()

        # Weekend vs weekday totals
        weekend_total = spending_df[spending_df['is_weekend']]['abs_amount'].sum()
        weekday_total = spending_df[~spending_df['is_weekend']]['abs_amount'].sum()

        # Count of weekends and weekdays for daily averages
        num_weeks = len(self.df['week_key'].unique())
        weekend_daily_avg = weekend_total / (num_weeks * 2) if num_weeks > 0 else 0
        weekday_daily_avg = weekday_total / (num_weeks * 5) if num_weeks > 0 else 0

        return {
            'by_day': by_day,
            'weekend_total': weekend_total,
            'weekday_total': weekday_total,
            'weekend_daily_avg': weekend_daily_avg,
            'weekday_daily_avg': weekday_daily_avg
        }

    def _aggregate_by_month_number(self) -> Dict:
        """Aggregate by month number (1-12) across all years for seasonal patterns"""
        spending_df = self.df[~self.df['is_income']].copy()

        seasonal = spending_df.groupby('month')['abs_amount'].sum().to_dict()

        return seasonal

    def _aggregate_by_merchant(self) -> Dict:
        """Aggregate lifetime spending per merchant"""
        spending_df = self.df[~self.df['is_income']].copy()

        merchant_totals = spending_df.groupby('merchant_name').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count',
            'date': ['min', 'max']
        })

        merchant_totals.columns = ['total_spending', 'transaction_count', 'first_transaction', 'last_transaction']

        return merchant_totals.to_dict('index')

    def _aggregate_by_category(self) -> Dict:
        """Aggregate lifetime spending per category"""
        spending_df = self.df[~self.df['is_income']].copy()

        category_totals = spending_df.groupby('category').agg({
            'abs_amount': 'sum',
            'transaction_id': 'count'
        }).rename(columns={'abs_amount': 'total_spending', 'transaction_id': 'transaction_count'})

        return category_totals.to_dict('index')

    def _compute_derived_metrics(self):
        """Compute derived metrics from aggregations"""

        # Account age
        if len(self.df) > 0:
            earliest_date = self.df['date'].min()
            latest_date = self.df['date'].max()
            self.derived_metrics['earliest_transaction'] = earliest_date
            self.derived_metrics['latest_transaction'] = latest_date
            self.derived_metrics['account_age_days'] = (latest_date - earliest_date).days
            self.derived_metrics['account_age_months'] = max(1, len(self.aggregations['by_month']['sorted_keys']))

        # Overall monthly average
        total_spending = self.df[~self.df['is_income']]['abs_amount'].sum()
        num_months = self.derived_metrics.get('account_age_months', 1)
        self.derived_metrics['overall_monthly_avg'] = total_spending / num_months if num_months > 0 else 0

        # Category monthly averages
        category_monthly_avgs = {}
        for category, data in self.aggregations['by_category'].items():
            category_monthly_avgs[category] = data['total_spending'] / num_months if num_months > 0 else 0
        self.derived_metrics['category_monthly_averages'] = category_monthly_avgs

        # Current period identifiers (using rolling 30-day windows)
        # Use the latest transaction date instead of datetime.now() to work correctly with historical data
        if len(self.df) > 0:
            # Convert pandas Timestamp to datetime if needed
            today = latest_date.to_pydatetime() if hasattr(latest_date, 'to_pydatetime') else latest_date
        else:
            today = datetime.now()
        self.derived_metrics['current_year'] = str(today.year)
        self.derived_metrics['current_quarter'] = f"{today.year}-Q{(today.month - 1) // 3 + 1}"
        self.derived_metrics['current_week'] = f"{today.year}-W{today.isocalendar()[1]:02d}"

        # Rolling month periods (30 days)
        self.derived_metrics['current_month_start'] = today - timedelta(days=30)
        self.derived_metrics['current_month_end'] = today
        self.derived_metrics['previous_month_start'] = today - timedelta(days=60)
        self.derived_metrics['previous_month_end'] = today - timedelta(days=30)

        # For backward compatibility with calendar month keys
        self.derived_metrics['current_month'] = pd.Period(today, freq='M').strftime('%Y-%m')
        prev_month = today.replace(day=1) - timedelta(days=1)
        self.derived_metrics['previous_month'] = pd.Period(prev_month, freq='M').strftime('%Y-%m')

        prev_year = today.year - 1
        self.derived_metrics['previous_year'] = str(prev_year)
        self.derived_metrics['same_month_last_year'] = f"{prev_year}-{today.month:02d}"

        # Rolling period for year-over-year comparison (same 30-day period from last year)
        self.derived_metrics['yoy_current_start'] = today - timedelta(days=30)
        self.derived_metrics['yoy_current_end'] = today
        self.derived_metrics['yoy_previous_start'] = today - timedelta(days=365) - timedelta(days=30)
        self.derived_metrics['yoy_previous_end'] = today - timedelta(days=365)

    def get_current_vs_previous_period(self, period_type: str) -> Tuple[float, float]:
        """Get current and previous period spending totals"""

        if period_type == 'month':
            current_key = self.derived_metrics.get('current_month')
            previous_key = self.derived_metrics.get('previous_month')
            data = self.aggregations['by_month']['totals']
        elif period_type == 'week':
            current_key = self.derived_metrics.get('current_week')
            sorted_keys = self.aggregations['by_week']['sorted_keys']
            current_idx = sorted_keys.index(current_key) if current_key in sorted_keys else -1
            previous_key = sorted_keys[current_idx - 1] if current_idx > 0 else None
            data = self.aggregations['by_week']['totals']
        elif period_type == 'quarter':
            current_key = self.derived_metrics.get('current_quarter')
            sorted_keys = self.aggregations['by_quarter']['sorted_keys']
            current_idx = sorted_keys.index(current_key) if current_key in sorted_keys else -1
            previous_key = sorted_keys[current_idx - 1] if current_idx > 0 else None
            data = self.aggregations['by_quarter']['totals']
        else:
            return 0, 0

        current_total = data.get(current_key, {}).get('total_spending', 0) if current_key else 0
        previous_total = data.get(previous_key, {}).get('total_spending', 0) if previous_key else 0

        return current_total, previous_total

    def get_rolling_30day_totals(self) -> Dict:
        """Get spending totals for current and previous 30-day rolling periods"""

        current_start = self.derived_metrics.get('current_month_start')
        current_end = self.derived_metrics.get('current_month_end')
        previous_start = self.derived_metrics.get('previous_month_start')
        previous_end = self.derived_metrics.get('previous_month_end')

        # Filter for current 30-day period
        current_df = self.df[
            (self.df['date'] >= current_start) &
            (self.df['date'] <= current_end) &
            (~self.df['is_income'])
        ]

        # Filter for previous 30-day period
        previous_df = self.df[
            (self.df['date'] >= previous_start) &
            (self.df['date'] <= previous_end) &
            (~self.df['is_income'])
        ]

        # Calculate totals
        current_total = current_df['abs_amount'].sum()
        previous_total = previous_df['abs_amount'].sum()

        # Category breakdowns
        current_by_category = current_df.groupby('category')['abs_amount'].sum().to_dict()
        previous_by_category = previous_df.groupby('category')['abs_amount'].sum().to_dict()

        # Merchant breakdowns
        current_by_merchant = current_df.groupby('merchant_name')['abs_amount'].sum().to_dict()

        # Income
        current_income_df = self.df[
            (self.df['date'] >= current_start) &
            (self.df['date'] <= current_end) &
            (self.df['is_income'])
        ]
        current_income = current_income_df['abs_amount'].sum()

        return {
            'current_total': current_total,
            'previous_total': previous_total,
            'current_by_category': current_by_category,
            'previous_by_category': previous_by_category,
            'current_by_merchant': current_by_merchant,
            'current_income': current_income,
            'current_start': current_start,
            'current_end': current_end,
            'previous_start': previous_start,
            'previous_end': previous_end
        }

    def get_yoy_rolling_totals(self) -> Dict:
        """Get spending totals for current and year-ago 30-day rolling periods"""

        yoy_current_start = self.derived_metrics.get('yoy_current_start')
        yoy_current_end = self.derived_metrics.get('yoy_current_end')
        yoy_previous_start = self.derived_metrics.get('yoy_previous_start')
        yoy_previous_end = self.derived_metrics.get('yoy_previous_end')

        # Filter for current 30-day period
        current_df = self.df[
            (self.df['date'] >= yoy_current_start) &
            (self.df['date'] <= yoy_current_end) &
            (~self.df['is_income'])
        ]

        # Filter for same 30-day period last year
        previous_df = self.df[
            (self.df['date'] >= yoy_previous_start) &
            (self.df['date'] <= yoy_previous_end) &
            (~self.df['is_income'])
        ]

        # Calculate totals
        current_total = current_df['abs_amount'].sum()
        previous_total = previous_df['abs_amount'].sum()

        # Category breakdowns
        current_by_category = current_df.groupby('category')['abs_amount'].sum().to_dict()
        previous_by_category = previous_df.groupby('category')['abs_amount'].sum().to_dict()

        return {
            'current_total': current_total,
            'previous_total': previous_total,
            'current_by_category': current_by_category,
            'previous_by_category': previous_by_category,
            'current_start': yoy_current_start,
            'current_end': yoy_current_end,
            'previous_start': yoy_previous_start,
            'previous_end': yoy_previous_end
        }

    def get_rolling_trend(self, period_type: str, window_months: int = 6) -> Dict:
        """Calculate rolling period trends using linear regression"""

        sorted_keys = self.aggregations['by_month']['sorted_keys']
        if len(sorted_keys) < window_months:
            return {'has_data': False}

        # Get last N months
        recent_keys = sorted_keys[-window_months:]
        recent_totals = [
            self.aggregations['by_month']['totals'].get(key, {}).get('total_spending', 0)
            for key in recent_keys
        ]

        # Linear regression
        x = np.arange(len(recent_totals))
        y = np.array(recent_totals)

        if len(x) < 2:
            return {'has_data': False}

        # Calculate slope
        slope, intercept = np.polyfit(x, y, 1)

        # Calculate percentage change between first half and second half
        mid_point = len(recent_totals) // 2
        first_half_avg = np.mean(recent_totals[:mid_point])
        second_half_avg = np.mean(recent_totals[mid_point:])

        pct_change = 0
        if first_half_avg > 0:
            pct_change = ((second_half_avg - first_half_avg) / first_half_avg) * 100

        avg_spending = np.mean(recent_totals)

        return {
            'has_data': True,
            'slope': slope,
            'avg_spending': avg_spending,
            'slope_pct_of_avg': (slope / avg_spending * 100) if avg_spending > 0 else 0,
            'first_half_avg': first_half_avg,
            'second_half_avg': second_half_avg,
            'pct_change': pct_change,
            'window_months': window_months
        }
