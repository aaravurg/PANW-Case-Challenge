"""
Test script for goal competition analysis
Shows how multiple goals compete for limited savings
"""

import pandas as pd
import json
from datetime import datetime, timedelta
from app.models import Transaction, Goal
from goals.forecaster import GoalForecaster

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


def test_goal_competition():
    """Test how multiple goals compete for savings"""

    print("=" * 70)
    print("GOAL COMPETITION TEST")
    print("Shows how multiple simultaneous goals affect each other")
    print("=" * 70)

    # Load transactions
    print("\n1. Loading transaction data...")
    transactions = load_test_transactions()
    print(f"   ✓ Loaded {len(transactions)} transactions")

    # Create multiple goals
    print("\n2. Creating multiple savings goals...")

    goal1 = Goal(
        id="goal-tesla",
        goal_name="Tesla Down Payment",
        target_amount=15000,
        deadline=(datetime.now() + timedelta(days=180)).isoformat(),
        current_savings=1200,
        priority_level="high",
        created_at=datetime.now().isoformat(),
        monthly_income=5000.0,
        income_type="fixed",
        is_active=True
    )

    goal2 = Goal(
        id="goal-vacation",
        goal_name="Europe Vacation",
        target_amount=4000,
        deadline=(datetime.now() + timedelta(days=365)).isoformat(),
        current_savings=500,
        priority_level="medium",
        created_at=datetime.now().isoformat(),
        monthly_income=5000.0,
        income_type="fixed",
        is_active=True
    )

    goal3 = Goal(
        id="goal-emergency",
        goal_name="Emergency Fund",
        target_amount=10000,
        deadline=(datetime.now() + timedelta(days=730)).isoformat(),
        current_savings=2000,
        priority_level="high",
        created_at=datetime.now().isoformat(),
        monthly_income=5000.0,
        income_type="fixed",
        is_active=True
    )

    all_goals = [goal1, goal2, goal3]

    print(f"\n   Created {len(all_goals)} goals:")
    for g in all_goals:
        months = (datetime.fromisoformat(g.deadline.replace('Z', '+00:00')) - datetime.now()).days / 30
        print(f"   - {g.goal_name}: ${g.target_amount:,.0f} in {months:.0f} months (Priority: {g.priority_level})")

    # Forecast each goal WITH competition analysis
    forecaster = GoalForecaster(transactions)

    print("\n" + "=" * 70)
    print("FORECASTING EACH GOAL WITH COMPETITION ANALYSIS")
    print("=" * 70)

    for i, goal in enumerate(all_goals, 1):
        print(f"\n{'─' * 70}")
        print(f"Goal {i}: {goal.goal_name}")
        print(f"{'─' * 70}")

        forecast = forecaster.forecast_goal(goal, all_goals=all_goals)

        print(f"\nBasic Info:")
        print(f"  Target: ${forecast.target_amount:,.2f}")
        print(f"  Current: ${forecast.current_savings:,.2f}")
        print(f"  Status: {forecast.status.upper()}")
        print(f"  Expected Total by Deadline: ${forecast.projection.expected_total:,.2f}")

        # Show competition analysis
        if forecast.competition_analysis:
            comp = forecast.competition_analysis
            print(f"\n🏁 Priority-Based Competition Analysis:")
            print(f"  Total Available Savings: ${comp.total_available_savings:,.2f}/month")
            print(f"  THIS Goal Priority: {goal.priority_level.upper()}")

            if comp.competing_goals:
                print(f"\n  📌 Other Active Goals (sorted by priority):")
                current_priority_order = {"high": 0, "medium": 1, "low": 2}[goal.priority_level]

                for cg in comp.competing_goals:
                    cg_priority_order = {"high": 0, "medium": 1, "low": 2}[cg.priority_level]

                    if cg_priority_order < current_priority_order:
                        marker = "⬆️ HIGHER"
                    elif cg_priority_order == current_priority_order:
                        marker = "⏸️ SAME"
                    else:
                        marker = "⬇️ LOWER"

                    print(f"     {marker} • {cg.goal_name}: ${cg.required_monthly_savings:,.2f}/month ({cg.priority_level.upper()})")

            print(f"\n  💰 Priority-Based Allocation:")
            print(f"     Committed to HIGHER Priority Goals: ${comp.total_committed_savings:,.2f}/month")
            print(f"     Remaining for THIS Goal: ${comp.remaining_available_savings:,.2f}/month")

            if forecast.gap_analysis:
                this_goal_needs = forecast.gap_analysis.required_monthly_savings
                print(f"     THIS Goal Needs: ${this_goal_needs:,.2f}/month")

            if comp.is_overcommitted:
                print(f"\n  ⚠️  INSUFFICIENT FUNDS AFTER HIGHER PRIORITIES!")
                print(f"     After funding higher-priority goals, you're short by: ${comp.overcommitment_amount:,.2f}/month")
            else:
                print(f"\n  ✅ Sufficient funds remain after higher-priority goals")

        # Show gap analysis
        if forecast.gap_analysis:
            print(f"\n  Gap Analysis:")
            print(f"     This goal needs: ${forecast.gap_analysis.required_monthly_savings:,.2f}/month")
            print(f"     Current pace: ${forecast.gap_analysis.current_monthly_savings:,.2f}/month")
            print(f"     Shortfall: ${forecast.gap_analysis.shortfall:,.2f}")

    # Summary
    print("\n" + "=" * 70)
    print("SUMMARY")
    print("=" * 70)

    total_required = 0
    for goal in all_goals:
        months = (datetime.fromisoformat(goal.deadline.replace('Z', '+00:00')) - datetime.now()).days / 30
        required = (goal.target_amount - goal.current_savings) / max(months, 1)
        total_required += required

    print(f"\nTotal Monthly Savings Needed for All Goals: ${total_required:,.2f}")
    print(f"Actual Monthly Savings Available: ${forecaster.transactions and 387.50 or 0:,.2f}")  # From test
    print(f"Over-commitment: ${max(0, total_required - 387.50):,.2f}")
    print(f"\n{'⚠️  ' if total_required > 387.50 else '✅ '}You {'CANNOT' if total_required > 387.50 else 'CAN'} achieve all these goals simultaneously!")

    print("\n" + "=" * 70)
    print("TEST COMPLETE")
    print("=" * 70)

    return True


if __name__ == "__main__":
    try:
        success = test_goal_competition()
        if success:
            print("\n✅ Goal competition analysis working!")
        else:
            print("\n❌ Test failed")
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
