"""
Recommendation Engine for generating actionable spending cut suggestions
to help users reach their savings goals
"""

import pandas as pd
from typing import List, Dict, Tuple
from app.models import Transaction, GoalRecommendation, GapAnalysis


class RecommendationEngine:
    """
    Analyzes discretionary spending and generates specific, feasible
    cut suggestions to close the gap on savings goals
    """

    # Define discretionary categories and feasible reduction percentages
    DISCRETIONARY_CATEGORIES = {
        'FOOD_AND_DRINK': {
            'display_name': 'dining out',
            'min_reduction': 0.20,
            'max_reduction': 0.50,
            'priority': 2
        },
        'ENTERTAINMENT': {
            'display_name': 'entertainment',
            'min_reduction': 0.30,
            'max_reduction': 0.60,
            'priority': 3
        },
        'GENERAL_MERCHANDISE': {
            'display_name': 'shopping',
            'min_reduction': 0.20,
            'max_reduction': 0.40,
            'priority': 4
        },
        'GENERAL_SERVICES': {
            'display_name': 'subscriptions and services',
            'min_reduction': 0.30,
            'max_reduction': 1.0,  # Can cancel completely
            'priority': 1  # Easiest to cut
        },
        'TRANSPORTATION': {
            'display_name': 'rideshare and transportation',
            'min_reduction': 0.30,
            'max_reduction': 0.50,
            'priority': 5
        }
    }

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.df = self._create_dataframe()

    def _create_dataframe(self) -> pd.DataFrame:
        """Convert transactions to DataFrame"""
        data = []
        for t in self.transactions:
            # Only include expenses (negative amounts)
            if t.amount < 0:
                data.append({
                    'date': t.date,
                    'amount': abs(t.amount),  # Make positive for easier math
                    'category': t.category[0] if t.category else 'OTHER',
                    'merchant_name': t.merchant_name
                })

        df = pd.DataFrame(data)
        if not df.empty:
            df['date'] = pd.to_datetime(df['date'])
        return df

    def calculate_monthly_spending_by_category(self) -> Dict[str, float]:
        """
        Calculate average monthly spending per category

        Returns: {category: monthly_average}
        """
        if self.df.empty:
            return {}

        # Get number of months in dataset
        df = self.df.copy()
        df['year_month'] = df['date'].dt.to_period('M')
        num_months = df['year_month'].nunique()

        if num_months == 0:
            num_months = 1

        # Calculate total spending by category
        category_totals = df.groupby('category')['amount'].sum()

        # Convert to monthly average
        monthly_avg = (category_totals / num_months).to_dict()

        return monthly_avg

    def identify_cut_candidates(
        self,
        monthly_spending: Dict[str, float]
    ) -> List[Tuple[str, float, Dict]]:
        """
        Identify categories that can be cut

        Returns: List of (category, monthly_amount, config) sorted by priority
        """
        candidates = []

        for category, amount in monthly_spending.items():
            if category in self.DISCRETIONARY_CATEGORIES:
                config = self.DISCRETIONARY_CATEGORIES[category]
                # Only consider if there's meaningful spending
                if amount >= 10:  # At least $10/month to be worth cutting
                    candidates.append((category, amount, config))

        # Sort by priority (lower number = higher priority)
        candidates.sort(key=lambda x: x[2]['priority'])

        return candidates

    def generate_single_recommendation(
        self,
        category: str,
        monthly_amount: float,
        reduction_pct: float,
        config: Dict
    ) -> GoalRecommendation:
        """
        Create a single recommendation

        Returns: GoalRecommendation
        """
        monthly_savings = monthly_amount * reduction_pct
        display_name = config['display_name']

        # Create action description
        if reduction_pct >= 0.9:
            action = f"Cancel or eliminate {display_name}"
        else:
            action = f"Reduce {display_name} by {int(reduction_pct * 100)}%"

        return GoalRecommendation(
            action=action,
            category=category,
            monthly_savings=round(monthly_savings, 2),
            impact=""  # Will be filled in later with cumulative impact
        )

    def generate_recommendations(
        self,
        gap_analysis: GapAnalysis,
        max_recommendations: int = 3
    ) -> List[GoalRecommendation]:
        """
        Generate specific spending cut recommendations to close the gap

        Args:
            gap_analysis: The gap analysis showing how much user is short
            max_recommendations: Maximum number of recommendations to generate

        Returns: List of GoalRecommendation objects
        """
        if gap_analysis is None:
            return []

        monthly_gap = gap_analysis.monthly_gap

        if monthly_gap <= 0:
            return []

        # Get monthly spending by category
        monthly_spending = self.calculate_monthly_spending_by_category()

        # Identify cut candidates
        candidates = self.identify_cut_candidates(monthly_spending)

        if not candidates:
            return []

        recommendations = []
        cumulative_savings = 0.0

        # Try to close the gap with minimal cuts
        for category, amount, config in candidates:
            if cumulative_savings >= monthly_gap:
                break

            if len(recommendations) >= max_recommendations:
                break

            remaining_gap = monthly_gap - cumulative_savings

            # Determine reduction percentage needed
            # Try minimum reduction first
            min_reduction = config['min_reduction']
            max_reduction = config['max_reduction']

            # Calculate what percentage would close the remaining gap
            needed_reduction = min(remaining_gap / amount, max_reduction)

            # Use the minimum feasible reduction, or what's needed (whichever is less)
            if needed_reduction < min_reduction:
                reduction_pct = min_reduction
            else:
                # Round to nice percentages (25%, 30%, 50%, etc.)
                reduction_pct = self._round_to_nice_percentage(
                    needed_reduction,
                    max_reduction
                )

            # Generate recommendation
            rec = self.generate_single_recommendation(
                category,
                amount,
                reduction_pct,
                config
            )

            cumulative_savings += rec.monthly_savings
            recommendations.append(rec)

        # Update impact descriptions
        for i, rec in enumerate(recommendations):
            if cumulative_savings >= monthly_gap:
                buffer = cumulative_savings - monthly_gap
                rec.impact = f"Closes gap with ${buffer:.2f} buffer"
            else:
                progress = (cumulative_savings / monthly_gap) * 100
                rec.impact = f"Achieves {progress:.0f}% of needed savings"

        return recommendations

    def _round_to_nice_percentage(
        self,
        percentage: float,
        max_allowed: float
    ) -> float:
        """
        Round to nice percentages like 0.25, 0.30, 0.50, etc.

        Returns: float between 0 and max_allowed
        """
        nice_percentages = [0.25, 0.30, 0.35, 0.40, 0.50, 0.60, 0.75, 1.0]

        # Find the smallest nice percentage that meets the need
        for nice_pct in nice_percentages:
            if nice_pct >= percentage and nice_pct <= max_allowed:
                return nice_pct

        # If none found, return the max
        return max_allowed

    def get_category_breakdown(self) -> Dict[str, Dict]:
        """
        Get detailed breakdown of discretionary spending

        Returns: {category: {monthly_avg, total, merchant_count}}
        """
        if self.df.empty:
            return {}

        monthly_spending = self.calculate_monthly_spending_by_category()
        breakdown = {}

        for category in self.DISCRETIONARY_CATEGORIES:
            if category in monthly_spending:
                category_df = self.df[self.df['category'] == category]

                breakdown[category] = {
                    'monthly_avg': round(monthly_spending[category], 2),
                    'total_transactions': len(category_df),
                    'merchant_count': category_df['merchant_name'].nunique(),
                    'display_name': self.DISCRETIONARY_CATEGORIES[category]['display_name']
                }

        return breakdown
