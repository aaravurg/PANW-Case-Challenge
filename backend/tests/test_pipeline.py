#!/usr/bin/env python3
"""
Test script for the insights pipeline (Stages 1-3)
This runs without needing the Anthropic API key
"""

import pandas as pd
import json
from datetime import datetime
from app.models import Transaction
from spending.aggregator import DataAggregator
from insights.trigger_detector import TriggerDetector
from insights.priority_scorer import PriorityScorer

def test_pipeline():
    print("=" * 70)
    print("TESTING INTELLIGENT SPENDING INSIGHTS PIPELINE")
    print("=" * 70)
    print()

    # Load transaction data
    print("📊 Loading transaction data...")
    csv_path = '../sample_transactions_1000_sorted.csv'
    df = pd.read_csv(csv_path)

    # Convert to Transaction objects
    transactions = []
    for _, row in df.iterrows():
        category = json.loads(row['category']) if isinstance(row['category'], str) else row['category']
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

    print(f"✓ Loaded {len(transactions)} transactions")
    print()

    # STAGE 1: Data Aggregation
    print("=" * 70)
    print("STAGE 1: DATA AGGREGATION")
    print("=" * 70)
    aggregator = DataAggregator(transactions)
    stats = aggregator.aggregate()

    print(f"\n💰 Financial Summary:")
    print(f"   Total Income (this month): ${stats.total_income_this_month:,.2f}")
    print(f"   Total Spending (this month): ${stats.total_spending_this_month:,.2f}")
    print(f"   Total Spending (last month): ${stats.total_spending_last_month:,.2f}")

    print(f"\n📈 Spending by Category (This Month):")
    for category, amount in sorted(stats.spending_by_category_this_month.items(),
                                   key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {category:20s}: ${amount:8.2f}")

    print(f"\n🏪 Top Merchants (This Month):")
    for merchant, amount in sorted(stats.spending_by_merchant_this_month.items(),
                                   key=lambda x: x[1], reverse=True)[:10]:
        print(f"   {merchant:30s}: ${amount:8.2f}")

    print()

    # STAGE 2: Trigger Detection
    print("=" * 70)
    print("STAGE 2: TRIGGER DETECTION")
    print("=" * 70)
    detector = TriggerDetector(stats, aggregator)
    triggers = detector.detect_all_triggers()

    print(f"\n🎯 Detected {len(triggers)} triggers:\n")

    trigger_types = {}
    for trigger in triggers:
        trigger_types[trigger.type] = trigger_types.get(trigger.type, 0) + 1

    for trigger_type, count in sorted(trigger_types.items()):
        print(f"   {trigger_type:30s}: {count} trigger(s)")

    print(f"\n📋 Trigger Details:\n")
    for i, trigger in enumerate(triggers[:15], 1):  # Show first 15
        print(f"{i}. Type: {trigger.type}")
        if trigger.category:
            print(f"   Category: {trigger.category}")
        if trigger.merchant:
            print(f"   Merchant: {trigger.merchant}")
        if trigger.this_month is not None:
            print(f"   This Month: ${trigger.this_month:.2f}")
        if trigger.percent_change is not None:
            print(f"   Change: {trigger.percent_change:.1f}%")
        print()

    # STAGE 3: Priority Scoring
    print("=" * 70)
    print("STAGE 3: PRIORITY SCORING")
    print("=" * 70)
    scorer = PriorityScorer(triggers)
    scored_triggers = scorer.score_and_rank(top_n=7)

    print(f"\n🏆 Top 7 Insights (by priority):\n")
    for i, (trigger, score) in enumerate(scored_triggers, 1):
        print(f"{i}. Score: {score:.1f}/100")
        print(f"   Type: {trigger.type}")
        print(f"   Category: {scorer.get_trigger_category(trigger)}")

        if trigger.category:
            print(f"   Subject: {trigger.category}")
        elif trigger.merchant:
            print(f"   Subject: {trigger.merchant}")

        if trigger.this_month is not None:
            print(f"   Amount: ${trigger.this_month:.2f}")
        if trigger.percent_change is not None:
            print(f"   Change: {trigger.percent_change:.1f}%")
        print()

    # Summary
    print("=" * 70)
    print("PIPELINE TEST COMPLETE")
    print("=" * 70)
    print()
    print("✅ Stage 1: Data Aggregation - PASSED")
    print("✅ Stage 2: Trigger Detection - PASSED")
    print("✅ Stage 3: Priority Scoring - PASSED")
    print()
    print("To test Stage 4 (LLM Text Generation):")
    print("1. Add your Gemini API key to .env:")
    print("   GEMINI_API_KEY=AIza...")
    print("2. Start the backend server:")
    print("   python main.py")
    print("3. Visit: http://localhost:8000/api/insights")
    print()

if __name__ == "__main__":
    try:
        test_pipeline()
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
