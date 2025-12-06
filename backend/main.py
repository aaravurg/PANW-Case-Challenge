from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
import os
import pandas as pd
import json
from typing import List
from datetime import datetime

from models import Transaction, Insight
from insights_pipeline import InsightsPipeline

# Load environment variables from root .env file
load_dotenv(os.path.join(os.path.dirname(__file__), '..', '.env'))

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
        api_key = os.getenv("GROQ_API_KEY")
        if not api_key:
            raise HTTPException(status_code=500, detail="GROQ_API_KEY not configured")
        pipeline = InsightsPipeline(anthropic_api_key=api_key)
    return pipeline

@app.get("/")
async def root():
    return {"message": "Welcome to PANW Case Challenge API"}

@app.get("/health")
async def health_check():
    return {"status": "healthy"}

@app.get("/api/insights", response_model=List[Insight])
async def get_insights(user_name: str = "Aarav", top_n: int = 7):
    """
    Generate intelligent spending insights from transaction data

    Query Parameters:
    - user_name: Name for personalization (default: "Aarav")
    - top_n: Number of insights to return (default: 7)
    """
    try:
        # Load transaction data from CSV
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'sample_transactions_1000_sorted.csv')

        if not os.path.exists(csv_path):
            raise HTTPException(status_code=404, detail="Transaction data not found")

        # Read CSV
        df = pd.read_csv(csv_path)

        # Convert to Transaction objects
        transactions = []
        for _, row in df.iterrows():
            # Parse category JSON
            category = json.loads(row['category']) if isinstance(row['category'], str) else row['category']

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

        # Run insights pipeline
        insights_pipeline = get_pipeline()
        insights = insights_pipeline.generate_insights(
            transactions=transactions,
            user_name=user_name,
            top_n=top_n
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
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'sample_transactions_1000_sorted.csv')

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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
