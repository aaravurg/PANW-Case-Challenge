import google.generativeai as genai
import os
import json
from typing import List, Tuple
from datetime import datetime
from models import Trigger, Insight
from priority_scorer import PriorityScorer
from insight_details_builder import InsightDetailsBuilder


class InsightGenerator:
    """Stage 4: Generates natural language insights using Gemini LLM"""

    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("GEMINI_API_KEY not found in environment variables")

        # Configure Gemini API
        genai.configure(api_key=self.api_key)

        # Initialize the model - using gemini-pro which is available in v1
        self.model = genai.GenerativeModel('gemini-2.5-flash')

    def generate_insights(self, scored_triggers: List[Tuple[Trigger, float]],
                         user_name: str = "there", account_age_months: int = None, aggregator = None) -> List[Insight]:
        """Generate natural language insights from triggers with comprehensive context"""

        if not scored_triggers:
            return []

        # Prepare trigger data for LLM
        trigger_data = self._prepare_trigger_data(scored_triggers, account_age_months)

        # Call Claude API with enhanced context
        insights_json = self._call_claude_api(trigger_data, user_name, account_age_months)

        # Parse and create Insight objects
        insights = self._parse_insights(insights_json, scored_triggers, aggregator)

        return insights

    def _prepare_trigger_data(self, scored_triggers: List[Tuple[Trigger, float]], account_age_months: int = None) -> List[dict]:
        """Convert triggers to LLM-friendly format with comprehensive context"""
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
        """Call Gemini API to generate insights with comprehensive context"""

        # TEMPORARILY DISABLED - Using fallback insights instead of calling Gemini
        return self._generate_fallback_insights(trigger_data)

        # Build context string
        context = f"User has {account_age_months} months of transaction history." if account_age_months else "New user."

        system_instruction = "You are a helpful financial insights assistant. Always respond with valid JSON only."

        prompt = f"""You are a witty, creative, and insightful personal finance assistant with a flair for making money management fun and engaging. Transform the following financial triggers into memorable, actionable insights that people will actually want to read and act on.

Context: {context}
User's name: {user_name}

Data Field Meanings - IMPORTANT:
- For "merchant_lifetime_milestone" and "lifetime_spending_milestone" triggers:
  * "lifetime_total" field = TOTAL LIFETIME spending at that merchant/overall
  * "visit_count" = total number of visits/transactions EVER
  * "milestone_amount" = DOLLAR threshold crossed (e.g., $500, $1000), NOT visit count!
  * "milestone_type" = "spending" means milestone is a dollar amount
  * Example: "You've spent $2,482 total at Safeway over 47 visits, crossing the $500 spending milestone"
  * DO NOT say "milestone of 500 visits" - the milestone is about dollars spent, not visits!
- For all other triggers:
  * "this_month" = current period spending
  * "last_month" = previous period spending

Creative Guidelines - BE BOLD AND ENGAGING:
1. Use specific dollar amounts and percentages, but present them in creative, memorable ways
2. Be conversational, witty, and engaging - think of yourself as a financially-savvy friend who makes personal finance actually interesting
3. For each insight, craft:
   - A punchy, creative headline (5-10 words) that grabs attention
     * Use wordplay, alliteration, or clever phrases when appropriate
     * Examples: "Coffee Connoisseur or Cash Drainer?", "Delivery App Devotee Alert!", "Savings Superstar Unlocked!"
   - A vivid description (2-3 sentences) that:
     * Explains patterns using creative comparisons or relatable examples
     * Uses engaging language: "That's enough to...", "Imagine if...", "You're on track to..."
     * Includes specific, actionable alternatives with yearly projections
     * Makes savings tangible: "That's a weekend getaway!", "Almost a new laptop!", "A year of Spotify!"
   - A perfectly fitting emoji that enhances the insight
   - The insight type: "win" (positive/celebration), "alert" (needs attention), or "anomaly" (unusual pattern)

4. Savings Advice - GET CREATIVE:
   - Don't just state savings - paint a picture of what they could do with that money
   - Use creative comparisons: "That $1,200/year could fund a vacation to Bali" or "Enough to subscribe to every streaming service and still have money left over"
   - Offer specific, creative alternatives: "Try meal-prepping Sundays - your wallet and future self will thank you"
   - Make it relatable and fun: "Swap that $6 latte for homemade coffee and treat yourself to something special with the savings"

5. Tone Variety - Keep It Fresh:
   - For wins: Enthusiastic and celebratory with creative praise ("You're absolutely crushing it!", "Financial genius alert!", "This deserves a victory lap!")
   - For alerts: Playful yet helpful ("Your wallet called - it needs a break", "Let's tame this spending beast together")
   - For anomalies: Intriguing and thought-provoking ("Plot twist in your spending story!", "Interesting discovery ahead!")

6. Creative Framing Ideas:
   - Use metaphors: "Your savings are blossoming", "You've tamed the takeout dragon"
   - Make comparisons: "That's enough coffees to caffeinate a small office"
   - Create scenarios: "If this trend continues, you'll save enough for..."
   - Use humor (when appropriate): Light, friendly jokes about common spending habits
   - Tell mini-stories: "Last month vs this month tells an interesting tale..."

7. Make Numbers Come Alive:
   - Instead of "$120 on coffee": "A $120 coffee habit - that's 4 lattes a week adding up to a $1,440 annual caffeine bill"
   - Instead of "20% increase": "Your spending shot up 20% - that's like adding an extra week of expenses to your month"
   - Transform yearly projections into exciting possibilities: "$2,400 saved = a road trip, new tech, or 6 months of gym membership"

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
            # Configure generation settings with higher token limit and safety settings
            generation_config = {
                "temperature": 0.9,  # Increased for more creative responses
                "max_output_tokens": 8192,  # Increased token limit
                "top_p": 0.95,
                "top_k": 40,
            }

            # Set safety settings to be more permissive for financial content
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

            # Generate content using Gemini
            response = self.model.generate_content(
                prompt,
                generation_config=generation_config,
                safety_settings=safety_settings
            )

            # Check if response has valid parts
            if not response.candidates:
                print("No candidates in response, using fallback")
                return self._generate_fallback_insights(trigger_data)

            candidate = response.candidates[0]

            # Check finish reason
            finish_reason = candidate.finish_reason
            if finish_reason != 1:  # 1 = STOP (successful completion)
                print(f"Response finished with reason {finish_reason}, using fallback")
                return self._generate_fallback_insights(trigger_data)

            # Get response text
            if not candidate.content.parts:
                print("No parts in response content, using fallback")
                return self._generate_fallback_insights(trigger_data)

            response_text = candidate.content.parts[0].text.strip()

            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split('\n')
                response_text = '\n'.join(lines[1:-1]) if len(lines) > 2 else response_text
                response_text = response_text.replace("```json", "").replace("```", "").strip()

            return response_text

        except Exception as e:
            print(f"Error calling Gemini API: {e}")
            import traceback
            traceback.print_exc()
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

    def _parse_insights(self, insights_json: str, scored_triggers: List[Tuple[Trigger, float]], aggregator = None) -> List[Insight]:
        """Parse LLM response into Insight objects with detailed calculation breakdowns"""
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

            # Generate detailed calculation breakdown with transactions
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
                details=details  # Attach calculation details with transactions
            )
            insights.append(insight)

        return insights

    def _format_timestamp(self) -> str:
        """Format current timestamp for display"""
        now = datetime.now()
        return "Just now"
