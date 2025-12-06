from openai import OpenAI
import os
import json
from typing import List, Tuple
from datetime import datetime
from models import Trigger, Insight
from priority_scorer import PriorityScorer
import httpx


class InsightGenerator:
    """Stage 4: Generates natural language insights using Groq LLM"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        if not self.api_key:
            raise ValueError("GROQ_API_KEY not found in environment variables")

        # Create httpx client without proxies to avoid compatibility issues
        http_client = httpx.Client(timeout=60.0)

        self.client = OpenAI(
            api_key=self.api_key,
            base_url="https://api.groq.com/openai/v1",
            http_client=http_client
        )

    def generate_insights(self, scored_triggers: List[Tuple[Trigger, float]],
                         user_name: str = "there") -> List[Insight]:
        """Generate natural language insights from triggers"""

        if not scored_triggers:
            return []

        # Prepare trigger data for LLM
        trigger_data = self._prepare_trigger_data(scored_triggers)

        # Call Claude API
        insights_json = self._call_claude_api(trigger_data, user_name)

        # Parse and create Insight objects
        insights = self._parse_insights(insights_json, scored_triggers)

        return insights

    def _prepare_trigger_data(self, scored_triggers: List[Tuple[Trigger, float]]) -> List[dict]:
        """Convert triggers to LLM-friendly format"""
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

            trigger_list.append(trigger_dict)

        return trigger_list

    def _call_claude_api(self, trigger_data: List[dict], user_name: str) -> str:
        """Call Groq API to generate insights"""

        prompt = f"""You are a friendly, insightful personal finance assistant. Convert the following financial triggers into natural, actionable insights for the user.

Guidelines:
1. Use specific dollar amounts and percentages from the data
2. Be conversational and non-judgmental in tone
3. For each insight, include:
   - A catchy headline (3-8 words)
   - A detailed description (2-3 sentences) that explains the pattern and suggests an action
   - An appropriate emoji that fits the insight type
   - The insight type: "win" (positive news), "alert" (something to pay attention to), or "anomaly" (unusual pattern)
4. Even if spending is high in some areas, try to include at least one positive insight
5. Make insights personal and actionable
6. User's name: {user_name}

Trigger data:
{json.dumps(trigger_data, indent=2)}

Return ONLY a valid JSON array with this exact structure (no markdown, no code blocks):
[
  {{
    "type": "win|alert|anomaly",
    "emoji": "relevant emoji",
    "headline": "Catchy headline here",
    "description": "Detailed explanation with specific numbers and actionable advice."
  }}
]

Return the JSON array now:"""

        try:
            completion = self.client.chat.completions.create(
                model="llama-3.3-70b-versatile",
                messages=[
                    {"role": "system", "content": "You are a helpful financial insights assistant. Always respond with valid JSON only."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.7,
                max_tokens=2048
            )

            response_text = completion.choices[0].message.content.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            return response_text

        except Exception as e:
            print(f"Error calling Groq API: {e}")
            # Return fallback insights
            return self._generate_fallback_insights(trigger_data)

    def _generate_fallback_insights(self, trigger_data: List[dict]) -> str:
        """Generate simple fallback insights if API fails"""
        fallback_insights = []

        for trigger in trigger_data[:5]:  # Limit to 5
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

    def _parse_insights(self, insights_json: str, scored_triggers: List[Tuple[Trigger, float]]) -> List[Insight]:
        """Parse LLM response into Insight objects"""
        try:
            insights_data = json.loads(insights_json)
        except json.JSONDecodeError as e:
            print(f"Error parsing JSON: {e}")
            print(f"Response was: {insights_json}")
            return []

        insights = []
        for i, data in enumerate(insights_data):
            # Get corresponding trigger and score
            trigger, score = scored_triggers[i] if i < len(scored_triggers) else (None, 0)

            insight = Insight(
                id=f"insight_{i}_{datetime.now().timestamp()}",
                type=data.get("type", "alert"),
                emoji=data.get("emoji", "💡"),
                headline=data.get("headline", "Financial Insight"),
                description=data.get("description", "Review your spending patterns."),
                timestamp=self._format_timestamp(),
                priority_score=score,
                trigger_type=trigger.type if trigger else "unknown"
            )
            insights.append(insight)

        return insights

    def _format_timestamp(self) -> str:
        """Format current timestamp for display"""
        now = datetime.now()
        return "Just now"
