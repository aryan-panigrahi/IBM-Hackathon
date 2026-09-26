"""Tests for authentication module."""

import sys
from pathlib import Path

# Add demo_repo to path
demo_root = Path(__file__).resolve().parent.parent
if str(demo_root) not in sys.path:
    sys.path.insert(0, str(demo_root))

from src.auth.login import User, login, authenticate


def test_login_success():
    """Test successful login."""
    user = User(email="alice@company.com", password_hash="valid_hash", name="Alice")
    result = login(user)
    assert result["status"] == "success"


def test_login_failure():
    """Test failed login with wrong password."""
    user = User(email="bob@company.com", password_hash="wrong_hash", name="Bob")
    result = login(user)
    assert result["status"] == "failed"


def test_authenticate_valid():
    """Test authentication with correct hash."""
    user = User(email="test@example.com", password_hash="valid_hash")
    assert authenticate(user) is True


def test_authenticate_invalid():
    """Test authentication with incorrect hash."""
    user = User(email="test@example.com", password_hash="invalid")
    assert authenticate(user) is False
