"""Case Classifier — Determines case type, severity, and confidence score."""

from typing import Any


# Import-safe: these are string constants matching CaseType/Severity enums
CASE_FUNCTIONAL = "functional"
CASE_POLICY = "policy"
CASE_COMBINED = "combined"
CASE_UNKNOWN = "unknown"

SEVERITY_HIGH = "high"
SEVERITY_MEDIUM = "medium"
SEVERITY_LOW = "low"

# Files/paths that indicate high-severity changes
SENSITIVE_PATTERNS = [
    "auth", "login", "payment", "checkout", "crypto",
    "secret", "password", "token", "session", "admin",
    "migration", "security",
]


def classify_case_type(evidence: dict[str, Any]) -> str:
    """Determine if the case is FUNCTIONAL, POLICY, COMBINED, or UNKNOWN."""
    tests_failed = not evidence.get("test_results", {}).get("passed", True)
    secrets_found = not evidence.get("secret_scan", {}).get("passed", True)
    pii_found = not evidence.get("pii_scan", {}).get("passed", True)
    policy_failed = secrets_found or pii_found

    if tests_failed and policy_failed:
        return CASE_COMBINED
    elif tests_failed:
        return CASE_FUNCTIONAL
    elif policy_failed:
        return CASE_POLICY
    return CASE_UNKNOWN


def classify_severity(evidence: dict[str, Any]) -> str:
    """Determine severity: HIGH, MEDIUM, or LOW."""
    # Secrets are always HIGH
    if not evidence.get("secret_scan", {}).get("passed", True):
        return SEVERITY_HIGH

    # Check if changed files touch sensitive areas
    changed_files = evidence.get("changed_files", [])
    for filepath in changed_files:
        filepath_lower = filepath.lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern in filepath_lower:
                return SEVERITY_HIGH

    # PII violations are at least MEDIUM, potentially HIGH
    if not evidence.get("pii_scan", {}).get("passed", True):
        return SEVERITY_MEDIUM

    # Default
    return SEVERITY_MEDIUM


def compute_confidence(
    evidence: dict[str, Any],
    reproduction_success: bool,
) -> float:
    """Compute confidence score for root cause hypothesis.

    Formula:
        0.40 * reproduction_success
      + 0.25 * recent_commit_correlation
      + 0.15 * stack_trace_match
      + 0.10 * policy_clause_match
      + 0.10 * baseline (always added for MVP)
    """
    score = 0.0

    # Reproduction success (highest weight)
    if reproduction_success:
        score += 0.40

    # Recent commit correlation
    if evidence.get("recent_commits"):
        score += 0.25

    # Stack trace points to specific file/line
    failures = evidence.get("test_results", {}).get("failures", [])
    if failures and failures[0].get("file"):
        score += 0.15

    # Policy clause match
    policy_failed = (
        not evidence.get("pii_scan", {}).get("passed", True)
        or not evidence.get("secret_scan", {}).get("passed", True)
    )
    if policy_failed:
        score += 0.10

    # Baseline (always add for MVP)
    score += 0.10

    return round(min(score, 1.0), 2)


def should_require_human_approval(
    severity: str,
    confidence_score: float,
    changed_files: list[str],
) -> bool:
    """Determine if human approval is required before merging."""
    if severity == SEVERITY_HIGH:
        return True
    if confidence_score < 0.75:
        return True

    # Check for sensitive file modifications
    for filepath in changed_files:
        filepath_lower = filepath.lower()
        for pattern in SENSITIVE_PATTERNS:
            if pattern in filepath_lower:
                return True

    return False
