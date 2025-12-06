from typing import List
from models import Trigger, AggregatedStats
from data_aggregator import DataAggregator


class TriggerDetector:
    """Stage 2: Detects spending patterns and triggers insights"""

    def __init__(self, stats: AggregatedStats, aggregator: DataAggregator):
        self.stats = stats
        self.aggregator = aggregator

    def detect_all_triggers(self) -> List[Trigger]:
        """Detect all triggers from aggregated statistics"""
        triggers = []

        # Category-based triggers
        triggers.extend(self._detect_category_triggers())

        # Merchant-based triggers
        triggers.extend(self._detect_merchant_triggers())

        # General financial health triggers
        triggers.extend(self._detect_general_triggers())

        return triggers

    def _detect_category_triggers(self) -> List[Trigger]:
        """Detect category spending patterns"""
        triggers = []

        for category, this_month in self.stats.spending_by_category_this_month.items():
            last_month = self.stats.spending_by_category_last_month.get(category, 0)
            avg_3mo = self.stats.spending_by_category_3mo_average.get(category, 0)

            # Skip if no historical data
            if avg_3mo == 0:
                avg_3mo = this_month  # Use current as baseline

            percent_change_vs_avg = ((this_month - avg_3mo) / avg_3mo * 100) if avg_3mo > 0 else 0
            percent_change_vs_last = ((this_month - last_month) / last_month * 100) if last_month > 0 else 0
            dollar_change = this_month - avg_3mo

            # TRIGGER: Spending spike (30% above average)
            if percent_change_vs_avg > 30:
                top_merchants = self.aggregator.get_top_merchants_for_category(category)
                triggers.append(Trigger(
                    type="spending_spike",
                    category=category,
                    this_month=this_month,
                    average=avg_3mo,
                    percent_change=percent_change_vs_avg,
                    dollar_change=dollar_change,
                    top_merchants=top_merchants
                ))

            # TRIGGER: Spending win (20% below average)
            if percent_change_vs_avg < -20:
                triggers.append(Trigger(
                    type="spending_win",
                    category=category,
                    this_month=this_month,
                    average=avg_3mo,
                    percent_change=abs(percent_change_vs_avg),
                    dollar_change=abs(dollar_change)
                ))

            # TRIGGER: Sudden increase (50% above last month)
            if percent_change_vs_last > 50 and last_month > 0:
                triggers.append(Trigger(
                    type="sudden_increase",
                    category=category,
                    this_month=this_month,
                    last_month=last_month,
                    percent_change=percent_change_vs_last,
                    dollar_change=this_month - last_month
                ))

            # TRIGGER: Dominant category (>40% of total spending)
            if self.stats.total_spending_this_month > 0:
                category_share = (this_month / self.stats.total_spending_this_month) * 100
                if category_share > 40:
                    triggers.append(Trigger(
                        type="dominant_category",
                        category=category,
                        this_month=this_month,
                        percent_change=category_share,
                        raw_data={"total_spending": self.stats.total_spending_this_month}
                    ))

        return triggers

    def _detect_merchant_triggers(self) -> List[Trigger]:
        """Detect merchant-specific patterns"""
        triggers = []
        visit_counts = self.aggregator.get_merchant_visit_counts()

        for merchant, amount in self.stats.spending_by_merchant_this_month.items():
            visits = visit_counts.get(merchant, 0)

            # TRIGGER: Frequent merchant (>10 visits)
            if visits > 10:
                triggers.append(Trigger(
                    type="frequent_merchant",
                    merchant=merchant,
                    this_month=amount,
                    visit_count=visits
                ))

            # TRIGGER: High merchant spend (>$200)
            if amount > 200:
                triggers.append(Trigger(
                    type="high_merchant_spend",
                    merchant=merchant,
                    this_month=amount,
                    visit_count=visits
                ))

        return triggers

    def _detect_general_triggers(self) -> List[Trigger]:
        """Detect general financial health patterns"""
        triggers = []

        # Calculate savings rate
        if self.stats.total_income_this_month > 0:
            savings = self.stats.total_income_this_month - self.stats.total_spending_this_month
            savings_rate = (savings / self.stats.total_income_this_month) * 100

            # TRIGGER: Savings win (>20% savings rate)
            if savings_rate > 20:
                triggers.append(Trigger(
                    type="savings_win",
                    savings_rate=savings_rate,
                    this_month=savings,
                    raw_data={
                        "income": self.stats.total_income_this_month,
                        "spending": self.stats.total_spending_this_month
                    }
                ))

            # TRIGGER: Savings concern (<5% savings rate)
            if savings_rate < 5 and savings_rate > -20:  # Not deep in negative
                triggers.append(Trigger(
                    type="savings_concern",
                    savings_rate=savings_rate,
                    this_month=savings,
                    raw_data={
                        "income": self.stats.total_income_this_month,
                        "spending": self.stats.total_spending_this_month
                    }
                ))

        # Weekend vs Weekday spending
        weekend_weekday = self.aggregator.get_weekend_vs_weekday_spending()
        weekend_spend = weekend_weekday.get('weekend', 0)
        weekday_spend = weekend_weekday.get('weekday', 0)

        # TRIGGER: Weekend heavy (weekend > weekday * 1.5)
        if weekday_spend > 0 and weekend_spend > weekday_spend * 1.5:
            triggers.append(Trigger(
                type="weekend_heavy",
                weekend_spend=weekend_spend,
                weekday_spend=weekday_spend,
                percent_change=(weekend_spend / weekday_spend * 100) if weekday_spend > 0 else 0
            ))

        # TRIGGER: Spending increase vs last month
        if self.stats.total_spending_last_month > 0:
            spending_change = ((self.stats.total_spending_this_month - self.stats.total_spending_last_month)
                              / self.stats.total_spending_last_month * 100)
            if spending_change > 20:
                triggers.append(Trigger(
                    type="overall_spending_increase",
                    this_month=self.stats.total_spending_this_month,
                    last_month=self.stats.total_spending_last_month,
                    percent_change=spending_change,
                    dollar_change=self.stats.total_spending_this_month - self.stats.total_spending_last_month
                ))

        return triggers
