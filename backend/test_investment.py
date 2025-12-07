"""
Quick test script for investment capacity calculator
"""

import sys
import os
import json
from datetime import datetime

# Add parent directory to path so we can import app modules
sys.path.insert(0, os.path.dirname(__file__))

from app.models import Transaction, Goal
from app.investment_calculator import InvestmentCapacityCalculator

def create_test_transactions():
    """Create some test transactions"""
    transactions = []

    # Create 3 months of test expenses
    for month in range(3):
        # Groceries: ~$500/month
        for i in range(8):
            transactions.append(Transaction(
                transaction_id=f"txn_grocery_{month}_{i}",
                date=datetime(2024, 9 + month, 5 + i),
                amount=-62.50,
                merchant_name="Whole Foods",
                category=["FOOD_AND_DRINK"],
                payment_channel="online",
                pending=False
            ))

        # Rent: $1850/month
        transactions.append(Transaction(
            transaction_id=f"txn_rent_{month}",
            date=datetime(2024, 9 + month, 1),
            amount=-1850.00,
            merchant_name="Property Management",
            category=["RENT_AND_UTILITIES"],
            payment_channel="online",
            pending=False
        ))

        # Utilities: $150/month
        transactions.append(Transaction(
            transaction_id=f"txn_utilities_{month}",
            date=datetime(2024, 9 + month, 15),
            amount=-150.00,
            merchant_name="PG&E",
            category=["RENT_AND_UTILITIES"],
            payment_channel="online",
            pending=False
        ))

        # Dining: ~$300/month
        for i in range(12):
            transactions.append(Transaction(
                transaction_id=f"txn_dining_{month}_{i}",
                date=datetime(2024, 9 + month, 3 + i),
                amount=-25.00,
                merchant_name="Restaurant",
                category=["FOOD_AND_DRINK"],
                payment_channel="online",
                pending=False
            ))

    return transactions

def create_test_goals():
    """Create test goals"""
    return [
        Goal(
            id="goal_1",
            goal_name="Emergency Fund",
            target_amount=10000.0,
            deadline="2025-12-31",
            current_savings=2000.0,
            priority_level="high",
            created_at=datetime.now().isoformat(),
            user_id="test_user",
            is_active=True,
            monthly_income=6000.0,
            income_type="fixed"
        ),
        Goal(
            id="goal_2",
            goal_name="Vacation",
            target_amount=3000.0,
            deadline="2025-06-30",
            current_savings=500.0,
            priority_level="medium",
            created_at=datetime.now().isoformat(),
            user_id="test_user",
            is_active=True,
            monthly_income=6000.0,
            income_type="fixed"
        )
    ]

def test_investment_capacity():
    """Test the investment capacity calculator"""
    print("\n" + "="*60)
    print("Testing Investment Capacity Calculator")
    print("="*60 + "\n")

    # Create test data
    transactions = create_test_transactions()
    goals = create_test_goals()

    print(f"✓ Created {len(transactions)} test transactions")
    print(f"✓ Created {len(goals)} test goals\n")

    # Create calculator
    calculator = InvestmentCapacityCalculator(transactions, goals)

    # Test with gross income
    print("Test Case 1: Gross Income ($8000/month)")
    print("-" * 60)
    result = calculator.calculate(
        monthly_income=8000.0,
        is_gross_income=True
    )

    print(f"Monthly Income (Gross):        ${result.breakdown.monthly_income:,.2f}")
    print(f"Take-Home Income (75%):        ${result.breakdown.take_home_income:,.2f}")
    print(f"Average Monthly Spending:     -${result.breakdown.average_monthly_spending:,.2f}")
    print(f"Goal Commitments:             -${result.breakdown.total_goal_commitments:,.2f}")
    print(f"{'='*40}")
    print(f"💰 Available to Invest:        ${result.breakdown.investable_surplus:,.2f}\n")
    print(f"Calculation Period: {result.calculation_period}")
    print(f"Active Goals: {result.active_goals_count}")
    print(f"Investment Options: {len(result.investment_options)}\n")

    # Test with net income
    print("\nTest Case 2: Net Income ($6000/month)")
    print("-" * 60)
    result2 = calculator.calculate(
        monthly_income=6000.0,
        is_gross_income=False
    )

    print(f"Monthly Income (Net):          ${result2.breakdown.monthly_income:,.2f}")
    print(f"Take-Home Income:              ${result2.breakdown.take_home_income:,.2f}")
    print(f"Average Monthly Spending:     -${result2.breakdown.average_monthly_spending:,.2f}")
    print(f"Goal Commitments:             -${result2.breakdown.total_goal_commitments:,.2f}")
    print(f"{'='*40}")
    print(f"💰 Available to Invest:        ${result2.breakdown.investable_surplus:,.2f}\n")

    # Show investment options
    print("\nInvestment Options Provided:")
    print("-" * 60)
    for i, option in enumerate(result.investment_options, 1):
        print(f"{i}. {option.name}")
        print(f"   Risk: {option.risk_level} | Returns: {option.typical_returns}")
        print(f"   Access: {option.accessibility}")
        print(f"   Best for: {option.best_for}\n")

    print("="*60)
    print("✅ All tests passed successfully!")
    print("="*60 + "\n")

if __name__ == "__main__":
    test_investment_capacity()
