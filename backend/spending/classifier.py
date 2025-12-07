"""
Spending Category Classifier
Classifies spending as necessary (non-negotiable) vs discretionary (cuttable)
"""

from typing import Dict, List, Tuple
import pandas as pd
from app.models import Transaction

# Category classification based on necessity
NECESSARY_CATEGORIES = {
    'Housing',
    'Utilities',
    'Internet',
    'Food and Groceries',
    'Groceries',  # Alternative name
    'Gas',  # Transportation
    'Transportation'
}

DISCRETIONARY_CATEGORIES = {
    'Travel',
    'Dining Out',
    'Restaurants',  # Alternative name
    'Entertainment',
    'Cloud',
    'Shopping',
    'News'
}


class SpendingClassifier:
    """Classifies and analyzes spending by necessity"""

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions

    def classify_category(self, category: str) -> str:
        """
        Classify a category as 'necessary' or 'discretionary'

        Args:
            category: The spending category to classify

        Returns:
            'necessary' or 'discretionary'
        """
        category_upper = category.upper()

        # Check necessary categories
        for necessary in NECESSARY_CATEGORIES:
            if necessary.upper() in category_upper or category_upper in necessary.upper():
                return 'necessary'

        # Check discretionary categories
        for discretionary in DISCRETIONARY_CATEGORIES:
            if discretionary.upper() in category_upper or category_upper in discretionary.upper():
                return 'discretionary'

        # Default to discretionary if unknown (conservative approach)
        return 'discretionary'

    def analyze_spending_breakdown(self) -> Dict:
        """
        Analyze monthly spending broken down by necessary vs discretionary

        Returns:
            Dict with spending breakdown and statistics
        """
        # Convert to DataFrame
        data = []
        for t in self.transactions:
            # Only include expenses (negative amounts)
            if t.amount < 0:
                category = t.category[0] if t.category else 'OTHER'
                data.append({
                    'date': t.date,
                    'amount': abs(t.amount),
                    'category': category,
                    'necessity': self.classify_category(category)
                })

        if not data:
            return {
                'monthly_necessary': 0,
                'monthly_discretionary': 0,
                'monthly_total': 0,
                'necessary_percent': 0,
                'discretionary_percent': 0,
                'by_category': {},
                'max_realistic_cuts': 0
            }

        df = pd.DataFrame(data)
        df['date'] = pd.to_datetime(df['date'])
        df['year_month'] = df['date'].dt.to_period('M')

        # Exclude current incomplete month
        current_month = pd.Timestamp.now().to_period('M')
        df = df[df['year_month'] < current_month]

        # Calculate monthly averages by necessity
        monthly_by_necessity = df.groupby(['year_month', 'necessity'])['amount'].sum().reset_index()
        avg_by_necessity = monthly_by_necessity.groupby('necessity')['amount'].mean()

        necessary_spending = avg_by_necessity.get('necessary', 0)
        discretionary_spending = avg_by_necessity.get('discretionary', 0)
        total_spending = necessary_spending + discretionary_spending

        # Calculate by category
        by_category = df.groupby(['category', 'necessity'])['amount'].mean().reset_index()
        category_breakdown = {}
        for _, row in by_category.iterrows():
            category_breakdown[row['category']] = {
                'monthly_avg': round(row['amount'], 2),
                'necessity': row['necessity']
            }

        # Calculate realistic maximum cuts (assume can cut 70% of discretionary)
        max_realistic_cuts = discretionary_spending * 0.7

        return {
            'monthly_necessary': round(necessary_spending, 2),
            'monthly_discretionary': round(discretionary_spending, 2),
            'monthly_total': round(total_spending, 2),
            'necessary_percent': round((necessary_spending / total_spending * 100) if total_spending > 0 else 0, 1),
            'discretionary_percent': round((discretionary_spending / total_spending * 100) if total_spending > 0 else 0, 1),
            'by_category': category_breakdown,
            'max_realistic_cuts': round(max_realistic_cuts, 2)
        }

    def calculate_realistic_savings_potential(
        self,
        monthly_income: float,
        target_monthly_savings: float
    ) -> Dict:
        """
        Calculate whether a savings target is realistically achievable

        Args:
            monthly_income: User's monthly income
            target_monthly_savings: How much they need to save per month

        Returns:
            Analysis of whether target is achievable and by how much
        """
        breakdown = self.analyze_spending_breakdown()

        current_total_spending = breakdown['monthly_total']
        necessary_spending = breakdown['monthly_necessary']
        discretionary_spending = breakdown['monthly_discretionary']
        max_realistic_cuts = breakdown['max_realistic_cuts']

        # Current savings
        current_savings = monthly_income - current_total_spending

        # Required total spending to hit target
        required_total_spending = monthly_income - target_monthly_savings

        # How much we need to cut
        required_cuts = current_total_spending - required_total_spending

        # Is it achievable?
        is_achievable = required_cuts <= max_realistic_cuts

        # If achievable, what discretionary spending should be
        if is_achievable:
            target_discretionary = discretionary_spending - required_cuts
            achievability = "realistic"
        elif required_total_spending >= necessary_spending:
            # Achievable if you cut ALL discretionary + some necessary
            target_discretionary = 0
            achievability = "difficult"
        else:
            # Impossible without reducing necessities (move, get roommate, etc.)
            target_discretionary = 0
            achievability = "unrealistic"

        return {
            'is_achievable': is_achievable,
            'achievability': achievability,
            'current_savings': round(current_savings, 2),
            'target_savings': round(target_monthly_savings, 2),
            'necessary_spending': round(necessary_spending, 2),
            'discretionary_spending': round(discretionary_spending, 2),
            'required_cuts': round(required_cuts, 2),
            'max_realistic_cuts': round(max_realistic_cuts, 2),
            'target_discretionary': round(target_discretionary, 2),
            'shortfall': round(max(0, required_cuts - max_realistic_cuts), 2)
        }
