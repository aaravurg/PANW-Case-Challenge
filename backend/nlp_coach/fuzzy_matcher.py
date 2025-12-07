"""
Fuzzy Matching Layer for Natural Language Coach

Handles fuzzy string matching for merchant names and categories to handle
typos and partial matches (e.g., "Starbuck" -> "Starbucks", "amazn" -> "Amazon")
"""

from typing import List, Optional, Tuple
from rapidfuzz import process, fuzz
from app.models import Transaction


class FuzzyMatcher:
    """
    Fuzzy matcher for normalizing merchant names and categories
    """

    def __init__(self, transactions: List[Transaction]):
        """
        Initialize the fuzzy matcher with transaction data to build indices.

        Args:
            transactions: List of all transactions
        """
        self.transactions = transactions
        self.merchant_index = self._build_merchant_index()
        self.category_index = self._build_category_index()

    def _build_merchant_index(self) -> List[str]:
        """Build index of unique merchant names"""
        merchants = set()
        for t in self.transactions:
            if t.merchant_name:
                merchants.add(t.merchant_name)
        return sorted(list(merchants))

    def _build_category_index(self) -> List[str]:
        """Build index of unique categories"""
        categories = set()
        for t in self.transactions:
            if isinstance(t.category, list):
                for cat in t.category:
                    if cat:
                        categories.add(cat.upper())
            elif t.category:
                categories.add(t.category.upper())
        return sorted(list(categories))

    def match_merchant(
        self,
        query: str,
        threshold: int = 80,
        limit: int = 1
    ) -> Optional[str]:
        """
        Fuzzy match a merchant name query to the closest merchant in the index.

        Args:
            query: Merchant name to match (can be partial or misspelled)
            threshold: Minimum similarity score (0-100) to consider a match
            limit: Number of matches to return (default: 1 for best match)

        Returns:
            Best matching merchant name, or None if no match above threshold

        Examples:
            - "Starbuck" -> "Starbucks"
            - "amazn" -> "Amazon"
            - "whole food" -> "Whole Foods"
        """
        if not query or not self.merchant_index:
            return None

        # Use rapidfuzz to find best matches
        results = process.extract(
            query,
            self.merchant_index,
            scorer=fuzz.WRatio,  # Weighted ratio handles partial matches well
            limit=limit
        )

        if results and results[0][1] >= threshold:
            return results[0][0]  # Return best match

        return None

    def match_category(
        self,
        query: str,
        threshold: int = 80
    ) -> Optional[str]:
        """
        Fuzzy match a category query to the closest category in the index.

        Args:
            query: Category name to match (can be partial or misspelled)
            threshold: Minimum similarity score (0-100) to consider a match

        Returns:
            Best matching category name, or None if no match above threshold

        Examples:
            - "dine" -> "DINING"
            - "grocery" -> "GROCERIES"
            - "transport" -> "TRANSPORTATION"
        """
        if not query or not self.category_index:
            return None

        # Normalize query to uppercase for category matching
        query_upper = query.upper()

        # Use rapidfuzz to find best match
        results = process.extract(
            query_upper,
            self.category_index,
            scorer=fuzz.WRatio,
            limit=1
        )

        if results and results[0][1] >= threshold:
            return results[0][0]  # Return best match

        return None

    def get_all_merchants(self) -> List[str]:
        """Get all unique merchant names"""
        return self.merchant_index

    def get_all_categories(self) -> List[str]:
        """Get all unique categories"""
        return self.category_index

    def find_merchant_matches(
        self,
        query: str,
        threshold: int = 70,
        limit: int = 5
    ) -> List[Tuple[str, float]]:
        """
        Find multiple merchant matches for disambiguation.

        Args:
            query: Merchant name to match
            threshold: Minimum similarity score
            limit: Maximum number of matches to return

        Returns:
            List of (merchant_name, score) tuples sorted by score

        Useful for when user query is ambiguous and we want to suggest options
        """
        if not query or not self.merchant_index:
            return []

        results = process.extract(
            query,
            self.merchant_index,
            scorer=fuzz.WRatio,
            limit=limit
        )

        # Filter by threshold and return
        return [(match[0], match[1]) for match in results if match[1] >= threshold]
