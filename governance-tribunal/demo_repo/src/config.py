"""Configuration — Contains an intentional hardcoded secret for demo.

DEFECT 3: Secret Violation
AWS credentials are hardcoded instead of loaded from environment.
"""

import os

# SECURITY VIOLATION: Hardcoded AWS credentials
AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"
AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"

DATABASE_URL = "postgresql://localhost:5432/demo"
DEBUG = True
LOG_LEVEL = "INFO"
