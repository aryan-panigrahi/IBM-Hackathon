"""Authentication module — Contains intentional PII violations for demo."""

import logging

logger = logging.getLogger(__name__)


class User:
    """Simple user model."""
    def __init__(self, email: str, password_hash: str, name: str = "Unknown"):
        self.email = email
        self.password_hash = password_hash
        self.name = name


def authenticate(user: User) -> bool:
    """Authenticate a user against the database."""
    # Simulated authentication
    return user.password_hash == "valid_hash"


def login(user: User) -> dict:
    """Process a user login.

    DEFECT 2: Privacy Violation
    This function logs the user's email in plain text,
    violating the Data Privacy Policy Section 1.1.
    """
    logger.info(f"User login attempt: {user.email}")  # PII LEAK!

    if authenticate(user):
        logger.info(f"Login successful for {user.name}")
        return {"status": "success", "user": user.name}
    else:
        logger.warning(f"Login failed for {user.email}")  # Another PII leak!
        return {"status": "failed", "error": "Invalid credentials"}
