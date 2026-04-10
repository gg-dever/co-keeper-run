"""
Category Mapper Service

Maps between ML-predicted categories and QuickBooks account names.
Handles bidirectional conversion with fuzzy matching fallback.

Author: CoKeeper AI
Date: April 2026
"""

from typing import Optional, List, Dict
from difflib import get_close_matches
import logging

logger = logging.getLogger(__name__)


class CategoryMapper:
    """Maps between ML categories and QuickBooks account names."""

    def __init__(self, qb_accounts: List[Dict]):
        """
        Initialize with QB accounts from /api/quickbooks/accounts.

        Args:
            qb_accounts: List of QB accounts with Id, Name, FullyQualifiedName, AccountType
        """
        self.qb_accounts = qb_accounts

        # Build lookup tables
        self.account_by_name = {}
        self.account_by_id = {}

        for account in qb_accounts:
            name = account.get("Name", "").lower()
            fqn = account.get("FullyQualifiedName", "").lower()
            acc_id = account.get("Id", "")

            if name:
                self.account_by_name[name] = account
            if fqn:
                self.account_by_name[fqn] = account
            if acc_id:
                self.account_by_id[acc_id] = account

        logger.info(f"CategoryMapper initialized with {len(qb_accounts)} QB accounts")

    def ml_to_qb(self, ml_category: str) -> Optional[Dict]:
        """
        Convert ML predicted category to QB account.

        Args:
            ml_category: Category predicted by ML (e.g., "Meals & Entertainment")

        Returns:
            Dict with:
            - id: QB account ID
            - name: QB account name
            - fqn: Fully qualified name
            - confidence: Match confidence (1.0 exact, 0.85 fuzzy)
            OR None if no match found
        """
        if not ml_category:
            return None

        ml_cat_lower = ml_category.lower().strip()

        # Try exact match first
        if ml_cat_lower in self.account_by_name:
            account = self.account_by_name[ml_cat_lower]
            return {
                "id": account.get("Id"),
                "name": account.get("Name"),
                "fqn": account.get("FullyQualifiedName"),
                "confidence": 1.0,
                "match_type": "exact"
            }

        # Try fuzzy match
        candidates = list(self.account_by_name.keys())
        matches = get_close_matches(
            ml_cat_lower,
            candidates,
            n=1,
            cutoff=0.75
        )

        if matches:
            account = self.account_by_name[matches[0]]
            return {
                "id": account.get("Id"),
                "name": account.get("Name"),
                "fqn": account.get("FullyQualifiedName"),
                "confidence": 0.85,
                "match_type": "fuzzy"
            }

        logger.warning(f"No QB account match found for ML category: {ml_category}")
        return None

    def qb_to_ml(self, qb_account_name: str) -> str:
        """
        Convert QB account name to standardized ML category format.

        Args:
            qb_account_name: QB account name (e.g., "Automobile:Fuel")

        Returns:
            Standardized category name for ML pipeline
        """
        # Standard mappings from QB account names to ML categories
        mappings = {
            # Auto & Transport
            "automobile": "Auto & Transport",
            "automobile:fuel": "Auto & Transport",
            "automobile:maintenance": "Auto & Transport",
            "automobile:rent": "Auto & Transport",
            "automobile:repairs": "Auto & Transport",
            "gas and fuel": "Auto & Transport",
            "parking": "Auto & Transport",
            "tolls": "Auto & Transport",
            "vehicle": "Auto & Transport",

            # Meals & Entertainment
            "meals and entertainment": "Meals & Entertainment",
            "meals": "Meals & Entertainment",
            "entertainment": "Meals & Entertainment",

            # Office Supplies
            "office supplies": "Office Supplies",
            "office equipment": "Office Supplies",
            "office": "Office Supplies",

            # Software & Internet
            "software": "Software",
            "subscriptions": "Software",
            "internet": "Software",

            # Utilities
            "utilities": "Utilities",
            "phone": "Utilities",

            # Travel
            "travel": "Travel",
            "airfare": "Travel",
            "hotels": "Travel",

            # Professional Services
            "professional services": "Professional Services",
            "legal": "Professional Services",
            "accounting": "Professional Services",
            "consulting": "Professional Services",
        }

        qb_lower = qb_account_name.lower().strip()

        # Try exact match
        if qb_lower in mappings:
            return mappings[qb_lower]

        # Try partial match (for hierarchical accounts like "Automobile:Fuel")
        for key, value in mappings.items():
            if key in qb_lower:
                return value

        # If no mapping, return original
        return qb_account_name

    def get_account_by_id(self, account_id: str) -> Optional[Dict]:
        """
        Get QB account details by ID.

        Args:
            account_id: QB account ID

        Returns:
            Account dict or None
        """
        return self.account_by_id.get(account_id)

    def get_account_by_name(self, account_name: str) -> Optional[Dict]:
        """
        Get QB account details by name (case-insensitive).

        Args:
            account_name: QB account name

        Returns:
            Account dict or None
        """
        return self.account_by_name.get(account_name.lower())

    def validate_account_id(self, account_id: str) -> bool:
        """
        Check if an account ID exists in QB.

        Args:
            account_id: QB account ID

        Returns:
            True if account exists
        """
        return account_id in self.account_by_id

    def list_expense_accounts(self) -> List[Dict]:
        """
        Get all expense accounts from QB.

        Returns:
            List of expense account dicts
        """
        expense_accounts = []
        for account in self.qb_accounts:
            acc_type = account.get("AccountType", "").lower()
            if "expense" in acc_type or "cost" in acc_type:
                expense_accounts.append(account)
        return expense_accounts
