from typing import List
from models import Transaction, Insight
from data_aggregator import DataAggregator
from trigger_detector import TriggerDetector
from priority_scorer import PriorityScorer
from insight_generator import InsightGenerator


class InsightsPipeline:
    """
    Orchestrates the complete Intelligent Spending Insights pipeline:
    Stage 1: Data Aggregation
    Stage 2: Trigger Detection
    Stage 3: Priority Scoring
    Stage 4: LLM Text Generation
    """

    def __init__(self, anthropic_api_key: str = None):
        self.insight_generator = InsightGenerator(api_key=anthropic_api_key)

    def generate_insights(self, transactions: List[Transaction],
                         user_name: str = "there",
                         top_n: int = 7) -> List[Insight]:
        """
        Run the complete pipeline to generate insights

        Args:
            transactions: List of user transactions
            user_name: User's name for personalization
            top_n: Number of top insights to return

        Returns:
            List of generated insights
        """

        # STAGE 1: DATA AGGREGATION
        print("Stage 1: Aggregating transaction data...")
        aggregator = DataAggregator(transactions)
        stats = aggregator.aggregate()

        print(f"  - Total spending this month: ${stats.total_spending_this_month:.2f}")
        print(f"  - Total income this month: ${stats.total_income_this_month:.2f}")
        print(f"  - Categories tracked: {len(stats.spending_by_category_this_month)}")

        # STAGE 2: TRIGGER DETECTION
        print("\nStage 2: Detecting spending triggers...")
        detector = TriggerDetector(stats, aggregator)
        triggers = detector.detect_all_triggers()

        print(f"  - Triggers detected: {len(triggers)}")
        for trigger in triggers[:5]:  # Show first 5
            print(f"    * {trigger.type}: {trigger.category or trigger.merchant or 'general'}")

        if not triggers:
            print("  - No triggers detected. Returning empty insights.")
            return []

        # STAGE 3: PRIORITY SCORING
        print("\nStage 3: Scoring and ranking triggers...")
        scorer = PriorityScorer(triggers)
        scored_triggers = scorer.score_and_rank(top_n=top_n)

        print(f"  - Top {len(scored_triggers)} triggers selected")
        for trigger, score in scored_triggers[:3]:  # Show top 3
            print(f"    * {trigger.type} (score: {score:.1f})")

        # STAGE 4: LLM TEXT GENERATION
        print("\nStage 4: Generating natural language insights...")
        insights = self.insight_generator.generate_insights(scored_triggers, user_name)

        print(f"  - Insights generated: {len(insights)}")

        return insights
