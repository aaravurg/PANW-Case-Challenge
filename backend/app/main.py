from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
from typing import List, Optional, Dict, Any
from pydantic import BaseModel

from app.models import (
    Transaction, Insight, Goal, GoalForecast, SubscriptionSummary,
    InvestmentCapacityRequest, InvestmentCapacityResponse
)
from app.config import CORS_ORIGINS, ENV_FILE, DEFAULT_USER_ID
from app.utils import load_transactions_from_csv, validate_api_key
from app.logger import setup_logging, get_logger
from insights.pipeline import InsightsPipeline
from goals.storage import get_goal_storage
from goals.forecaster import GoalForecaster
from goals.recommendations import RecommendationEngine
from spending.subscription_detector import SubscriptionDetector
from app.investment_calculator import InvestmentCapacityCalculator
from nlp_coach.coach import NaturalLanguageCoach

# Setup logging
setup_logging()
logger = get_logger(__name__)

# Load environment variables
load_dotenv(ENV_FILE)
logger.info(f"Environment loaded from {ENV_FILE}")

app = FastAPI(title="PANW Case Challenge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize insights pipeline (lazy loading)
_insights_pipeline = None


def get_pipeline():
    """Get or create insights pipeline instance."""
    global _insights_pipeline
    if _insights_pipeline is None:
        try:
            api_key = validate_api_key("GEMINI_API_KEY")
            _insights_pipeline = InsightsPipeline(anthropic_api_key=api_key)
        except ValueError as e:
            raise HTTPException(status_code=500, detail=str(e))
    return _insights_pipeline

@app.get("/")
async def root():
    return {"message": "Welcome to PANW Case Challenge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/insights", response_model=List[Insight])
async def get_insights(user_name: str = "Aarav", top_n: int = 7, buffer: int = 5):
    """
    Generate intelligent spending insights from transaction data.

    Args:
        user_name: Name for personalization
        top_n: Number of insights to display
        buffer: Additional insights for queue

    Returns:
        List of insights or empty list if API key not configured
    """
    if not os.getenv("GEMINI_API_KEY"):
        logger.warning("Insights paused: GEMINI_API_KEY not configured")
        return []

    try:
        transactions = load_transactions_from_csv()
        insights_pipeline = get_pipeline()
        insights = insights_pipeline.generate_insights(
            transactions=transactions,
            user_name=user_name,
            top_n=top_n + buffer
        )
        return insights

    except FileNotFoundError as e:
        logger.error(f"Transaction data not found: {e}")
        raise HTTPException(status_code=404, detail="Transaction data not found")
    except Exception as e:
        logger.error(f"Error generating insights: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@app.get("/api/transactions/summary")
async def get_transactions_summary():
    """Get summary statistics for transaction data."""
    try:
        transactions = load_transactions_from_csv()

        dates = [t.date for t in transactions]
        spending = sum(t.amount for t in transactions if t.amount < 0)
        income = sum(t.amount for t in transactions if t.amount > 0)

        return {
            "total_transactions": len(transactions),
            "date_range": {
                "start": min(dates).isoformat() if dates else None,
                "end": max(dates).isoformat() if dates else None
            },
            "total_spending": spending,
            "total_income": income
        }

    except FileNotFoundError:
        raise HTTPException(status_code=404, detail="Transaction data not found")
    except Exception as e:
        logger.error(f"Error getting summary: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")


# ============================================================================
# GOAL FORECASTING ENDPOINTS
# ============================================================================

@app.post("/api/goals", response_model=Goal)
async def create_goal(
    goal_name: str,
    target_amount: float,
    deadline: str,
    monthly_income: float,
    current_savings: float = 0.0,
    priority_level: str = "medium",
    income_type: str = "fixed",
    user_id: str = DEFAULT_USER_ID
):
    """Create a new savings goal."""
    try:
        storage = get_goal_storage()
        goal = storage.create_goal(
            goal_name=goal_name,
            target_amount=target_amount,
            deadline=deadline,
            monthly_income=monthly_income,
            current_savings=current_savings,
            priority_level=priority_level,
            income_type=income_type,
            user_id=user_id
        )
        return goal
    except Exception as e:
        logger.error(f"Error creating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")


@app.get("/api/goals", response_model=List[Goal])
async def get_goals(user_id: str = DEFAULT_USER_ID):
    """Get all goals for a user."""
    try:
        storage = get_goal_storage()
        goals = storage.get_all_goals(user_id=user_id)
        return goals
    except Exception as e:
        logger.error(f"Error fetching goals: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")


@app.get("/api/goals/{goal_id}", response_model=Goal)
async def get_goal(goal_id: str, user_id: str = DEFAULT_USER_ID):
    """Get a specific goal by ID."""
    try:
        storage = get_goal_storage()
        goal = storage.get_goal(goal_id, user_id=user_id)

        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error fetching goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error fetching goal: {str(e)}")


@app.get("/api/goals/{goal_id}/forecast", response_model=GoalForecast)
async def get_goal_forecast(goal_id: str, user_id: str = DEFAULT_USER_ID):
    """
    Get forecast for a goal with ML-powered predictions and recommendations.
    Uses Prophet for spending forecasts and derives savings projections.
    """
    try:
        storage = get_goal_storage()
        goal = storage.get_goal(goal_id, user_id=user_id)

        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        transactions = load_transactions_from_csv()
        all_goals = storage.get_all_goals(user_id=user_id)

        forecaster = GoalForecaster(transactions)
        forecast = forecaster.forecast_goal(goal, all_goals=all_goals)

        if forecast.gap_analysis is not None:
            rec_engine = RecommendationEngine(transactions)
            recommendations = rec_engine.generate_recommendations(
                gap_analysis=forecast.gap_analysis,
                max_recommendations=3
            )
            forecast.recommendations = recommendations

        return forecast

    except HTTPException:
        raise
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error generating forecast: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


@app.put("/api/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: str,
    user_id: str = DEFAULT_USER_ID,
    goal_name: str = None,
    target_amount: float = None,
    deadline: str = None,
    current_savings: float = None,
    priority_level: str = None,
    monthly_income: float = None,
    income_type: str = None
):
    """Update an existing goal with partial fields."""
    try:
        storage = get_goal_storage()

        updates = {}
        if goal_name is not None:
            updates['goal_name'] = goal_name
        if target_amount is not None:
            updates['target_amount'] = target_amount
        if deadline is not None:
            updates['deadline'] = deadline
        if current_savings is not None:
            updates['current_savings'] = current_savings
        if priority_level is not None:
            updates['priority_level'] = priority_level
        if monthly_income is not None:
            updates['monthly_income'] = monthly_income
        if income_type is not None:
            updates['income_type'] = income_type

        goal = storage.update_goal(goal_id, user_id=user_id, **updates)

        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        return goal
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error updating goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error updating goal: {str(e)}")


@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = DEFAULT_USER_ID):
    """Delete a goal by ID."""
    try:
        storage = get_goal_storage()
        success = storage.delete_goal(goal_id, user_id=user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")

        return {"message": "Goal deleted successfully", "goal_id": goal_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error deleting goal: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error deleting goal: {str(e)}")


# ============================================================================
# SUBSCRIPTION DETECTION ENDPOINTS
# ============================================================================

@app.get("/api/subscriptions", response_model=SubscriptionSummary)
async def detect_subscriptions():
    """
    Detect recurring subscriptions using pattern analysis.
    Identifies gray charges, price increases, and trial conversions.
    """
    try:
        transactions = load_transactions_from_csv()
        detector = SubscriptionDetector(transactions)
        summary = detector.detect_subscriptions()
        return summary

    except Exception as e:
        logger.error(f"Error detecting subscriptions: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error detecting subscriptions: {str(e)}")


# ============================================================================
# INVESTMENT CAPACITY PREDICTOR ENDPOINTS
# ============================================================================

@app.post("/api/investment-capacity", response_model=InvestmentCapacityResponse)
async def calculate_investment_capacity(request: InvestmentCapacityRequest):
    """
    Calculate monthly investable surplus after expenses and goal commitments.
    Provides educational content on investment options for beginners.
    """
    try:
        transactions = load_transactions_from_csv()
        storage = get_goal_storage()
        goals = storage.get_all_goals(user_id=request.user_id)

        calculator = InvestmentCapacityCalculator(transactions, goals)
        result = calculator.calculate(
            monthly_income=request.monthly_income,
            is_gross_income=request.is_gross_income
        )

        return result

    except Exception as e:
        logger.error(f"Error calculating investment capacity: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error calculating investment capacity: {str(e)}")


# ============================================================================
# NATURAL LANGUAGE COACH ENDPOINTS
# ============================================================================

class ChatMessage(BaseModel):
    """Individual message in chat history"""
    role: str
    content: Any


class ChatRequest(BaseModel):
    """Request model for natural language coach chat"""
    message: str  # User's message
    conversation_history: Optional[List[Dict[str, Any]]] = []  # Previous messages
    user_id: str = "default_user"  # User identifier for fetching goals


class ChatResponse(BaseModel):
    """Response model for natural language coach chat"""
    response: str  # Assistant's response text
    function_calls: List[Dict[str, Any]]  # Functions that were called
    conversation_history: List[Dict[str, Any]]  # Updated conversation history


@app.post("/api/coach/chat", response_model=ChatResponse)
async def chat_with_coach(request: ChatRequest):
    """
    Natural language interface for querying financial data.
    Uses Gemini function calling to interpret questions and execute data queries.
    """
    if not os.getenv("GEMINI_CHATBOT_API_KEY"):
        raise HTTPException(
            status_code=503,
            detail="Natural Language Coach not configured. GEMINI_CHATBOT_API_KEY missing."
        )

    try:
        transactions = load_transactions_from_csv()
        storage = get_goal_storage()
        goals = storage.get_all_goals(user_id=request.user_id)

        coach = NaturalLanguageCoach(transactions, goals)
        result = coach.chat(
            user_message=request.message,
            conversation_history=request.conversation_history
        )

        return ChatResponse(
            response=result["response"],
            function_calls=result["function_calls"],
            conversation_history=result["conversation_history"]
        )

    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"Error in natural language coach: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=f"Error processing chat: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
