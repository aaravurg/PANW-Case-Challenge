"""
Utility functions for data loading and common operations.
"""
import os
import json
import logging
import pandas as pd
from typing import List
from pathlib import Path

from app.models import Transaction
from app.config import TRANSACTIONS_CSV

logger = logging.getLogger(__name__)


def load_transactions_from_csv(csv_path: Path = None) -> List[Transaction]:
    """
    Load transaction data from CSV file.

    Args:
        csv_path: Path to CSV file. If None, uses default from config.

    Returns:
        List of Transaction objects.

    Raises:
        FileNotFoundError: If CSV file doesn't exist.
    """
    if csv_path is None:
        csv_path = TRANSACTIONS_CSV

    if not csv_path.exists():
        raise FileNotFoundError(f"Transaction data not found at {csv_path}")

    df = pd.read_csv(csv_path)
    transactions = []

    for _, row in df.iterrows():
        try:
            category = json.loads(row['category']) if isinstance(row['category'], str) else row['category']
        except json.JSONDecodeError:
            category = [row['category']]

        transaction = Transaction(
            transaction_id=row['transaction_id'],
            date=pd.to_datetime(row['date']),
            amount=float(row['amount']),
            merchant_name=row['merchant_name'],
            category=category,
            payment_channel=row['payment_channel'],
            pending=bool(row['pending'])
        )
        transactions.append(transaction)

    logger.info(f"Loaded {len(transactions)} transactions from {csv_path}")
    return transactions


def validate_api_key(key_name: str) -> str:
    """
    Validate and retrieve API key from environment.

    Args:
        key_name: Name of the environment variable.

    Returns:
        API key value.

    Raises:
        ValueError: If API key is not configured.
    """
    api_key = os.getenv(key_name)
    if not api_key:
        raise ValueError(f"{key_name} not configured in environment")
    return api_key


def calculate_months_remaining(deadline_str: str) -> float:
    """
    Calculate months remaining until deadline.

    Args:
        deadline_str: ISO format date string.

    Returns:
        Number of months remaining (minimum 0.5).
    """
    from datetime import datetime

    deadline = datetime.fromisoformat(deadline_str.replace('Z', '+00:00'))
    now = datetime.now(deadline.tzinfo) if deadline.tzinfo else datetime.now()

    months = (deadline.year - now.year) * 12 + (deadline.month - now.month)
    return max(months, 0.5)
