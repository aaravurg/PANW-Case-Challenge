import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict, List
from models import AggregatedStats, Transaction
import json


class DataAggregator:
    """Stage 1: Aggregates transaction data for insight generation"""

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """Convert transactions to pandas DataFrame"""
        data = []
        for t in self.transactions:
            # Parse categories from JSON string if needed
            categories = t.category if isinstance(t.category, list) else json.loads(t.category)
            data.append({
                'transaction_id': t.transaction_id,
                'date': t.date,
                'amount': t.amount,
                'merchant_name': t.merchant_name,
                'category': categories[0] if categories else 'Other',  # Use primary category
                'payment_channel': t.payment_channel,
                'pending': t.pending
            })

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['day_of_week'] = df['date'].dt.day_name()
        df['is_weekend'] = df['date'].dt.dayofweek >= 5
        df['month'] = df['date'].dt.to_period('M')

        return df

    def aggregate(self) -> AggregatedStats:
        """Compute all aggregated statistics"""

        # Get current date range
        today = datetime.now()
        current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        last_month_start = (current_month_start - timedelta(days=1)).replace(day=1)
        last_month_end = current_month_start - timedelta(days=1)
        three_months_ago = (current_month_start - timedelta(days=90))

        # Filter data
        current_month_df = self.df[self.df['date'] >= current_month_start]
        last_month_df = self.df[(self.df['date'] >= last_month_start) & (self.df['date'] <= last_month_end)]
        three_month_df = self.df[self.df['date'] >= three_months_ago]

        # Separate income (positive) and spending (negative)
        current_spending_df = current_month_df[current_month_df['amount'] < 0].copy()
        current_income_df = current_month_df[current_month_df['amount'] > 0].copy()
        last_spending_df = last_month_df[last_month_df['amount'] < 0].copy()
        three_month_spending_df = three_month_df[three_month_df['amount'] < 0].copy()

        # Convert amounts to positive for spending calculations
        current_spending_df['abs_amount'] = current_spending_df['amount'].abs()
        last_spending_df['abs_amount'] = last_spending_df['amount'].abs()
        three_month_spending_df['abs_amount'] = three_month_spending_df['amount'].abs()

        # Aggregate by category
        spending_by_category_this_month = current_spending_df.groupby('category')['abs_amount'].sum().to_dict()
        spending_by_category_last_month = last_spending_df.groupby('category')['abs_amount'].sum().to_dict()

        # 3-month average
        category_3mo = three_month_spending_df.groupby(['category', 'month'])['abs_amount'].sum().reset_index()
        spending_by_category_3mo_average = category_3mo.groupby('category')['abs_amount'].mean().to_dict()

        # Aggregate by merchant
        spending_by_merchant_this_month = current_spending_df.groupby('merchant_name')['abs_amount'].sum().to_dict()

        # Aggregate by day of week
        spending_by_day_of_week = current_spending_df.groupby('day_of_week')['abs_amount'].sum().to_dict()

        # Totals
        total_income_this_month = current_income_df['amount'].sum()
        total_spending_this_month = current_spending_df['abs_amount'].sum()
        total_spending_last_month = last_spending_df['abs_amount'].sum()

        return AggregatedStats(
            spending_by_category_this_month=spending_by_category_this_month,
            spending_by_category_last_month=spending_by_category_last_month,
            spending_by_category_3mo_average=spending_by_category_3mo_average,
            spending_by_merchant_this_month=spending_by_merchant_this_month,
            spending_by_day_of_week=spending_by_day_of_week,
            total_income_this_month=total_income_this_month,
            total_spending_this_month=total_spending_this_month,
            total_spending_last_month=total_spending_last_month
        )

    def get_merchant_visit_counts(self) -> Dict[str, int]:
        """Get visit counts per merchant for current month"""
        today = datetime.now()
        current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_df = self.df[self.df['date'] >= current_month_start]

        return current_month_df.groupby('merchant_name').size().to_dict()

    def get_weekend_vs_weekday_spending(self) -> Dict[str, float]:
        """Calculate weekend vs weekday spending"""
        today = datetime.now()
        current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_df = self.df[(self.df['date'] >= current_month_start) & (self.df['amount'] < 0)]

        weekend_spend = current_month_df[current_month_df['is_weekend']]['amount'].abs().sum()
        weekday_spend = current_month_df[~current_month_df['is_weekend']]['amount'].abs().sum()

        return {
            'weekend': weekend_spend,
            'weekday': weekday_spend
        }

    def get_top_merchants_for_category(self, category: str, limit: int = 3) -> List[str]:
        """Get top merchants for a specific category"""
        today = datetime.now()
        current_month_start = today.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        current_month_df = self.df[(self.df['date'] >= current_month_start) & (self.df['category'] == category)]

        top_merchants = current_month_df.groupby('merchant_name')['amount'].sum().abs().nlargest(limit)
        return top_merchants.index.tolist()
