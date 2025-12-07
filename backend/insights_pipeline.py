from typing import List
from models import Transaction, Insight
from data_aggregator import DataAggregator
from comprehensive_trigger_detector import ComprehensiveTriggerDetector
from comprehensive_priority_scorer import ComprehensivePriorityScorer
from insight_generator import InsightGenerator


class InsightsPipeline:
    """
    Orchestrates the complete Intelligent Spending Insights pipeline:
    Stage 1: Comprehensive Multi-Dimensional Data Aggregation
    Stage 2: Comprehensive Trigger Detection (All Timeframes & Patterns)
    Stage 3: Priority Scoring and Deduplication
    Stage 4: LLM Text Generation with Enhanced Context
    """

    def __init__(self, anthropic_api_key: str = None):
        self.insight_generator = InsightGenerator(api_key=anthropic_api_key)

    def generate_insights(self, transactions: List[Transaction],
                         user_name: str = "there",
                         top_n: int = 7) -> List[Insight]:
        """
        Run the complete comprehensive pipeline to generate intelligent insights

        Args:
            transactions: List of user transactions (entire history)
            user_name: User's name for personalization
            top_n: Number of top insights to return

        Returns:
            List of generated insights with comprehensive analysis
        """

        # STAGE 1: COMPREHENSIVE DATA AGGREGATION
        print("\n" + "="*80)
        print("STAGE 1: Multi-Dimensional Data Aggregation")
        print("="*80)

        aggregator = DataAggregator(transactions)
        aggregation_results = aggregator.aggregate_all()

        # Display aggregation summary
        derived = aggregator.derived_metrics
        print(f"\n📊 Account Overview:")
        print(f"  • Account age: {derived.get('account_age_months', 0)} months ({derived.get('account_age_days', 0)} days)")
        print(f"  • Overall monthly average: ${derived.get('overall_monthly_avg', 0):,.2f}")
        print(f"  • Current month: {derived.get('current_month', 'N/A')}")
        print(f"  • Current quarter: {derived.get('current_quarter', 'N/A')}")

        print(f"\n📈 Data Aggregated:")
        print(f"  • Weekly periods tracked: {len(aggregator.aggregations['by_week']['sorted_keys'])}")
        print(f"  • Monthly periods tracked: {len(aggregator.aggregations['by_month']['sorted_keys'])}")
        print(f"  • Quarterly periods tracked: {len(aggregator.aggregations['by_quarter']['sorted_keys'])}")
        print(f"  • Yearly periods tracked: {len(aggregator.aggregations['by_year']['sorted_keys'])}")
        print(f"  • Categories tracked: {len(aggregator.aggregations['by_category'])}")
        print(f"  • Merchants tracked: {len(aggregator.aggregations['by_merchant'])}")

        # STAGE 2: COMPREHENSIVE TRIGGER DETECTION
        print("\n" + "="*80)
        print("STAGE 2: Comprehensive Trigger Detection")
        print("="*80)

        detector = ComprehensiveTriggerDetector(aggregator)
        all_triggers = detector.detect_all_triggers()

        print(f"\n🔍 Total triggers detected: {len(all_triggers)}")

        # Group triggers by category for summary
        trigger_categories = {
            'short_term': ['weekly_spending_spike', 'weekly_spending_win', 'weekly_category_spike',
                          'monthly_spending_spike', 'monthly_spending_win', 'category_above_average'],
            'medium_term': ['quarterly_trend_increase', 'quarterly_trend_decrease',
                           'three_month_sustained_trend', 'six_month_sustained_trend', 'category_rolling_trend'],
            'long_term': ['year_over_year_change', 'category_year_over_year', 'all_time_high_spending',
                         'all_time_low_spending', 'category_all_time_high', 'lifetime_spending_milestone',
                         'merchant_lifetime_milestone', 'annual_growth_rate', 'lifestyle_inflation'],
            'seasonal': ['seasonal_high_spend_month', 'holiday_season_pattern'],
            'behavioral': ['weekend_warrior', 'weekday_spender', 'merchant_loyalty',
                          'new_significant_merchant', 'category_dominance'],
            'positive': ['savings_streak', 'income_positive_streak', 'category_improvement_trend',
                        'overall_improvement_trend']
        }

        for category, trigger_types in trigger_categories.items():
            count = sum(1 for t in all_triggers if t.type in trigger_types)
            if count > 0:
                print(f"  • {category.replace('_', ' ').title()}: {count} triggers")

        # Show sample triggers
        print("\n📋 Sample Triggers:")
        for trigger in all_triggers[:8]:
            context = ""
            if trigger.category:
                context = f" [{trigger.category}]"
            elif trigger.merchant:
                context = f" [{trigger.merchant}]"

            if trigger.percent_change:
                context += f" ({trigger.percent_change:+.1f}%)"

            print(f"  • {trigger.type}{context}")

        if not all_triggers:
            print("\n⚠️  No triggers detected. Returning empty insights.")
            return []

        # STAGE 3: PRIORITY SCORING AND DEDUPLICATION
        print("\n" + "="*80)
        print("STAGE 3: Priority Scoring & Deduplication")
        print("="*80)

        scorer = ComprehensivePriorityScorer()
        scored_triggers = scorer.score_and_rank(all_triggers, top_n=top_n)

        print(f"\n⭐ Top {len(scored_triggers)} insights selected after prioritization:")
        for i, (trigger, score) in enumerate(scored_triggers[:top_n], 1):
            context = ""
            if trigger.category:
                context = f" - {trigger.category}"
            elif trigger.merchant:
                context = f" - {trigger.merchant}"

            print(f"  {i}. {trigger.type}{context} (score: {score:.0f})")

        # STAGE 4: LLM TEXT GENERATION
        print("\n" + "="*80)
        print("STAGE 4: Natural Language Insight Generation")
        print("="*80)

        account_age_months = derived.get('account_age_months', None)
        insights = self.insight_generator.generate_insights(
            scored_triggers,
            user_name,
            account_age_months,
            aggregator  # Pass aggregator for transaction retrieval
        )

        print(f"\n✅ Generated {len(insights)} natural language insights")

        # Display insight summary
        insight_types = {'win': 0, 'alert': 0, 'anomaly': 0}
        for insight in insights:
            insight_types[insight.type] = insight_types.get(insight.type, 0) + 1

        print(f"\n📊 Insight Breakdown:")
        print(f"  • Wins (positive): {insight_types.get('win', 0)}")
        print(f"  • Alerts (attention needed): {insight_types.get('alert', 0)}")
        print(f"  • Anomalies (patterns): {insight_types.get('anomaly', 0)}")

        print("\n" + "="*80)
        print("✨ Pipeline Complete!")
        print("="*80 + "\n")

        return insights
