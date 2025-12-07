from app.models import Trigger, InsightDetails, TransactionSummary
from typing import List
import pandas as pd


class InsightDetailsBuilder:
    """
    Builds detailed calculation breakdowns with actual transactions
    Shows users the exact transactions that were used in calculations
    """

    @staticmethod
    def build_details(trigger: Trigger, aggregator) -> InsightDetails:
        """Generate detailed breakdown with actual transactions"""

        # Get the relevant transactions based on trigger type
        transactions = InsightDetailsBuilder._get_relevant_transactions(trigger, aggregator)

        # Build the details based on trigger type
        method, raw_values, timeframe, context = InsightDetailsBuilder._get_insight_info(trigger)

        return InsightDetails(
            calculation_method=method,
            raw_values=raw_values,
            timeframe=timeframe,
            comparison_context=context,
            transactions=transactions
        )

    @staticmethod
    def _get_relevant_transactions(trigger: Trigger, aggregator) -> List[TransactionSummary]:
        """Extract the actual transactions used in this insight's calculation"""
        df = aggregator.df
        transactions = []

        # Filter based on trigger type
        if 'weekly' in trigger.type:
            # Get current week transactions
            week = trigger.raw_data.get('week') if trigger.raw_data else None
            if week:
                week_df = df[df['week_key'] == week].copy()
                if trigger.category:
                    week_df = week_df[week_df['category'] == trigger.category]
                transactions = InsightDetailsBuilder._df_to_transactions(week_df)

        elif 'monthly' in trigger.type or 'category_above_average' in trigger.type:
            # Get rolling 30-day period transactions
            is_rolling = trigger.raw_data and trigger.raw_data.get('rolling_period')
            if is_rolling and trigger.raw_data.get('current_start'):
                # Use the specific dates from the trigger, not global dates
                current_start = pd.to_datetime(trigger.raw_data.get('current_start'))
                current_end = pd.to_datetime(trigger.raw_data.get('current_end'))
                month_df = df[(df['date'] >= current_start) & (df['date'] <= current_end)].copy()
            else:
                # Fallback to calendar month
                current_month = aggregator.derived_metrics.get('current_month')
                month_df = df[df['month_key'] == current_month].copy()

            if trigger.category:
                month_df = month_df[month_df['category'] == trigger.category]
            transactions = InsightDetailsBuilder._df_to_transactions(month_df)

        elif 'year_over_year' in trigger.type:
            # Get rolling 30-day periods for YoY comparison
            is_rolling = trigger.raw_data and trigger.raw_data.get('rolling_period')
            if is_rolling and trigger.raw_data.get('yoy_current_start'):
                # Use the specific dates from the trigger, not global dates
                yoy_current_start = pd.to_datetime(trigger.raw_data.get('yoy_current_start'))
                yoy_current_end = pd.to_datetime(trigger.raw_data.get('yoy_current_end'))
                yoy_previous_start = pd.to_datetime(trigger.raw_data.get('yoy_previous_start'))
                yoy_previous_end = pd.to_datetime(trigger.raw_data.get('yoy_previous_end'))

                # Get transactions from both periods
                current_period_df = df[
                    (df['date'] >= yoy_current_start) & (df['date'] <= yoy_current_end)
                ].copy()
                previous_period_df = df[
                    (df['date'] >= yoy_previous_start) & (df['date'] <= yoy_previous_end)
                ].copy()

                combined_df = pd.concat([current_period_df, previous_period_df])
            else:
                # Fallback to calendar month
                current_month = aggregator.derived_metrics.get('current_month')
                same_month_last_year = aggregator.derived_metrics.get('same_month_last_year')
                combined_df = df[df['month_key'].isin([current_month, same_month_last_year])].copy()

            if trigger.category:
                combined_df = combined_df[combined_df['category'] == trigger.category]
            transactions = InsightDetailsBuilder._df_to_transactions(combined_df)

        elif 'merchant_lifetime_milestone' == trigger.type:
            # Get all transactions for this merchant (for milestone achievements)
            if trigger.merchant:
                merchant_df = df[df['merchant_name'] == trigger.merchant].copy()
                # Sort by date and get most recent 50 transactions to show milestone progress
                merchant_df = merchant_df.sort_values('date', ascending=False)
                transactions = InsightDetailsBuilder._df_to_transactions(merchant_df.head(50))
            else:
                transactions = []

        elif 'merchant' in trigger.type:
            # Get all transactions for this merchant
            if trigger.merchant:
                merchant_df = df[df['merchant_name'] == trigger.merchant].copy()
                # Sort by date and get most recent 30 transactions
                merchant_df = merchant_df.sort_values('date', ascending=False)
                transactions = InsightDetailsBuilder._df_to_transactions(merchant_df.head(30))
            else:
                transactions = []

        elif 'weekend' in trigger.type or 'weekday' in trigger.type:
            # Get weekend or weekday transactions
            if 'weekend' in trigger.type:
                filtered_df = df[df['is_weekend'] == True].copy()
            else:
                filtered_df = df[df['is_weekend'] == False].copy()
            # Sort by date and get most recent 50 transactions
            filtered_df = filtered_df.sort_values('date', ascending=False)
            transactions = InsightDetailsBuilder._df_to_transactions(filtered_df.head(50))

        elif 'category_dominance' in trigger.type:
            # Get all transactions for this dominant category
            cat_df = df[df['category'] == trigger.category].copy()
            # Sort by date and get most recent 50 transactions
            cat_df = cat_df.sort_values('date', ascending=False)
            transactions = InsightDetailsBuilder._df_to_transactions(cat_df.head(50))

        elif 'lifetime_spending_milestone' == trigger.type:
            # Get all transactions (for overall lifetime milestone)
            # Sort by date and get most recent 100 transactions to show overall spending
            all_df = df.copy()
            all_df = all_df.sort_values('date', ascending=False)
            transactions = InsightDetailsBuilder._df_to_transactions(all_df.head(100))

        elif 'all_time_high' in trigger.type or 'all_time_low' in trigger.type:
            # Get current month transactions
            current_month = aggregator.derived_metrics.get('current_month')
            if current_month:
                month_df = df[df['month_key'] == current_month].copy()
                if trigger.category:
                    month_df = month_df[month_df['category'] == trigger.category]
                transactions = InsightDetailsBuilder._df_to_transactions(month_df)

        elif 'savings_streak' in trigger.type or 'improvement' in trigger.type:
            # Get last 3-6 months of transactions
            months = trigger.raw_data.get('months', []) if trigger.raw_data else []
            if months:
                streak_df = df[df['month_key'].isin(months)].copy()
                if trigger.category:
                    streak_df = streak_df[streak_df['category'] == trigger.category]
                transactions = InsightDetailsBuilder._df_to_transactions(streak_df)

        elif 'rolling_trend' in trigger.type or 'quarterly' in trigger.type or 'sustained_trend' in trigger.type:
            # Get last 3-6 months
            # Prefer specific months from raw_data if available
            if trigger.raw_data and trigger.raw_data.get('months'):
                recent_months = trigger.raw_data['months']
            else:
                sorted_months = aggregator.aggregations['by_month']['sorted_keys']
                window = 6 if 'six_month' in trigger.type else 3 if 'three_month' in trigger.type else 3
                recent_months = sorted_months[-window:] if len(sorted_months) >= window else sorted_months

            trend_df = df[df['month_key'].isin(recent_months)].copy()
            if trigger.category:
                trend_df = trend_df[trend_df['category'] == trigger.category]
            transactions = InsightDetailsBuilder._df_to_transactions(trend_df)

        else:
            # Default: get recent transactions
            current_month = aggregator.derived_metrics.get('current_month')
            if current_month:
                month_df = df[df['month_key'] == current_month].copy()
                transactions = InsightDetailsBuilder._df_to_transactions(month_df.head(20))

        return transactions

    @staticmethod
    def _df_to_transactions(df: pd.DataFrame) -> List[TransactionSummary]:
        """Convert DataFrame rows to TransactionSummary objects"""
        transactions = []

        # Only include spending (negative amounts)
        spending_df = df[df['amount'] < 0].copy()

        # Sort by date descending
        spending_df = spending_df.sort_values('date', ascending=False)

        for _, row in spending_df.iterrows():
            transactions.append(TransactionSummary(
                date=row['date'].strftime('%Y-%m-%d'),
                merchant=row['merchant_name'],
                amount=abs(row['amount']),  # Convert to positive for display
                category=row['category']
            ))

        return transactions

    @staticmethod
    def _get_insight_info(trigger: Trigger) -> tuple:
        """Get method, raw values, timeframe, and context for the trigger"""

        if 'weekly_spending_spike' == trigger.type:
            return (
                "Week-over-Week Spending Increase",
                {
                    "current_week": trigger.this_month,
                    "previous_week": trigger.last_month,
                    "increase": trigger.dollar_change,
                    "percent_increase": trigger.percent_change
                },
                f"Comparing this week to last week",
                f"Your spending increased by ${trigger.dollar_change:.2f} ({trigger.percent_change:.1f}%) this week compared to last week."
            )

        elif 'monthly_spending_spike' == trigger.type:
            date_range = trigger.raw_data.get('date_range', 'this month') if trigger.raw_data else 'this month'
            return (
                "Month-over-Month Spending Increase (30-Day Rolling Period)",
                {
                    "current_period": trigger.this_month,
                    "previous_period": trigger.last_month,
                    "increase": trigger.dollar_change,
                    "percent_increase": trigger.percent_change
                },
                f"Last 30 days ({date_range}) vs previous 30 days",
                f"Your spending increased by ${trigger.dollar_change:.2f} ({trigger.percent_change:.1f}%) in the last 30 days compared to the prior 30 days. These are all transactions from the current 30-day period."
            )

        elif 'monthly_spending_win' == trigger.type:
            date_range = trigger.raw_data.get('date_range', 'this month') if trigger.raw_data else 'this month'
            return (
                "Month-over-Month Spending Decrease (30-Day Rolling Period)",
                {
                    "current_period": trigger.this_month,
                    "previous_period": trigger.last_month,
                    "savings": trigger.dollar_change,
                    "percent_decrease": trigger.percent_change
                },
                f"Last 30 days ({date_range}) vs previous 30 days",
                f"You saved ${trigger.dollar_change:.2f} ({trigger.percent_change:.1f}%) in the last 30 days compared to the prior 30 days. These are all transactions from the current 30-day period."
            )

        elif 'category_above_average' == trigger.type:
            date_range = trigger.raw_data.get('date_range', 'this month') if trigger.raw_data else 'this month'
            return (
                f"{trigger.category} Spending Above Average (30-Day Rolling Period)",
                {
                    "current_period": trigger.this_month,
                    "historical_average": trigger.average,
                    "above_average_by": trigger.dollar_change,
                    "percent_above": trigger.percent_change
                },
                f"Last 30 days ({date_range}) vs historical average",
                f"You spent ${trigger.dollar_change:.2f} more than your usual ${trigger.average:.2f} average on {trigger.category} in the last 30 days. Below are all {trigger.category} transactions from this period."
            )

        elif 'year_over_year' in trigger.type:
            is_rolling = trigger.raw_data and trigger.raw_data.get('rolling_period')
            if is_rolling:
                current_period = trigger.raw_data.get('current_period', 'current period')
                comparison_period = trigger.raw_data.get('comparison_period', 'last year')
                return (
                    "Year-over-Year Comparison (30-Day Rolling Period)",
                    {
                        "current_period": trigger.this_month,
                        "last_year_period": trigger.last_month,
                        "change": trigger.dollar_change,
                        "percent_change": trigger.percent_change
                    },
                    f"{current_period} vs {comparison_period}",
                    f"Comparing the last 30 days to the same 30-day period last year shows a change of ${abs(trigger.dollar_change):.2f} ({trigger.percent_change:.1f}%). Transactions from both periods are shown."
                )
            else:
                return (
                    "Year-over-Year Comparison",
                    {
                        "this_year": trigger.this_month,
                        "last_year": trigger.last_month,
                        "change": trigger.dollar_change,
                        "percent_change": trigger.percent_change
                    },
                    "Same month, different years",
                    f"Comparing this month to the same month last year shows a change of ${abs(trigger.dollar_change):.2f} ({trigger.percent_change:.1f}%). Transactions from both months are shown."
                )

        elif 'merchant_lifetime_milestone' == trigger.type:
            milestone = trigger.raw_data.get('milestone_amount', 0) if trigger.raw_data else 0
            return (
                f"{trigger.merchant} Lifetime Milestone",
                {
                    "total_spent": trigger.this_month,
                    "number_of_visits": trigger.visit_count,
                    "milestone_reached": milestone
                },
                f"All-time spending history at {trigger.merchant} (showing 50 most recent transactions)",
                f"You've spent a total of ${trigger.this_month:.2f} at {trigger.merchant} over {trigger.visit_count} visits, crossing the ${milestone:,.0f} spending milestone. Below are all {trigger.merchant} transactions (up to 50 most recent)."
            )

        elif 'merchant_loyalty' == trigger.type:
            return (
                f"Frequent Spending at {trigger.merchant}",
                {
                    "total_spent": trigger.this_month,
                    "number_of_visits": trigger.visit_count
                },
                "All-time spending history (showing 30 most recent transactions)",
                f"You've made {trigger.visit_count} purchases at {trigger.merchant}, totaling ${trigger.this_month:.2f} (calculated from all your transaction history). The 30 most recent transactions at this merchant are shown below."
            )

        elif 'weekend_warrior' == trigger.type:
            return (
                "Weekend Spending Pattern",
                {
                    "weekend_daily_avg": trigger.weekend_spend,
                    "weekday_daily_avg": trigger.weekday_spend,
                    "ratio": trigger.weekend_spend / trigger.weekday_spend if trigger.weekday_spend > 0 else 0
                },
                "All-time weekend vs weekday spending (showing 50 most recent weekend transactions)",
                f"You spend ${trigger.weekend_spend:.2f} per day on weekends vs ${trigger.weekday_spend:.2f} on weekdays (calculated from all your transaction history). The 50 most recent weekend transactions are shown below."
            )

        elif 'lifetime_spending_milestone' == trigger.type:
            milestone = trigger.raw_data.get('milestone', 0) if trigger.raw_data else 0
            return (
                "Lifetime Spending Milestone",
                {
                    "total_lifetime_spending": trigger.this_month,
                    "milestone_reached": milestone
                },
                "All-time spending history (showing 100 most recent transactions)",
                f"You've reached a major milestone with ${trigger.this_month:,.2f} in total lifetime spending, crossing the ${milestone:,.0f} mark. Below are your 100 most recent transactions."
            )

        elif 'all_time_high' in trigger.type:
            return (
                "All-Time High Spending Month",
                {
                    "current_month_total": trigger.this_month
                },
                "Highest spending month on record",
                f"This month's spending of ${trigger.this_month:.2f} is the highest in your account history. All transactions from this month are shown."
            )

        elif 'savings_streak' == trigger.type:
            streak = trigger.raw_data.get('streak_length', 0) if trigger.raw_data else 0
            return (
                f"{streak}-Month Savings Streak",
                {
                    "total_saved": trigger.dollar_change,
                    "streak_length": streak
                },
                f"Last {streak} months of below-average spending",
                f"You've saved ${trigger.dollar_change:.2f} total by staying below your average for {streak} consecutive months. Transactions from the streak period are shown."
            )

        elif 'improvement' in trigger.type:
            return (
                "Spending Improvement Trend",
                {
                    "starting_amount": trigger.last_month,
                    "current_amount": trigger.this_month,
                    "total_reduction": trigger.dollar_change,
                    "percent_improvement": trigger.percent_change
                },
                "3-month improvement trend",
                f"Your spending decreased from ${trigger.last_month:.2f} to ${trigger.this_month:.2f} over 3 months, a {trigger.percent_change:.1f}% improvement. Transactions from this period are shown."
            )

        elif 'category_dominance' == trigger.type:
            share = trigger.raw_data.get('share', 0) if trigger.raw_data else 0
            return (
                f"{trigger.category} Dominates Your Spending",
                {
                    "category_total": trigger.this_month,
                    "percent_of_total": share
                },
                "All-time spending breakdown (showing 50 most recent transactions)",
                f"{trigger.category} represents {share:.1f}% of your total spending (${trigger.this_month:.2f}, calculated from all your transaction history). The 50 most recent {trigger.category} transactions are shown below."
            )

        else:
            # Default case
            return (
                "Spending Analysis",
                {"amount": trigger.this_month or 0},
                "Recent transactions",
                "Analysis of your recent spending patterns."
            )
