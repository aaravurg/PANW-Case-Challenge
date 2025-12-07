import google.generativeai as genai
import os
import json
from typing import List, Tuple
from datetime import datetime
from app.models import Trigger, Insight
from insights.priority_scorer import PriorityScorer
from insights.details_builder import InsightDetailsBuilder


class InsightGenerator:
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        genai.configure(api_key=self.api_key)
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_insights(self, scored_triggers: List[Tuple[Trigger, float]],
                         user_name: str = "there", account_age_months: int = None, aggregator = None) -> List[Insight]:
        if not scored_triggers:
            return []

        trigger_data = self._prepare_trigger_data(scored_triggers, account_age_months)
        insights_json = self._call_claude_api(trigger_data, user_name, account_age_months)
        insights = self._parse_insights(insights_json, scored_triggers, aggregator)

        return insights

    def _prepare_trigger_data(self, scored_triggers: List[Tuple[Trigger, float]], account_age_months: int = None) -> List[dict]:
        trigger_list = []

        for trigger, score in scored_triggers:
            trigger_dict = {
                "type": trigger.type,
                "priority_score": round(score, 2)
            }

            # Add relevant fields based on trigger type
            if trigger.category:
                trigger_dict["category"] = trigger.category
            if trigger.merchant:
                trigger_dict["merchant"] = trigger.merchant
            if trigger.this_month is not None:
                # For lifetime milestones, use clearer field names
                if 'lifetime' in trigger.type or 'milestone' in trigger.type:
                    trigger_dict["lifetime_total"] = round(trigger.this_month, 2)
                else:
                    trigger_dict["this_month"] = round(trigger.this_month, 2)
            if trigger.last_month is not None:
                trigger_dict["last_month"] = round(trigger.last_month, 2)
            if trigger.average is not None:
                trigger_dict["average"] = round(trigger.average, 2)
            if trigger.percent_change is not None:
                trigger_dict["percent_change"] = round(trigger.percent_change, 1)
            if trigger.dollar_change is not None:
                trigger_dict["dollar_change"] = round(trigger.dollar_change, 2)
            if trigger.top_merchants:
                trigger_dict["top_merchants"] = trigger.top_merchants
            if trigger.visit_count is not None:
                trigger_dict["visit_count"] = trigger.visit_count
            if trigger.savings_rate is not None:
                trigger_dict["savings_rate"] = round(trigger.savings_rate, 1)
            if trigger.weekend_spend is not None:
                trigger_dict["weekend_spend"] = round(trigger.weekend_spend, 2)
            if trigger.weekday_spend is not None:
                trigger_dict["weekday_spend"] = round(trigger.weekday_spend, 2)

            # Add raw_data if present (for additional context like timeframes, trends, etc.)
            if trigger.raw_data:
                trigger_dict["context"] = trigger.raw_data

            trigger_list.append(trigger_dict)

        return trigger_list

    def _call_claude_api(self, trigger_data: List[dict], user_name: str, account_age_months: int = None) -> str:
        context = f"User has {account_age_months} months of transaction history." if account_age_months else "New user."

        prompt = f"""You are a personal finance assistant. Create insights from the following financial triggers.

Context: {context}
User's name: {user_name}

Important data fields:
- For milestone triggers: "lifetime_total" = total spending, "milestone_amount" = dollar threshold crossed
- For spending triggers: "this_month" = current spending, "last_month" = previous spending

Guidelines:
- Write conversational, engaging insights
- Use specific numbers and percentages
- Include actionable advice with yearly projections
- Keep headlines under 10 words
- Make savings recommendations tangible and relatable

Insight types:
- "win": positive achievements
- "alert": needs attention
- "anomaly": unusual patterns

Trigger data:
{json.dumps(trigger_data, indent=2)}

Return ONLY valid JSON (no markdown):
[
  {{
    "type": "win|alert|anomaly",
    "emoji": "relevant emoji",
    "headline": "Catchy headline",
    "description": "Detailed explanation with numbers and advice."
  }}
]"""

        try:
            generation_config = {
                "temperature": 0.9,
                "max_output_tokens": 8192,
                "top_p": 0.95,
                "top_k": 40,
            }

            safety_settings = [
                {
                    "category": "HARM_CATEGORY_HARASSMENT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_HATE_SPEECH",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
                    "threshold": "BLOCK_NONE"
                },
                {
                    "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                    "threshold": "BLOCK_NONE"
                }
            ]

            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            if not response.candidates:
                print("No candidates in response, using fallback")
                return self._generate_fallback_insights(trigger_data)

            candidate = response.candidates[0]
            finish_reason = candidate.finish_reason

            if finish_reason != 1:
                print(f"Response finished with reason {finish_reason}, using fallback")
                return self._generate_fallback_insights(trigger_data)

            if not candidate.content.parts:
                print("No parts in response content, using fallback")
                return self._generate_fallback_insights(trigger_data)

            response_text = candidate.content.parts[0].text.strip()

            if response_text.startswith("```"):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            return response_text

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            import traceback
            traceback.print_exc()
            return self._generate_fallback_insights(trigger_data)

    def _generate_fallback_insights(self, trigger_data: List[dict]) -> str:
        fallback_insights = []

        for trigger in trigger_data[:5]:
            if trigger["type"] == "spending_spike":
                fallback_insights.append({
                    "type": "alert",
                    "emoji": "📈",
                    "headline": f"{trigger.get('category', 'Spending')} is up",
                    "description": f"You spent ${trigger.get('this_month', 0):.2f} on {trigger.get('category', 'this category')} this month, which is {trigger.get('percent_change', 0):.1f}% more than usual."
                })
            elif trigger["type"] == "spending_win":
                fallback_insights.append({
                    "type": "win",
                    "emoji": "🎉",
                    "headline": f"{trigger.get('category', 'Spending')} is down",
                    "description": f"Great job! You spent {trigger.get('percent_change', 0):.1f}% less on {trigger.get('category', 'this category')} this month."
                })

        return json.dumps(fallback_insights)

    def _parse_insights(self, insights_json: str, scored_triggers: List[Tuple[Trigger, float]], aggregator = None) -> List[Insight]:
        try:
            insights_data = json.loads(insights_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {insights_json}")
            return []

        insights = []
        for i, data in enumerate(insights_data):
            trigger, score = scored_triggers[i] if i < len(scored_triggers) else (None, 0)

            details = None
            if trigger and aggregator:
                details = InsightDetailsBuilder.build_details(trigger, aggregator)

            insight = Insight(
                id=f"insight_{i}_{datetime.now().timestamp()}",
                type=data.get("type", "alert"),
                emoji=data.get("emoji", "💡"),
                headline=data.get("headline", "Financial Insight"),
                description=data.get("description", "Review your spending patterns."),
                timestamp=self._format_timestamp(),
                priority_score=score,
                trigger_type=trigger.type if trigger else "unknown",
                details=details
            )
            insights.append(insight)

        return insights

    def _format_timestamp(self) -> str:
        return "Just now"
