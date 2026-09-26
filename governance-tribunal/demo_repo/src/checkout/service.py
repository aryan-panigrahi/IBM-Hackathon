"""Checkout Service — Contains intentional functional regression + combined defect."""

import logging
import time

logger = logging.getLogger(__name__)


class DatabaseError(Exception):
    """Simulated database connection error."""
    pass


class Cart:
    """Simple shopping cart."""
    def __init__(self, items: list, total: float):
        self.items = items
        self.total = total


class CheckoutUser:
    """User in checkout context."""
    def __init__(self, email: str, cart: Cart):
        self.email = email
        self.cart = cart


def process_payment(cart: Cart) -> dict:
    """Simulate payment processing."""
    if cart.total <= 0:
        raise ValueError("Cart total must be positive")
    return {"status": "completed", "amount": cart.total}


def process_checkout(cart: Cart) -> dict:
    """Process a checkout transaction.

    DEFECT 1: Functional Regression
    The retry loop has no upper bound, causing TimeoutError
    when the database is unreachable.
    """
    # BUG: unbounded retry — will hang forever if DB is down
    while True:
        try:
            result = process_payment(cart)
            logger.info(f"Checkout completed: ${cart.total}")
            return result
        except DatabaseError:
            time.sleep(0.1)  # No max retries — infinite loop!


def process_checkout_with_user(user: CheckoutUser) -> dict:
    """Process checkout with user context.

    DEFECT 4: Combined Defect (Functional + Policy)
    The retry logic works correctly BUT logs the user's email,
    creating both a functional concern and a privacy violation.
    """
    for i in range(3):
        try:
            result = process_payment(user.cart)
            logger.info(f"Checkout completed for order")
            return result
        except DatabaseError:
            logger.info(f"Retrying checkout for {user.email}")  # PII LEAK in retry!
            time.sleep(0.1)

    raise TimeoutError("Checkout failed after 3 retries")
