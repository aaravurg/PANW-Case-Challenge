"""
Subscription & Gray Charge Detector

Purely algorithmic pattern recognition engine for detecting recurring subscriptions
and potentially forgotten charges. No machine learning required - just intelligent
interval and amount analysis.
"""

import re
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Tuple, Optional
from collections import defaultdict
from app.models import Transaction, Subscription, SubscriptionCharge, PriceIncrease, SubscriptionSummary


# Well-known subscription services (whitelist for gray charge detection)
KNOWN_SUBSCRIPTION_SERVICES = {
    'netflix', 'spotify', 'apple', 'amazon prime', 'hulu', 'disney', 'youtube',
    'google one', 'icloud', 'microsoft', 'adobe', 'dropbox', 'gym', 'fitness',
    'planet fitness', '24 hour fitness', 'equinox', 'hbo', 'peacock', 'paramount',
    'audible', 'kindle', 'crunchyroll', 'linkedin', 'github', 'slack', 'zoom'
}


class SubscriptionDetector:
    """
    Detects recurring subscriptions using algorithmic pattern analysis
    """

    def __init__(self, transactions: List[Transaction]):
        self.transactions = transactions
        self.grouped_transactions = {}
        self.subscriptions = []

    def normalize_merchant_name(self, merchant: str) -> str:
        """
        Normalize merchant names to group variations together

        Handles:
        - Lowercase conversion
        - Business suffix removal (INC, LLC, etc.)
        - Special character removal
        - Trailing numbers and location codes
        """
        if not merchant:
            return "unknown"

        # Convert to lowercase
        normalized = merchant.lower()

        # Remove common business suffixes
        suffixes = [
            r'\s+inc\.?$', r'\s+llc\.?$', r'\s+ltd\.?$', r'\s+corp\.?$',
            r'\s+co\.?$', r'\s+lp\.?$', r'\s+sa\.?$', r'\s+limited\.?$',
            r'\s+corporation\.?$', r'\s+company\.?$'
        ]
        for suffix in suffixes:
            normalized = re.sub(suffix, '', normalized, flags=re.IGNORECASE)

        # Remove common subscription identifiers and location codes
        # e.g., "NETFLIX.COM/ACCT" -> "netflix"
        normalized = re.sub(r'\.com.*$', '', normalized)
        normalized = re.sub(r'/.*$', '', normalized)
        normalized = re.sub(r'\s*-\s*\d+$', '', normalized)  # Remove trailing numbers
        normalized = re.sub(r'#\d+$', '', normalized)  # Remove location codes

        # Remove special characters but keep spaces
        normalized = re.sub(r'[^\w\s]', ' ', normalized)

        # Collapse multiple spaces
        normalized = re.sub(r'\s+', ' ', normalized)

        # Strip whitespace
        normalized = normalized.strip()

        return normalized if normalized else "unknown"

    def group_by_merchant(self) -> Dict[str, List[Transaction]]:
        """
        Group transactions by normalized merchant name
        Returns only groups with 2+ transactions (requirement for subscriptions)
        """
        groups = defaultdict(list)

        # Only include expenses (negative amounts)
        for transaction in self.transactions:
            if transaction.amount < 0:
                normalized = self.normalize_merchant_name(transaction.merchant_name)
                groups[normalized].append(transaction)

        # Filter to groups with at least 2 transactions
        self.grouped_transactions = {
            merchant: txns for merchant, txns in groups.items()
            if len(txns) >= 2
        }

        return self.grouped_transactions

    def calculate_interval_stats(self, transactions: List[Transaction]) -> Dict:
        """
        Calculate interval statistics for a group of transactions

        Returns:
        - average_interval: Mean days between charges
        - std_dev: Standard deviation of intervals
        - cv: Coefficient of variation (lower = more regular)
        - intervals: List of all intervals
        """
        # Sort by date
        sorted_txns = sorted(transactions, key=lambda t: t.date)

        # Calculate intervals (days between consecutive charges)
        intervals = []
        for i in range(1, len(sorted_txns)):
            delta = (sorted_txns[i].date - sorted_txns[i-1].date).days
            intervals.append(delta)

        if not intervals:
            return {
                'average_interval': 0,
                'std_dev': 0,
                'cv': 100,  # High CV indicates irregularity
                'intervals': []
            }

        average_interval = np.mean(intervals)
        std_dev = np.std(intervals)
        cv = (std_dev / average_interval * 100) if average_interval > 0 else 100

        return {
            'average_interval': average_interval,
            'std_dev': std_dev,
            'cv': cv,
            'intervals': intervals
        }

    def match_frequency_bucket(self, avg_interval: float) -> Optional[Tuple[str, int]]:
        """
        Match average interval to known billing frequency buckets

        Returns:
        - (frequency_name, bucket_center) or None if no match

        Frequency buckets with tolerance windows:
        - Weekly: 6-8 days (center: 7)
        - Bi-weekly: 13-16 days (center: 14)
        - Monthly: 28-32 days (center: 30)
        - Quarterly: 88-95 days (center: 91)
        - Annual: 360-370 days (center: 365)
        """
        buckets = [
            ('weekly', 7, 6, 8),
            ('bi-weekly', 14, 13, 16),
            ('monthly', 30, 28, 32),
            ('quarterly', 91, 88, 95),
            ('annual', 365, 360, 370)
        ]

        for name, center, min_val, max_val in buckets:
            if min_val <= avg_interval <= max_val:
                return (name, center)

        return None

    def calculate_amount_stats(self, transactions: List[Transaction]) -> Dict:
        """
        Calculate amount consistency statistics

        Returns:
        - average_amount: Mean charge amount
        - std_dev: Standard deviation of amounts
        - cv: Coefficient of variation (lower = more consistent)
        - min_amount: Minimum charge
        - max_amount: Maximum charge
        """
        amounts = [abs(t.amount) for t in transactions]

        average_amount = np.mean(amounts)
        std_dev = np.std(amounts)
        cv = (std_dev / average_amount * 100) if average_amount > 0 else 100

        return {
            'average_amount': average_amount,
            'std_dev': std_dev,
            'cv': cv,
            'min_amount': min(amounts),
            'max_amount': max(amounts),
            'amounts': amounts
        }

    def calculate_confidence_score(
        self,
        interval_cv: float,
        amount_cv: float,
        transaction_count: int
    ) -> float:
        """
        Calculate confidence score for subscription detection

        Factors:
        - Interval regularity (lower CV = higher confidence)
        - Amount consistency (lower CV = higher confidence)
        - Transaction history depth (more charges = higher confidence)

        Returns: Confidence score 0-100
        """
        # Interval regularity score (0-40 points)
        # CV < 10% = excellent (40 pts)
        # CV 10-20% = good (30 pts)
        # CV 20-30% = moderate (20 pts)
        # CV > 30% = poor (10 pts)
        if interval_cv < 10:
            interval_score = 40
        elif interval_cv < 20:
            interval_score = 30
        elif interval_cv < 30:
            interval_score = 20
        else:
            interval_score = 10

        # Amount consistency score (0-40 points)
        # CV < 5% = excellent (40 pts)
        # CV 5-15% = good (30 pts)
        # CV 15-25% = moderate (20 pts)
        # CV > 25% = poor (10 pts)
        if amount_cv < 5:
            amount_score = 40
        elif amount_cv < 15:
            amount_score = 30
        elif amount_cv < 25:
            amount_score = 20
        else:
            amount_score = 10

        # History depth score (0-20 points)
        # 10+ charges = excellent (20 pts)
        # 6-9 charges = good (15 pts)
        # 3-5 charges = moderate (10 pts)
        # 2 charges = minimal (5 pts)
        if transaction_count >= 10:
            history_score = 20
        elif transaction_count >= 6:
            history_score = 15
        elif transaction_count >= 3:
            history_score = 10
        else:
            history_score = 5

        total_score = interval_score + amount_score + history_score
        return min(100, total_score)

    def detect_price_increase(
        self,
        transactions: List[Transaction],
        average_amount: float
    ) -> Optional[PriceIncrease]:
        """
        Detect price increases by comparing recent charge to historical average

        Returns PriceIncrease if increase > 3%
        """
        if len(transactions) < 2:
            return None

        # Sort by date
        sorted_txns = sorted(transactions, key=lambda t: t.date)

        # Get most recent charge
        latest_charge = abs(sorted_txns[-1].amount)

        # Compare to average (excluding latest charge)
        historical_avg = np.mean([abs(t.amount) for t in sorted_txns[:-1]])

        # Calculate percent change
        percent_change = ((latest_charge - historical_avg) / historical_avg * 100) if historical_avg > 0 else 0

        # Flag if increase > 3%
        if percent_change > 3:
            return PriceIncrease(
                old_price=round(historical_avg, 2),
                new_price=round(latest_charge, 2),
                percent_change=round(percent_change, 1),
                detected_date=sorted_txns[-1].date.isoformat()
            )

        return None

    def is_gray_charge(
        self,
        merchant: str,
        amount: float,
        transaction_count: int
    ) -> bool:
        """
        Detect gray charges (potentially forgotten/sneaky subscriptions)

        Criteria:
        - 3 or fewer transactions (new or infrequent)
        - Amount in $3-25 range (forgettable)
        - Not a well-known service (whitelist)
        """
        # Check if it's a known service
        merchant_lower = merchant.lower()
        is_known = any(known in merchant_lower for known in KNOWN_SUBSCRIPTION_SERVICES)

        # Check gray charge criteria
        is_infrequent = transaction_count <= 3
        is_forgettable_amount = 3 <= amount <= 25
        is_unknown_service = not is_known

        return is_infrequent and is_forgettable_amount and is_unknown_service

    def detect_trial_conversion(
        self,
        transactions: List[Transaction],
        average_amount: float
    ) -> bool:
        """
        Detect potential free trial conversions

        Criteria:
        - 1-2 charges total
        - First charge within last 60 days
        - First charge significantly lower than subsequent (trial discount)
        """
        if len(transactions) > 2:
            return False

        # Sort by date
        sorted_txns = sorted(transactions, key=lambda t: t.date)

        # Check if first charge is recent (within 60 days)
        first_charge_date = sorted_txns[0].date
        days_since_first = (datetime.now() - first_charge_date.replace(tzinfo=None)).days
        is_recent = days_since_first <= 60

        # Check if first charge was significantly lower (trial discount)
        if len(sorted_txns) == 2:
            first_amount = abs(sorted_txns[0].amount)
            second_amount = abs(sorted_txns[1].amount)
            is_trial_discount = first_amount < second_amount * 0.5  # 50%+ discount
        else:
            is_trial_discount = False

        return is_recent and (len(sorted_txns) == 1 or is_trial_discount)

    def normalize_to_monthly_cost(self, amount: float, frequency: str) -> float:
        """
        Normalize charge to monthly cost for comparison

        - Weekly: amount * 4.33
        - Bi-weekly: amount * 2.165
        - Monthly: amount
        - Quarterly: amount / 3
        - Annual: amount / 12
        """
        multipliers = {
            'weekly': 4.33,
            'bi-weekly': 2.165,
            'monthly': 1.0,
            'quarterly': 1/3,
            'annual': 1/12
        }

        return amount * multipliers.get(frequency, 1.0)

    def predict_next_charge_date(
        self,
        last_charge_date: datetime,
        average_interval: float
    ) -> str:
        """
        Predict next charge date based on average interval
        """
        next_date = last_charge_date + timedelta(days=int(average_interval))
        return next_date.isoformat()

    def detect_subscriptions(self) -> SubscriptionSummary:
        """
        Main detection method - runs complete subscription detection pipeline

        Returns SubscriptionSummary with all detected subscriptions
        """
        # Group transactions by merchant
        self.group_by_merchant()

        subscriptions = []

        for merchant, transactions in self.grouped_transactions.items():
            # Calculate interval statistics
            interval_stats = self.calculate_interval_stats(transactions)
            avg_interval = interval_stats['average_interval']
            interval_cv = interval_stats['cv']

            # Check if timing is regular (CV < 20%)
            if interval_cv >= 20:
                continue  # Skip irregular patterns

            # Match to frequency bucket
            frequency_match = self.match_frequency_bucket(avg_interval)
            if not frequency_match:
                continue  # Skip if doesn't match standard billing frequency

            frequency_name, frequency_days = frequency_match

            # Calculate amount statistics
            amount_stats = self.calculate_amount_stats(transactions)
            amount_cv = amount_stats['cv']

            # Check amount consistency (CV < 15%)
            if amount_cv >= 15:
                continue  # Skip if amounts are too variable

            # Check minimum amount (> $1)
            if amount_stats['average_amount'] < 1:
                continue  # Skip very small charges

            # At this point, we have a confirmed subscription!
            # Calculate confidence score
            confidence = self.calculate_confidence_score(
                interval_cv=interval_cv,
                amount_cv=amount_cv,
                transaction_count=len(transactions)
            )

            # Detect price increase
            price_increase = self.detect_price_increase(transactions, amount_stats['average_amount'])

            # Detect gray charge
            is_gray = self.is_gray_charge(
                merchant=merchant,
                amount=amount_stats['average_amount'],
                transaction_count=len(transactions)
            )

            # Detect trial conversion
            is_trial = self.detect_trial_conversion(transactions, amount_stats['average_amount'])

            # Sort transactions by date
            sorted_txns = sorted(transactions, key=lambda t: t.date)

            # Create subscription charges
            charges = [
                SubscriptionCharge(
                    date=t.date.isoformat(),
                    amount=round(abs(t.amount), 2)
                )
                for t in sorted_txns
            ]

            # Calculate costs
            current_amount = abs(sorted_txns[-1].amount)
            monthly_cost = self.normalize_to_monthly_cost(current_amount, frequency_name)
            annual_cost = monthly_cost * 12

            # Predict next charge
            next_charge = self.predict_next_charge_date(
                sorted_txns[-1].date,
                avg_interval
            )

            # Determine if needs attention
            needs_attention = price_increase is not None or is_gray or is_trial

            # Create subscription object
            subscription = Subscription(
                merchant_name=merchant,
                original_merchant_name=transactions[0].merchant_name,
                frequency=frequency_name,
                frequency_days=frequency_days,
                current_amount=round(current_amount, 2),
                average_amount=round(amount_stats['average_amount'], 2),
                min_amount=round(amount_stats['min_amount'], 2),
                max_amount=round(amount_stats['max_amount'], 2),
                first_charge_date=sorted_txns[0].date.isoformat(),
                last_charge_date=sorted_txns[-1].date.isoformat(),
                next_predicted_date=next_charge,
                transaction_count=len(transactions),
                charges=charges,
                monthly_cost=round(monthly_cost, 2),
                annual_cost=round(annual_cost, 2),
                confidence_score=round(confidence, 1),
                interval_regularity=round(interval_cv, 2),
                amount_consistency=round(amount_cv, 2),
                is_gray_charge=is_gray,
                has_price_increase=price_increase is not None,
                is_trial_conversion=is_trial,
                needs_attention=needs_attention,
                price_increase=price_increase
            )

            subscriptions.append(subscription)

        # Sort by monthly cost (descending)
        subscriptions.sort(key=lambda s: s.monthly_cost, reverse=True)

        # Calculate summary statistics
        total_monthly = sum(s.monthly_cost for s in subscriptions)
        total_annual = sum(s.annual_cost for s in subscriptions)
        gray_count = sum(1 for s in subscriptions if s.is_gray_charge)
        price_increase_count = sum(1 for s in subscriptions if s.has_price_increase)
        trial_count = sum(1 for s in subscriptions if s.is_trial_conversion)

        return SubscriptionSummary(
            total_subscriptions=len(subscriptions),
            total_monthly_cost=round(total_monthly, 2),
            total_annual_cost=round(total_annual, 2),
            gray_charges_count=gray_count,
            price_increases_count=price_increase_count,
            trial_conversions_count=trial_count,
            subscriptions=subscriptions
        )
