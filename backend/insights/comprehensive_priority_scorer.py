from typing import List, Tuple, Set
from app.models import Trigger
import re


class ComprehensivePriorityScorer:
    """
    Stage 3: Comprehensive priority scoring and insight deduplication
    Implements intelligent prioritization and selection logic
    """

    # Priority level definitions
    PRIORITY_CRITICAL = 1
    PRIORITY_HIGH = 2
    PRIORITY_MEDIUM = 3
    PRIORITY_LOW = 4

    # Non-actionable categories that users typically can't control
    NON_ACTIONABLE_CATEGORIES = {
        'Rent', 'rent', 'Housing', 'housing', 'Mortgage', 'mortgage',
        'Utilities', 'utilities', 'Electric', 'electric', 'Electricity', 'electricity',
        'Water', 'water', 'Gas', 'gas', 'Internet', 'internet', 'Phone', 'phone',
        'Insurance', 'insurance', 'Health Insurance', 'health insurance',
        'Car Insurance', 'car insurance', 'Home Insurance', 'home insurance',
        'Life Insurance', 'life insurance',
        'Loan', 'loan', 'Loans', 'loans', 'Student Loan', 'student loan',
        'Car Loan', 'car loan', 'Mortgage Payment', 'mortgage payment',
        'HOA', 'hoa', 'HOA Fees', 'hoa fees',
        'Property Tax', 'property tax', 'Taxes', 'taxes'
    }

    def __init__(self):
        self.priority_rules = self._define_priority_rules()

    def _define_priority_rules(self) -> dict:
        """Define priority levels for each trigger type"""
        return {
            # CRITICAL (1): All-time high spending, severe budget overruns
            'all_time_high_spending': self.PRIORITY_CRITICAL,
            'lifestyle_inflation': self.PRIORITY_CRITICAL,
            'monthly_spending_spike': self.PRIORITY_HIGH,  # Will be CRITICAL if > 50%

            # HIGH (2): Monthly spikes, new large merchants, YoY increases
            'category_all_time_high': self.PRIORITY_HIGH,
            'year_over_year_change': self.PRIORITY_HIGH,
            'category_year_over_year': self.PRIORITY_HIGH,
            'six_month_sustained_trend': self.PRIORITY_HIGH,
            'new_significant_merchant': self.PRIORITY_HIGH,

            # MEDIUM (3): Quarterly trends, category changes, behavioral observations
            'weekly_spending_spike': self.PRIORITY_MEDIUM,
            'weekly_category_spike': self.PRIORITY_MEDIUM,
            'category_above_average': self.PRIORITY_MEDIUM,
            'quarterly_trend_increase': self.PRIORITY_MEDIUM,
            'quarterly_trend_decrease': self.PRIORITY_MEDIUM,
            'three_month_sustained_trend': self.PRIORITY_MEDIUM,
            'category_rolling_trend': self.PRIORITY_MEDIUM,
            'weekend_warrior': self.PRIORITY_MEDIUM,
            'weekday_spender': self.PRIORITY_MEDIUM,
            'category_dominance': self.PRIORITY_MEDIUM,

            # LOW (4): Seasonal observations, minor improvements, informational
            'seasonal_high_spend_month': self.PRIORITY_LOW,
            'holiday_season_pattern': self.PRIORITY_LOW,
            'merchant_loyalty': self.PRIORITY_LOW,
            'lifetime_spending_milestone': self.PRIORITY_LOW,
            'merchant_lifetime_milestone': self.PRIORITY_LOW,
            'annual_growth_rate': self.PRIORITY_LOW,

            # POSITIVE (always prioritize at least one)
            'weekly_spending_win': self.PRIORITY_MEDIUM,
            'monthly_spending_win': self.PRIORITY_MEDIUM,
            'all_time_low_spending': self.PRIORITY_HIGH,
            'savings_streak': self.PRIORITY_MEDIUM,
            'income_positive_streak': self.PRIORITY_HIGH,
            'category_improvement_trend': self.PRIORITY_MEDIUM,
            'overall_improvement_trend': self.PRIORITY_HIGH,
        }

    def _is_actionable_category(self, category: str) -> bool:
        """Check if a category is actionable (user can control spending)"""
        if not category:
            return True  # Non-category insights are actionable

        # Check if category matches any non-actionable category
        return category not in self.NON_ACTIONABLE_CATEGORIES

    def score_and_rank(self, triggers: List[Trigger], top_n: int = 7) -> List[Tuple[Trigger, float]]:
        """
        Score all triggers, deduplicate, and return top N
        Returns list of (Trigger, score) tuples
        """
        if not triggers:
            return []

        # Step 0: Filter out non-actionable categories
        actionable_triggers = [
            t for t in triggers
            if not t.category or self._is_actionable_category(t.category)
        ]

        if not actionable_triggers:
            return []

        # Step 1: Assign base priority and magnitude scores
        scored_triggers = []
        for trigger in actionable_triggers:
            priority_level = self._get_priority_level(trigger)
            magnitude = self._calculate_magnitude(trigger)

            # Combine priority and magnitude into final score
            # Lower priority number = higher importance
            # Higher magnitude = more important
            # Score formula: (5 - priority) * 1000 + magnitude
            # This ensures priority dominates but magnitude differentiates within priority
            final_score = (5 - priority_level) * 1000 + magnitude

            scored_triggers.append((trigger, final_score, priority_level))

        # Step 2: Deduplicate overlapping insights
        scored_triggers = self._deduplicate(scored_triggers)

        # Step 3: Ensure diversity and at least one positive insight
        scored_triggers = self._ensure_diversity(scored_triggers, top_n)

        # Step 4: Sort by final score and return top N
        scored_triggers.sort(key=lambda x: x[1], reverse=True)
        return [(trigger, score) for trigger, score, _ in scored_triggers[:top_n]]

    def _get_priority_level(self, trigger: Trigger) -> int:
        """Get priority level for a trigger, with dynamic adjustments"""
        base_priority = self.priority_rules.get(trigger.type, self.PRIORITY_MEDIUM)

        # Dynamic priority adjustments
        if trigger.type == 'monthly_spending_spike':
            # Escalate to CRITICAL if spike is >50%
            if trigger.percent_change and trigger.percent_change > 50:
                return self.PRIORITY_CRITICAL

        if trigger.type == 'year_over_year_change':
            # Escalate if change is >50%
            if trigger.percent_change and trigger.percent_change > 50:
                return self.PRIORITY_CRITICAL

        if trigger.type == 'six_month_sustained_trend':
            # Escalate upward trends to HIGH
            direction = trigger.raw_data.get('trend_direction', '') if trigger.raw_data else ''
            if direction == 'increasing':
                return self.PRIORITY_HIGH

        return base_priority

    def _calculate_magnitude(self, trigger: Trigger) -> float:
        """Calculate magnitude score for a trigger"""
        magnitude = 0.0

        # Percentage change contributes to magnitude
        if trigger.percent_change:
            magnitude += min(trigger.percent_change, 200)  # Cap at 200 to avoid outliers dominating

        # Dollar amounts contribute (normalized)
        if trigger.dollar_change:
            magnitude += min(trigger.dollar_change / 10, 200)  # $1000 = 100 points, capped at 200

        if trigger.this_month:
            magnitude += min(trigger.this_month / 20, 100)  # $2000 = 100 points, capped at 100

        # Visit count for merchant insights
        if trigger.visit_count:
            magnitude += min(trigger.visit_count * 2, 50)  # 25 visits = 50 points, capped

        # Milestone amounts
        if trigger.raw_data and 'milestone' in trigger.raw_data:
            milestone = trigger.raw_data['milestone']
            magnitude += min(milestone / 100, 300)  # $10,000 milestone = 100 points

        # Streak length for positive insights
        if trigger.raw_data and 'streak_length' in trigger.raw_data:
            streak = trigger.raw_data['streak_length']
            magnitude += streak * 30  # Each month in streak = 30 points

        return magnitude

    def _deduplicate(self, scored_triggers: List[Tuple[Trigger, float, int]]) -> List[Tuple[Trigger, float, int]]:
        """Remove redundant insights covering the same pattern"""
        if len(scored_triggers) <= 1:
            return scored_triggers

        # Group triggers by category/merchant to detect overlaps
        category_triggers = {}
        merchant_triggers = {}
        general_triggers = []

        for trigger, score, priority in scored_triggers:
            if trigger.category:
                if trigger.category not in category_triggers:
                    category_triggers[trigger.category] = []
                category_triggers[trigger.category].append((trigger, score, priority))
            elif trigger.merchant:
                if trigger.merchant not in merchant_triggers:
                    merchant_triggers[trigger.merchant] = []
                merchant_triggers[trigger.merchant].append((trigger, score, priority))
            else:
                general_triggers.append((trigger, score, priority))

        deduplicated = []

        # For each category, keep only the highest-priority/highest-score trigger
        for category, triggers_list in category_triggers.items():
            # Sort by priority (lower is better), then by score (higher is better)
            triggers_list.sort(key=lambda x: (x[2], -x[1]))

            # Check for overlapping patterns
            if len(triggers_list) > 1:
                # Keep weekly spike only if there's no monthly spike
                weekly_types = ['weekly_spending_spike', 'weekly_category_spike']
                monthly_types = ['monthly_spending_spike', 'category_above_average']

                has_monthly = any(t[0].type in monthly_types for t in triggers_list)
                if has_monthly:
                    # Filter out weekly spikes
                    triggers_list = [t for t in triggers_list if t[0].type not in weekly_types]

            # Keep top 1-2 insights per category max
            deduplicated.extend(triggers_list[:2])

        # For each merchant, keep only top insight
        for merchant, triggers_list in merchant_triggers.items():
            triggers_list.sort(key=lambda x: (x[2], -x[1]))
            deduplicated.append(triggers_list[0])

        # Add all general triggers
        deduplicated.extend(general_triggers)

        return deduplicated

    def _ensure_diversity(self, scored_triggers: List[Tuple[Trigger, float, int]], top_n: int) -> List[Tuple[Trigger, float, int]]:
        """Ensure diversity in insights and at least one positive insight"""

        # Separate positive and negative/neutral insights
        positive_types = [
            'weekly_spending_win', 'monthly_spending_win', 'all_time_low_spending',
            'savings_streak', 'income_positive_streak', 'category_improvement_trend',
            'overall_improvement_trend'
        ]

        positive_insights = [t for t in scored_triggers if t[0].type in positive_types]
        other_insights = [t for t in scored_triggers if t[0].type not in positive_types]

        # Ensure at least one positive insight if available
        if positive_insights and not any(t[0].type in positive_types for t in scored_triggers[:top_n]):
            # Insert the highest-scoring positive insight
            positive_insights.sort(key=lambda x: x[1], reverse=True)
            # Replace the lowest-scoring other insight with the top positive
            other_insights.sort(key=lambda x: x[1], reverse=True)
            if len(other_insights) >= top_n:
                other_insights = other_insights[:top_n-1] + [positive_insights[0]]

        # Recombine and ensure no more than 2 insights about same category
        final_insights = other_insights + positive_insights
        final_insights.sort(key=lambda x: x[1], reverse=True)

        # Category diversity check
        category_counts = {}
        diverse_insights = []

        for trigger, score, priority in final_insights:
            if trigger.category:
                count = category_counts.get(trigger.category, 0)
                if count >= 2:
                    continue  # Skip this one, too many for this category
                category_counts[trigger.category] = count + 1

            diverse_insights.append((trigger, score, priority))

        # Timeframe diversity: mix of short-term, medium-term, long-term
        short_term_types = [
            'weekly_spending_spike', 'weekly_spending_win', 'weekly_category_spike',
            'monthly_spending_spike', 'monthly_spending_win', 'category_above_average'
        ]
        medium_term_types = [
            'quarterly_trend_increase', 'quarterly_trend_decrease',
            'three_month_sustained_trend', 'six_month_sustained_trend',
            'category_rolling_trend'
        ]
        long_term_types = [
            'year_over_year_change', 'category_year_over_year',
            'all_time_high_spending', 'all_time_low_spending',
            'category_all_time_high', 'annual_growth_rate', 'lifestyle_inflation'
        ]

        # Count by timeframe in top results
        top_subset = diverse_insights[:top_n]
        short_count = sum(1 for t, _, _ in top_subset if t.type in short_term_types)
        medium_count = sum(1 for t, _, _ in top_subset if t.type in medium_term_types)
        long_count = sum(1 for t, _, _ in top_subset if t.type in long_term_types)

        # Prefer balanced mix, but don't force it if data doesn't support it
        # This is informational for now, could add balancing logic if needed

        return diverse_insights

    def _is_positive_insight(self, trigger_type: str) -> bool:
        """Check if an insight type is positive/celebration"""
        positive_types = [
            'weekly_spending_win', 'monthly_spending_win', 'all_time_low_spending',
            'savings_streak', 'income_positive_streak', 'category_improvement_trend',
            'overall_improvement_trend'
        ]
        return trigger_type in positive_types
