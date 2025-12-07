import os
import json
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from app.models import Transaction, Goal
from nlp_coach.query_functions import QueryEngine
from nlp_coach.fuzzy_matcher import FuzzyMatcher
from nlp_coach.function_schemas import GEMINI_FUNCTION_SCHEMAS


class NaturalLanguageCoach:
    def __init__(
        self,
        transactions: List[Transaction],
        goals: List[Goal],
        api_key: Optional[str] = None
    ):
        self.transactions = transactions
        self.goals = goals
        self.api_key = api_key or os.getenv("GEMINI_CHATBOT_API_KEY")

        if not self.api_key:
            raise ValueError("GEMINI_CHATBOT_API_KEY not found in environment or constructor")

        genai.configure(api_key=self.api_key)
        self.query_engine = QueryEngine(transactions, goals)
        self.fuzzy_matcher = FuzzyMatcher(transactions)

        self.system_instruction = """You are a helpful financial coach assistant that helps users understand their spending and financial data.

You have access to the user's transaction history, subscriptions, and savings goals. When users ask questions about their finances, use the available functions to query their data and provide clear, conversational answers.

Guidelines:
- Be friendly and conversational
- When presenting numbers, include context (comparisons, percentages, trends)
- Suggest actionable insights when appropriate
- Keep responses concise but informative

Date Handling:
- Today's date is December 31, 2025
- Calculate exact start and end dates for time periods (e.g., "last 2 months" → "2025-10-31" to "2025-12-31")
- Use start_date and end_date parameters with YYYY-MM-DD format
- Only use predefined time_range if the user explicitly uses those exact phrases"""

        self.model = genai.GenerativeModel(
            model_name='gemini-2.5-flash',
            tools=GEMINI_FUNCTION_SCHEMAS,
            system_instruction=self.system_instruction
        )

    def chat(
        self,
        user_message: str,
        conversation_history: Optional[List[Dict[str, Any]]] = None,
        max_iterations: int = 5
    ) -> Dict[str, Any]:
        if conversation_history:
            history = self._convert_history_to_gemini(conversation_history[-10:])
            chat = self.model.start_chat(history=history)
        else:
            chat = self.model.start_chat(history=[])

        function_calls_made = []
        iterations = 0

        try:
            response = chat.send_message(user_message)

            while iterations < max_iterations:
                iterations += 1
                has_function_call = False

                if response.candidates[0].content.parts:
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call') and part.function_call:
                            has_function_call = True
                            function_call = part.function_call
                            function_name = function_call.name
                            function_args = dict(function_call.args)
                            function_args = self._apply_fuzzy_matching(function_args)

                            try:
                                result = self._execute_function(function_name, function_args)
                                function_calls_made.append({
                                    "function": function_name,
                                    "arguments": function_args,
                                    "result": result
                                })

                                response = chat.send_message(
                                    genai.protos.Content(
                                        parts=[genai.protos.Part(
                                            function_response=genai.protos.FunctionResponse(
                                                name=function_name,
                                                response={'result': result}
                                            )
                                        )]
                                    )
                                )

                            except Exception as e:
                                response = chat.send_message(
                                    genai.protos.Content(
                                        parts=[genai.protos.Part(
                                            function_response=genai.protos.FunctionResponse(
                                                name=function_name,
                                                response={'error': str(e)}
                                            )
                                        )]
                                    )
                                )

                            break

                if not has_function_call:
                    final_text = response.text
                    updated_history = self._build_conversation_history(
                        chat.history,
                        function_calls_made
                    )

                    return {
                        "response": final_text,
                        "function_calls": function_calls_made,
                        "conversation_history": updated_history
                    }

        except Exception as e:
            print(f"Error in Gemini chat: {e}")
            import traceback
            traceback.print_exc()
            return {
                "response": f"I apologize, but I encountered an error processing your request: {str(e)}",
                "function_calls": function_calls_made,
                "conversation_history": []
            }

        # If we hit max iterations, return what we have
        return {
            "response": "I apologize, but I encountered an issue processing your request. Please try rephrasing your question.",
            "function_calls": function_calls_made,
            "conversation_history": []
        }

    def _convert_history_to_gemini(self, history: List[Dict[str, Any]]) -> List:
        gemini_history = []

        for msg in history:
            role = msg.get('role')
            content = msg.get('content')

            if role == 'user':
                gemini_history.append({
                    'role': 'user',
                    'parts': [{'text': content}]
                })
            elif role == 'assistant':
                gemini_history.append({
                    'role': 'model',
                    'parts': [{'text': content}]
                })

        return gemini_history

    def _build_conversation_history(self, gemini_history: List, function_calls: List) -> List[Dict[str, Any]]:
        history = []

        for msg in gemini_history:
            role = 'user' if msg.role == 'user' else 'assistant'
            content = ""

            for part in msg.parts:
                if hasattr(part, 'text') and part.text:
                    content += part.text

            if content:
                history.append({
                    'role': role,
                    'content': content
                })

        return history

    def _apply_fuzzy_matching(self, function_args: Dict[str, Any]) -> Dict[str, Any]:
        args = function_args.copy()

        if "merchant" in args and args["merchant"]:
            matched_merchant = self.fuzzy_matcher.match_merchant(args["merchant"])
            if matched_merchant:
                args["merchant"] = matched_merchant

        if "merchant_filter" in args and args["merchant_filter"]:
            matched_merchant = self.fuzzy_matcher.match_merchant(args["merchant_filter"])
            if matched_merchant:
                args["merchant_filter"] = matched_merchant

        if "merchant_keyword" in args and args["merchant_keyword"]:
            matched_merchant = self.fuzzy_matcher.match_merchant(args["merchant_keyword"], threshold=70)
            if matched_merchant:
                args["merchant_keyword"] = matched_merchant

        if "category" in args and args["category"]:
            matched_category = self.fuzzy_matcher.match_category(args["category"])
            if matched_category:
                args["category"] = matched_category

        if "category_filter" in args and args["category_filter"]:
            matched_category = self.fuzzy_matcher.match_category(args["category_filter"])
            if matched_category:
                args["category_filter"] = matched_category

        return args

    def _execute_function(self, function_name: str, function_args: Dict[str, Any]) -> Any:
        function_map = {
            "query_spending": self.query_engine.query_spending,
            "get_top_merchants": self.query_engine.get_top_merchants,
            "get_top_categories": self.query_engine.get_top_categories,
            "compare_spending": self.query_engine.compare_spending,
            "get_subscriptions": self.query_engine.get_subscriptions,
            "get_goal_progress": self.query_engine.get_goal_progress,
            "get_transaction_details": self.query_engine.get_transaction_details,
            "get_financial_summary": self.query_engine.get_financial_summary
        }

        if function_name not in function_map:
            raise ValueError(f"Unknown function: {function_name}")

        function = function_map[function_name]
        return function(**function_args)
