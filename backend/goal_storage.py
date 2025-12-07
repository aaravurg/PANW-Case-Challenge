"""
In-memory storage for user goals
This provides CRUD operations for goals until a proper database is implemented
"""

from typing import Dict, List, Optional
from datetime import datetime
from models import Goal
import uuid


class GoalStorage:
    """In-memory storage for user savings goals"""

    def __init__(self):
        # Structure: {user_id: {goal_id: Goal}}
        self._storage: Dict[str, Dict[str, Goal]] = {}

    def create_goal(
        self,
        goal_name: str,
        target_amount: float,
        deadline: str,
        monthly_income: float,
        current_savings: float = 0.0,
        priority_level: str = "medium",
        income_type: str = "fixed",
        user_id: str = "default_user"
    ) -> Goal:
        """Create a new savings goal"""
        goal_id = str(uuid.uuid4())
        created_at = datetime.now().isoformat()

        goal = Goal(
            id=goal_id,
            goal_name=goal_name,
            target_amount=target_amount,
            deadline=deadline,
            current_savings=current_savings,
            priority_level=priority_level,
            created_at=created_at,
            user_id=user_id,
            monthly_income=monthly_income,
            income_type=income_type
        )

        # Initialize user storage if needed
        if user_id not in self._storage:
            self._storage[user_id] = {}

        self._storage[user_id][goal_id] = goal
        return goal

    def get_goal(self, goal_id: str, user_id: str = "default_user") -> Optional[Goal]:
        """Get a specific goal by ID"""
        if user_id not in self._storage:
            return None
        return self._storage[user_id].get(goal_id)

    def get_all_goals(self, user_id: str = "default_user") -> List[Goal]:
        """Get all goals for a user"""
        if user_id not in self._storage:
            return []
        return list(self._storage[user_id].values())

    def update_goal(
        self,
        goal_id: str,
        user_id: str = "default_user",
        **updates
    ) -> Optional[Goal]:
        """Update an existing goal"""
        goal = self.get_goal(goal_id, user_id)
        if not goal:
            return None

        # Update allowed fields
        allowed_fields = {
            'goal_name', 'target_amount', 'deadline',
            'current_savings', 'priority_level', 'monthly_income', 'income_type'
        }

        for field, value in updates.items():
            if field in allowed_fields and hasattr(goal, field):
                setattr(goal, field, value)

        self._storage[user_id][goal_id] = goal
        return goal

    def delete_goal(self, goal_id: str, user_id: str = "default_user") -> bool:
        """Delete a goal"""
        if user_id not in self._storage:
            return False
        if goal_id not in self._storage[user_id]:
            return False

        del self._storage[user_id][goal_id]
        return True

    def clear_all(self, user_id: str = "default_user") -> None:
        """Clear all goals for a user (useful for testing)"""
        if user_id in self._storage:
            self._storage[user_id] = {}


# Global instance
_goal_storage = None


def get_goal_storage() -> GoalStorage:
    """Get the global goal storage instance"""
    global _goal_storage
    if _goal_storage is None:
        _goal_storage = GoalStorage()
    return _goal_storage
