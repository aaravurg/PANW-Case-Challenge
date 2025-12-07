"""
Investment Capacity Calculator

Calculates how much money users have available to invest each month by:
1. Starting with monthly take-home income
2. Subtracting average monthly spending from transaction history
3. Subtracting monthly commitments to active savings goals
4. Providing educational content on beginner-friendly investment options
"""

from typing import List
from datetime import datetime, timedelta
import pandas as pd
from app.models import (
    Transaction, Goal, InvestmentOption, InvestmentBreakdown,
    InvestmentCapacityResponse
)


class InvestmentCapacityCalculator:
    """Calculates investment capacity and provides investment education"""

    # Simplified effective tax rate for gross income conversion
    DEFAULT_TAX_RATE = 0.25  # 25% effective tax rate

    def __init__(self, transactions: List[Transaction], goals: List[Goal]):
        """
        Initialize calculator with transaction history and active goals

        Args:
            transactions: List of user transactions
            goals: List of active savings goals
        """
        self.transactions = transactions
        self.goals = [g for g in goals if g.is_active]  # Only consider active goals

    def calculate_take_home(self, income: float, is_gross: bool) -> float:
        """
        Calculate take-home income

        Args:
            income: Monthly income amount
            is_gross: True if gross income, False if already net

        Returns:
            Take-home (after-tax) income
        """
        if is_gross:
            return income * (1 - self.DEFAULT_TAX_RATE)
        return income

    def calculate_average_monthly_spending(self, months_lookback: int = 3) -> float:
        """
        Calculate average monthly spending from transaction history

        Args:
            months_lookback: Number of months to look back (default: 3)

        Returns:
            Average monthly spending (absolute value)
        """
        if not self.transactions:
            return 0.0

        # Convert to DataFrame for easier analysis
        df = pd.DataFrame([
            {
                'date': t.date,
                'amount': t.amount
            }
            for t in self.transactions
        ])

        # Get cutoff date
        latest_date = df['date'].max()
        cutoff_date = latest_date - timedelta(days=months_lookback * 30)

        # Filter to recent transactions and expenses only (negative amounts)
        recent_expenses = df[
            (df['date'] >= cutoff_date) &
            (df['amount'] < 0)
        ]

        if recent_expenses.empty:
            return 0.0

        # Calculate total spending
        total_spending = abs(recent_expenses['amount'].sum())

        # Calculate actual number of months in the data
        date_range_days = (latest_date - recent_expenses['date'].min()).days
        actual_months = max(1, date_range_days / 30)

        # Return average per month
        return total_spending / actual_months

    def calculate_goal_commitments(self) -> float:
        """
        Calculate total monthly savings committed to active goals

        This uses a simple calculation based on goal requirements:
        Required Monthly Savings = (Target - Current Savings) / Months Remaining

        Returns:
            Total monthly commitment across all active goals
        """
        total_commitment = 0.0

        for goal in self.goals:
            # Parse deadline
            deadline = datetime.fromisoformat(goal.deadline.replace('Z', '+00:00'))
            now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()

            # Calculate months remaining
            months_remaining = max(1, (deadline.year - now.year) * 12 + (deadline.month - now.month))

            # Calculate amount still needed
            amount_needed = max(0, goal.target_amount - goal.current_savings)

            # Calculate required monthly savings
            required_monthly = amount_needed / months_remaining

            total_commitment += required_monthly

        return total_commitment

    def get_investment_options(self) -> List[InvestmentOption]:
        """
        Get list of beginner-friendly investment options with educational content

        Returns:
            List of investment options with descriptions
        """
        return [
            InvestmentOption(
                name="High-Yield Savings Account (HYSA)",
                risk_level="Zero risk",
                typical_returns="4-5% APY",
                accessibility="Instant access to your money",
                best_for="Emergency funds, short-term goals (< 2 years), money you might need quickly",
                description=(
                    "A savings account that pays significantly more interest than traditional savings accounts. "
                    "Your money is FDIC-insured (protected up to $250,000), so there's no risk of losing it. "
                    "Perfect for building an emergency fund or saving for something you'll need in the next year or two. "
                    "Popular options include Marcus by Goldman Sachs, Ally Bank, and American Express Personal Savings."
                )
            ),
            InvestmentOption(
                name="Certificates of Deposit (CDs)",
                risk_level="Very low risk",
                typical_returns="4-5.5% APY",
                accessibility="Fixed term (3 months to 5 years), early withdrawal penalties apply",
                best_for="Goals with a known timeline, money you won't need for a specific period",
                description=(
                    "A CD is a savings account where you agree to leave your money untouched for a specific period "
                    "(like 6 months, 1 year, or 5 years) in exchange for a higher interest rate. "
                    "Your money is also FDIC-insured. If you withdraw early, you'll pay a penalty (usually a few months of interest). "
                    "Great for saving toward a down payment, wedding, or other goal with a firm date. "
                    "Consider 'laddering' CDs (opening multiple with different terms) for flexibility."
                )
            ),
            InvestmentOption(
                name="Index Funds (S&P 500)",
                risk_level="Moderate risk",
                typical_returns="~10% average annual return (historically)",
                accessibility="Can sell anytime, but value fluctuates daily — best held 5+ years",
                best_for="Long-term growth (retirement, kids' college), money you won't need for 5+ years",
                description=(
                    "An index fund is a collection of stocks from many companies (like the 500 largest US companies in the S&P 500). "
                    "Instead of picking individual stocks, you own a tiny piece of all of them. "
                    "While the value goes up and down in the short term, historically it has grown about 10% per year on average. "
                    "This is riskier than a savings account but offers much higher potential returns over time. "
                    "Look for low-fee options like Vanguard's VOO or Fidelity's FXAIX. Not FDIC-insured — value can drop."
                )
            ),
            InvestmentOption(
                name="Roth IRA",
                risk_level="Varies (depends on what you invest in)",
                typical_returns="Tax-free growth on your investments",
                accessibility="Contributions can be withdrawn anytime; earnings locked until retirement (age 59½)",
                best_for="Retirement savings, especially if you're young and in a lower tax bracket now",
                description=(
                    "A Roth IRA is a special retirement account where your money grows completely tax-free. "
                    "You contribute money you've already paid taxes on, and when you retire, you can withdraw everything "
                    "(contributions AND earnings) without paying taxes. You can contribute up to $7,000/year (2024 limit). "
                    "Inside a Roth IRA, you can invest in stocks, bonds, index funds, etc. — you choose your risk level. "
                    "The key benefit: tax-free growth for decades. Open one through Vanguard, Fidelity, or Schwab."
                )
            )
        ]

    def calculate(
        self,
        monthly_income: float,
        is_gross_income: bool,
        months_lookback: int = 3
    ) -> InvestmentCapacityResponse:
        """
        Calculate complete investment capacity breakdown

        Args:
            monthly_income: User's monthly income
            is_gross_income: True if gross, False if net
            months_lookback: Months of transaction history to analyze

        Returns:
            Complete investment capacity response with breakdown and options
        """
        # Calculate components
        take_home = self.calculate_take_home(monthly_income, is_gross_income)
        avg_spending = self.calculate_average_monthly_spending(months_lookback)
        goal_commitments = self.calculate_goal_commitments()

        # Calculate investable surplus
        investable_surplus = take_home - avg_spending - goal_commitments

        # Build breakdown
        breakdown = InvestmentBreakdown(
            monthly_income=monthly_income,
            take_home_income=take_home,
            average_monthly_spending=avg_spending,
            total_goal_commitments=goal_commitments,
            investable_surplus=max(0, investable_surplus)  # Don't show negative
        )

        # Get investment options
        options = self.get_investment_options()

        # Build response
        return InvestmentCapacityResponse(
            breakdown=breakdown,
            investment_options=options,
            calculation_period=f"Based on last {months_lookback} months of spending",
            active_goals_count=len(self.goals)
        )
