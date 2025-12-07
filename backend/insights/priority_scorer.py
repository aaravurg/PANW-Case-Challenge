from typing import List, Tuple
from app.models import Trigger


class PriorityScorer:
    """Stage 3: Scores and ranks triggers by priority"""

    def __init__(self, triggers: List[Trigger]):
        self.triggers = triggers

    def score_and_rank(self, top_n: int = 7) -> List[Tuple[Trigger, float]]:
        """
        Score each trigger and return top N by priority

        Priority score = (
            dollar_impact × 0.3 +
            percent_change × 0.3 +
            recency_score × 0.2 +
            actionability × 0.2
        )
        """
        scored_triggers = []

        for trigger in self.triggers:
            score = self._calculate_priority_score(trigger)
            scored_triggers.append((trigger, score))

        # Sort by score descending
        scored_triggers.sort(key=lambda x: x[1], reverse=True)

        # Return top N
        return scored_triggers[:top_n]

    def _calculate_priority_score(self, trigger: Trigger) -> float:
        """Calculate priority score for a single trigger"""

        # Component 1: Dollar Impact (0-100 scale)
        dollar_impact = self._score_dollar_impact(trigger)

        # Component 2: Percent Change (0-100 scale)
        percent_change_score = self._score_percent_change(trigger)

        # Component 3: Recency (0-100 scale)
        # For now, all triggers are current month, so recency is high
        recency_score = 80  # Can be enhanced with week-level data

        # Component 4: Actionability (0-100 scale)
        actionability = self._score_actionability(trigger)

        # Weighted average
        priority_score = (
            dollar_impact * 0.3 +
            percent_change_score * 0.3 +
            recency_score * 0.2 +
            actionability * 0.2
        )

        return priority_score

    def _score_dollar_impact(self, trigger: Trigger) -> float:
        """Score based on dollar magnitude (higher = more important)"""

        # Get the dollar amount from trigger
        amount = 0
        if trigger.this_month:
            amount = trigger.this_month
        elif trigger.dollar_change:
            amount = abs(trigger.dollar_change)

        # Scale: $0-$50 = 0-20, $50-$200 = 20-50, $200-$500 = 50-80, >$500 = 80-100
        if amount < 50:
            return (amount / 50) * 20
        elif amount < 200:
            return 20 + ((amount - 50) / 150) * 30
        elif amount < 500:
            return 50 + ((amount - 200) / 300) * 30
        else:
            return min(80 + ((amount - 500) / 500) * 20, 100)

    def _score_percent_change(self, trigger: Trigger) -> float:
        """Score based on percent change magnitude (larger swings = more notable)"""

        if not trigger.percent_change:
            return 50  # Neutral score if no percent change

        percent = abs(trigger.percent_change)

        # Scale: 0-20% = 0-30, 20-50% = 30-60, 50-100% = 60-90, >100% = 90-100
        if percent < 20:
            return (percent / 20) * 30
        elif percent < 50:
            return 30 + ((percent - 20) / 30) * 30
        elif percent < 100:
            return 60 + ((percent - 50) / 50) * 30
        else:
            return min(90 + ((percent - 100) / 100) * 10, 100)

    def _score_actionability(self, trigger: Trigger) -> float:
        """Score based on how actionable the insight is"""

        actionability_map = {
            # High actionability (80-100)
            "spending_spike": 90,
            "frequent_merchant": 85,
            "high_merchant_spend": 85,
            "savings_concern": 95,
            "sudden_increase": 90,
            "dominant_category": 80,
            "overall_spending_increase": 85,

            # Medium actionability (50-79)
            "weekend_heavy": 70,

            # Lower actionability but positive (30-49)
            "spending_win": 40,
            "savings_win": 35,
        }

        return actionability_map.get(trigger.type, 50)

    def get_trigger_category(self, trigger: Trigger) -> str:
        """Categorize trigger type for LLM insight generation"""

        if trigger.type in ["spending_win", "savings_win"]:
            return "win"
        elif trigger.type in ["spending_spike", "sudden_increase", "overall_spending_increase",
                             "high_merchant_spend", "frequent_merchant", "dominant_category",
                             "savings_concern", "weekend_heavy"]:
            return "alert"
        else:
            return "anomaly"
