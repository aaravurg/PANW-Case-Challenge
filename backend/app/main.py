from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
import json
from typing import List
from datetime import datetime

from app.models import Transaction, Insight, Goal, GoalForecast, SubscriptionSummary
from insights.pipeline import InsightsPipeline
from goals.storage import get_goal_storage
from goals.forecaster import GoalForecaster
from goals.recommendations import RecommendationEngine
from spending.subscription_detector import SubscriptionDetector

# Load environment variables from root .env file
# Note: .env is in project root, need to go up 2 levels from app/main.py
env_path = os.path.join(os.path.dirname(__file__), '..', '..', '.env')
env_path_resolved = os.path.abspath(env_path)
load_dotenv(env_path)

# Debug: Check if .env loaded correctly
print(f"\n{'='*80}")
print(f"🔍 Environment Debug Info:")
print(f"  .env path: {env_path_resolved}")
print(f"  .env exists: {os.path.exists(env_path_resolved)}")
print(f"  GEMINI_API_KEY loaded: {'Yes ✅' if os.getenv('GEMINI_API_KEY') else 'No ❌'}")
if os.getenv('GEMINI_API_KEY'):
    key = os.getenv('GEMINI_API_KEY')
    print(f"  API key preview: {key[:10]}...")
print(f"{'='*80}\n")

app = FastAPI(title="PANW Case Challenge API")

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Next.js default port
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize insights pipeline
pipeline = None

def get_pipeline():
    global pipeline
    if pipeline is None:
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GEMINI_API_KEY not configured")
        pipeline = InsightsPipeline(anthropic_api_key=api_key)
    return pipeline

@app.get("/")
async def root():
    return {"message": "Welcome to PANW Case Challenge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/insights", response_model=List[Insight])
async def get_insights(user_name: str = "Aarav", top_n: int = 7, buffer: int = 5):
    """
    Generate intelligent spending insights from transaction data

    Query Parameters:
    - user_name: Name for personalization (default: "Aarav")
    - top_n: Number of insights to display initially (default: 7)
    - buffer: Additional insights to keep in queue for when user deletes insights (default: 5)

    Note: Returns empty list if GEMINI_API_KEY is not configured (insights paused)
    """
    # Check if API key is configured - if not, return empty list (insights paused)
    if not os.getenv("GEMINI_API_KEY"):
        print("⏸️  Insights paused: GEMINI_API_KEY not configured")
        return []

    try:
        # Load transaction data from CSV
        # Note: CSV is in project root, need to go up 2 levels from app/main.py
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sample_transactions_1000_sorted.csv')

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Transaction data not found")

        # Read CSV
        df = pd.read_csv(csv_path)

        # Convert to Transaction objects
        transactions = []
        for _, row in df.iterrows():
            # Parse category - handle both JSON array and simple string
            try:
                category = json.loads(row['category']) if isinstance(row['category'], str) else row['category']
            except json.JSONDecodeError:
                # If it's not valid JSON, treat it as a simple string and wrap in array
                category = [row['category']]

            # Parse date
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

        print(f"Loaded {len(transactions)} transactions")

        # Run insights pipeline - request extra insights for queue
        insights_pipeline = get_pipeline()
        insights = insights_pipeline.generate_insights(
            transactions=transactions,
            user_name=user_name,
            top_n=top_n + buffer  # Request extra insights for the queue
        )

        return insights

    except Exception as e:
        print(f"Error generating insights: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating insights: {str(e)}")

@app.get("/api/transactions/summary")
async def get_transactions_summary():
    """Get a summary of transaction data"""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sample_transactions_1000_sorted.csv')

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Transaction data not found")

        df = pd.read_csv(csv_path)

        return {
            "total_transactions": len(df),
            "date_range": {
                "start": df['date'].min(),
                "end": df['date'].max()
            },
            "total_spending": float(df[df['amount'] < 0]['amount'].sum()),
            "total_income": float(df[df['amount'] > 0]['amount'].sum())
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error getting summary: {str(e)}")


# ============================================================================
# GOAL FORECASTING ENDPOINTS
# ============================================================================

def load_transactions() -> List[Transaction]:
    """Helper function to load transactions from CSV"""
    csv_path = os.path.join(os.path.dirname(__file__), '..', '..', 'sample_transactions_1000_sorted.csv')

    if not os.path.exists(csv_path):
        raise HTTPException(status_code=404, detail="Transaction data not found")

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


@app.post("/api/goals", response_model=Goal)
async def create_goal(
    goal_name: str,
    target_amount: float,
    deadline: str,
    monthly_income: float,
    current_savings: float = 0.0,
    priority_level: str = "medium",
    income_type: str = "fixed",
    user_id: str = "default_user"
):
    """
    Create a new savings goal

    Parameters:
    - goal_name: Name of the goal (e.g., "Tesla Down Payment")
    - target_amount: Target amount to save
    - deadline: Deadline date in ISO format (e.g., "2024-12-31")
    - monthly_income: User's monthly income (required for forecasting)
    - current_savings: Amount already saved (default: 0)
    - priority_level: Priority level - "high", "medium", or "low" (default: "medium")
    - income_type: Income stability - "fixed" or "variable" (default: "fixed")
    - user_id: User identifier (default: "default_user")
    """
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
        raise HTTPException(status_code=500, detail=f"Error creating goal: {str(e)}")


@app.get("/api/goals", response_model=List[Goal])
async def get_goals(user_id: str = "default_user"):
    """
    Get all goals for a user

    Parameters:
    - user_id: User identifier (default: "default_user")
    """
    try:
        storage = get_goal_storage()
        goals = storage.get_all_goals(user_id=user_id)
        return goals
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goals: {str(e)}")


@app.get("/api/goals/{goal_id}", response_model=Goal)
async def get_goal(goal_id: str, user_id: str = "default_user"):
    """
    Get a specific goal by ID

    Parameters:
    - goal_id: Goal identifier
    - user_id: User identifier (default: "default_user")
    """
    try:
        storage = get_goal_storage()
        goal = storage.get_goal(goal_id, user_id=user_id)

        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        return goal
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching goal: {str(e)}")


@app.get("/api/goals/{goal_id}/forecast", response_model=GoalForecast)
async def get_goal_forecast(goal_id: str, user_id: str = "default_user"):
    """
    Get forecast for a specific goal with recommendations

    This endpoint:
    1. Loads the user's transaction history
    2. Calculates monthly SPENDING from transactions
    3. Uses Prophet (or linear fallback) to forecast future SPENDING
    4. Converts spending forecast to savings using user's income
    5. Determines probability of reaching goal
    6. Generates spending cut recommendations if off-track

    The forecasting approach:
    - Prophet models spending variability and seasonality
    - Savings = Income - Predicted Spending
    - Confidence intervals are inverted (lower spending = higher savings)

    Parameters:
    - goal_id: Goal identifier
    - user_id: User identifier (default: "default_user")
    """
    try:
        # Get the goal
        storage = get_goal_storage()
        goal = storage.get_goal(goal_id, user_id=user_id)

        if goal is None:
            raise HTTPException(status_code=404, detail="Goal not found")

        # Load transactions
        transactions = load_transactions()

        # Get all active goals for competition analysis
        all_goals = storage.get_all_goals(user_id=user_id)

        # Create forecaster and generate forecast (with all goals for competition analysis)
        forecaster = GoalForecaster(transactions)
        forecast = forecaster.forecast_goal(goal, all_goals=all_goals)

        # If off-track, generate recommendations
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
        print(f"Error generating forecast: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error generating forecast: {str(e)}")


@app.put("/api/goals/{goal_id}", response_model=Goal)
async def update_goal(
    goal_id: str,
    user_id: str = "default_user",
    goal_name: str = None,
    target_amount: float = None,
    deadline: str = None,
    current_savings: float = None,
    priority_level: str = None,
    monthly_income: float = None,
    income_type: str = None
):
    """
    Update an existing goal

    Parameters:
    - goal_id: Goal identifier
    - user_id: User identifier (default: "default_user")
    - goal_name: New goal name (optional)
    - target_amount: New target amount (optional)
    - deadline: New deadline (optional)
    - current_savings: New current savings amount (optional)
    - priority_level: New priority level (optional)
    - monthly_income: New monthly income (optional)
    - income_type: New income type - "fixed" or "variable" (optional)
    """
    try:
        storage = get_goal_storage()

        # Build updates dict
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
        raise HTTPException(status_code=500, detail=f"Error updating goal: {str(e)}")


@app.delete("/api/goals/{goal_id}")
async def delete_goal(goal_id: str, user_id: str = "default_user"):
    """
    Delete a goal

    Parameters:
    - goal_id: Goal identifier
    - user_id: User identifier (default: "default_user")
    """
    try:
        storage = get_goal_storage()
        success = storage.delete_goal(goal_id, user_id=user_id)

        if not success:
            raise HTTPException(status_code=404, detail="Goal not found")

        return {"message": "Goal deleted successfully", "goal_id": goal_id}
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error deleting goal: {str(e)}")


# ============================================================================
# SUBSCRIPTION DETECTION ENDPOINTS
# ============================================================================

@app.get("/api/subscriptions", response_model=SubscriptionSummary)
async def detect_subscriptions():
    """
    Detect recurring subscriptions and gray charges from transaction history

    This endpoint analyzes the complete transaction history to detect:
    1. Recurring subscriptions with regular intervals and consistent amounts
    2. Gray charges (potentially forgotten/sneaky subscriptions)
    3. Price increases (recent charges higher than historical average)
    4. Trial conversions (recently started subscriptions)

    The detection is purely algorithmic - no ML required:
    - Groups transactions by normalized merchant name
    - Analyzes interval regularity (CV < 20%)
    - Matches to frequency buckets (weekly, monthly, quarterly, annual)
    - Checks amount consistency (CV < 15%)
    - Calculates confidence scores based on pattern strength
    - Normalizes all costs to monthly/annual for comparison

    Returns:
    - Complete list of detected subscriptions
    - Summary statistics (total monthly/annual costs)
    - Flags for subscriptions needing attention
    """
    try:
        # Load transactions
        transactions = load_transactions()

        # Create detector and run detection
        detector = SubscriptionDetector(transactions)
        summary = detector.detect_subscriptions()

        return summary

    except Exception as e:
        print(f"Error detecting subscriptions: {e}")
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=f"Error detecting subscriptions: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
