class InvalidPromotionStatusTransitionError(Exception):
    """Raised when attempting an invalid status transition."""

    def __init__(self, current_status: str, target_status: str):
        self.current_status = current_status
        self.target_status = target_status
        super().__init__(
            f"Cannot transition from {current_status} to {target_status}. "
            f"Valid transitions: DRAFT→ACTIVE, ACTIVE→ENDED"
        )


class PromotionNotEditableError(Exception):
    """Raised when attempting to edit a promotion that is not editable."""

    def __init__(self, status: str, field: str):
        self.status = status
        self.field = field
        super().__init__(
            f"Cannot edit field '{field}' when promotion is in {status} status"
        )


class PromotionNotFoundError(Exception):
    """Raised when promotion is not found."""
    pass


class InvalidTimeRangeError(Exception):
    """Raised when promotion time range is invalid."""
    pass
