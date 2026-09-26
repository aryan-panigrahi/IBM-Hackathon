"""Tests for checkout service — includes a failing test for demo."""

import pytest
from unittest.mock import patch
import sys
from pathlib import Path

# Add demo_repo to path
demo_root = Path(__file__).resolve().parent.parent
if str(demo_root) not in sys.path:
    sys.path.insert(0, str(demo_root))

from src.checkout.service import (
    Cart, CheckoutUser, process_checkout, process_checkout_with_user,
    process_payment, DatabaseError,
)


def test_process_payment_success():
    """Test that payment processing works for valid carts."""
    cart = Cart(items=["item1", "item2"], total=29.99)
    result = process_payment(cart)
    assert result["status"] == "completed"
    assert result["amount"] == 29.99


def test_process_payment_invalid_total():
    """Test that payment fails for zero/negative totals."""
    cart = Cart(items=[], total=0)
    with pytest.raises(ValueError):
        process_payment(cart)


def test_checkout_timeout():
    """Test that checkout handles DB failures gracefully.
    
    This test FAILS because process_checkout has an unbounded
    retry loop (intentional DEFECT 1). It should raise TimeoutError
    or return after a bounded number of retries, but instead loops forever.
    """
    import threading

    cart = Cart(items=["item1"], total=19.99)
    result_holder = {"completed": False, "error": None}

    def run_checkout():
        try:
            with patch("src.checkout.service.process_payment", side_effect=DatabaseError("DB down")):
                process_checkout(cart)
            result_holder["completed"] = True
        except Exception as e:
            result_holder["error"] = str(e)
            result_holder["completed"] = True

    thread = threading.Thread(target=run_checkout, daemon=True)
    thread.start()
    thread.join(timeout=2)  # Wait max 2 seconds

    # If the thread is still alive, the function hung — BUG CONFIRMED
    assert not thread.is_alive(), (
        "REGRESSION: process_checkout has an unbounded retry loop! "
        "Function hung for >2 seconds instead of failing gracefully."
    )


def test_checkout_with_user_success():
    """Test checkout with user context works."""
    import importlib
    from src.checkout import service
    importlib.reload(service)
    from src.checkout.service import CheckoutUser, Cart, process_checkout_with_user

    cart = Cart(items=["item1"], total=49.99)
    user = CheckoutUser(email="test@example.com", cart=cart)
    result = process_checkout_with_user(user)
    assert result["status"] == "completed"

