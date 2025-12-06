from pydantic import BaseModel
from typing import List, Literal, Optional
from datetime import datetime


class Transaction(BaseModel):
    transaction_id: str
    date: datetime
    amount: float
    merchant_name: str
    category: List[str]
    payment_channel: str
    pending: bool


class Trigger(BaseModel):
    type: str
    category: Optional[str] = None
    merchant: Optional[str] = None
    this_month: Optional[float] = None
    last_month: Optional[float] = None
    average: Optional[float] = None
    percent_change: Optional[float] = None
    dollar_change: Optional[float] = None
    top_merchants: Optional[List[str]] = None
    visit_count: Optional[int] = None
    savings_rate: Optional[float] = None
    weekend_spend: Optional[float] = None
    weekday_spend: Optional[float] = None
    raw_data: Optional[dict] = None


class Insight(BaseModel):
    id: str
    type: Literal["win", "alert", "anomaly"]
    emoji: str
    headline: str
    description: str
    timestamp: str
    priority_score: float
    trigger_type: str


class AggregatedStats(BaseModel):
    spending_by_category_this_month: dict
    spending_by_category_last_month: dict
    spending_by_category_3mo_average: dict
    spending_by_merchant_this_month: dict
    spending_by_day_of_week: dict
    total_income_this_month: float
    total_spending_this_month: float
    total_spending_last_month: float
