class SubscriptionNotFoundError(Exception):
    """Raised when subscription is not found."""
    pass


class PromotionNotActiveError(Exception):
    """Raised when attempting to subscribe to a non-active promotion."""

    def __init__(self, promotion_id: int, status: str):
        self.promotion_id = promotion_id
        self.status = status
        super().__init__(
            f"Cannot subscribe to promotion {promotion_id} with status '{status}'. "
            f"Promotion must be ACTIVE to accept subscriptions."
        )


class UserNotFoundError(Exception):
    """Raised when user does not exist."""

    def __init__(self, user_id: int):
        self.user_id = user_id
        super().__init__(f"User {user_id} not found")


class DuplicateSubscriptionError(Exception):
    """Raised when attempting to create a duplicate subscription."""

    def __init__(self, user_id: int, promotion_id: int):
        self.user_id = user_id
        self.promotion_id = promotion_id
        super().__init__(
            f"User {user_id} is already subscribed to promotion {promotion_id}. "
            f"Duplicate subscriptions are not allowed."
        )


class SubscriptionAlreadyInactiveError(Exception):
    """Raised when attempting to deactivate an already inactive subscription."""

    def __init__(self, subscription_id: int):
        self.subscription_id = subscription_id
        super().__init__(f"Subscription {subscription_id} is already inactive")
