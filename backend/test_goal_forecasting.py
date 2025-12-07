"""
Test script for goal forecasting functionality
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from models import Transaction, Goal
from goal_forecaster import GoalForecaster
from recommendation_engine import RecommendationEngine

def load_test_transactions():
    """Load sample transactions"""
    csv_path = '../sample_transactions_1000_sorted.csv'
    df = pd.read_csv(csv_path)

    transactions = []
    for _, row in df.iterrows():
        try:
            category = json.loads(row['category']) if isinstance(row['category'], str) else row['category']
        except json.JSONDecodeError:
            category = [row['category']]

        date = pd.to_datetime(row['date'])

        transaction = Transaction(
            transaction_id=row['transaction_id'],
            date=date,
            amount=float(row['amount']),
            merchant_name=row['merchant_name'],
            category=category,
            payment_channel=row['payment_channel'],
            pending=bool(row['pending'])
        )
        transactions.append(transaction)

    return transactions


def test_forecasting():
    """Test the goal forecasting with different scenarios"""

    print("=" * 60)
    print("GOAL FORECASTING TEST")
    print("=" * 60)

    # Load transactions
    print("\n1. Loading transaction data...")
    transactions = load_test_transactions()
    print(f"   ✓ Loaded {len(transactions)} transactions")

    # Test Case 1: Ambitious goal (likely off-track)
    print("\n2. Testing Scenario 1: Ambitious Goal (Tesla Down Payment)")
    print("   Goal: $15,000 in 6 months")
    print("   Monthly Income: $5,000")

    goal1 = Goal(
        id="test-1",
        goal_name="Tesla Down Payment",
        target_amount=15000,
        deadline=(datetime.now() + timedelta(days=180)).isoformat(),
        current_savings=1200,
        priority_level="high",
        created_at=datetime.now().isoformat(),
        monthly_income=5000.0,
        income_type="fixed"
    )

    forecaster = GoalForecaster(transactions)
    forecast1 = forecaster.forecast_goal(goal1)

    print(f"\n   Results:")
    print(f"   - Status: {forecast1.status}")
    print(f"   - Probability: {forecast1.probability}")
    print(f"   - On Track: {forecast1.on_track}")
    print(f"   - Expected Total: ${forecast1.projection.expected_total:,.2f}")
    print(f"   - Expected Monthly Savings: ${forecast1.projection.expected_monthly_savings:,.2f}")

    if forecast1.gap_analysis:
        print(f"\n   Gap Analysis:")
        print(f"   - Shortfall: ${forecast1.gap_analysis.shortfall:,.2f}")
        print(f"   - Monthly Gap: ${forecast1.gap_analysis.monthly_gap:,.2f}")
        print(f"   - Current Monthly Savings: ${forecast1.gap_analysis.current_monthly_savings:,.2f}")
        print(f"   - Required Monthly Savings: ${forecast1.gap_analysis.required_monthly_savings:,.2f}")

        # Test recommendations
        print(f"\n   Generating recommendations...")
        rec_engine = RecommendationEngine(transactions)
        recommendations = rec_engine.generate_recommendations(forecast1.gap_analysis)

        print(f"\n   Recommendations ({len(recommendations)} found):")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec.action}")
            print(f"      Category: {rec.category}")
            print(f"      Monthly Savings: ${rec.monthly_savings:.2f}")
            print(f"      Impact: {rec.impact}")

    # Test Case 2: Moderate goal (more achievable)
    print("\n\n3. Testing Scenario 2: Moderate Goal (Vacation Fund)")
    print("   Goal: $3,000 in 12 months")
    print("   Monthly Income: $5,000")

    goal2 = Goal(
        id="test-2",
        goal_name="Vacation Fund",
        target_amount=3000,
        deadline=(datetime.now() + timedelta(days=365)).isoformat(),
        current_savings=500,
        priority_level="medium",
        created_at=datetime.now().isoformat(),
        monthly_income=5000.0,
        income_type="fixed"
    )

    forecast2 = forecaster.forecast_goal(goal2)

    print(f"\n   Results:")
    print(f"   - Status: {forecast2.status}")
    print(f"   - Probability: {forecast2.probability}")
    print(f"   - On Track: {forecast2.on_track}")
    print(f"   - Expected Total: ${forecast2.projection.expected_total:,.2f}")
    print(f"   - Optimistic Total: ${forecast2.projection.optimistic_total:,.2f}")
    print(f"   - Pessimistic Total: ${forecast2.projection.pessimistic_total:,.2f}")

    # Display forecast path sample
    print(f"\n   Forecast Path (first 3 months):")
    for point in forecast2.forecast_path[:3]:
        print(f"   - {point.month}: ${point.cumulative:,.2f} (range: ${point.lower:,.2f} - ${point.upper:,.2f})")

    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

    # Return success flag
    return True


if __name__ == "__main__":
    try:
        success = test_forecasting()
        if success:
            print("\n✅ All tests passed successfully!")
        else:
            print("\n❌ Some tests failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
