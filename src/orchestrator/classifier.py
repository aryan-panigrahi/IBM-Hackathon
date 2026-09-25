from src.orchestrator.case_manager import CaseType, Severity


def classify_case(evidence: dict) -> tuple:
    """Classify case type and severity from collected evidence."""
    tests_failed = not evidence.get("test_results", {}).get("passed", True)
    secrets_found = not evidence.get("secret_scan", {}).get("passed", True)
    pii_found = not evidence.get("pii_scan", {}).get("passed", True)
    policy_failed = secrets_found or pii_found

    # Case type
    if tests_failed and policy_failed:
        case_type = CaseType.COMBINED
    elif tests_failed:
        case_type = CaseType.FUNCTIONAL
    elif policy_failed:
        case_type = CaseType.POLICY
    else:
        case_type = CaseType.UNKNOWN

    # Severity
    severity = Severity.MEDIUM
    if secrets_found:
        severity = Severity.HIGH

    changed = evidence.get("changed_files", [])
    sensitive_patterns = ["auth", "login", "payment", "checkout", "crypto", "secret", "config"]
    for f in changed:
        if any(p in f.lower() for p in sensitive_patterns):
            severity = Severity.HIGH
            break

    return case_type, severity


def compute_confidence(evidence: dict, reproduction_success: bool) -> float:
    """Compute confidence score for root cause hypothesis."""
    score = 0.0
    score += 0.40 if reproduction_success else 0.0
    score += 0.25 if evidence.get("recent_commits") else 0.0

    failures = evidence.get("test_results", {}).get("failures", [])
    if failures and failures[0].get("file"):
        score += 0.15  # Stack trace points to specific file/line

    if not evidence.get("pii_scan", {}).get("passed", True) or not evidence.get("secret_scan", {}).get("passed", True):
        score += 0.10  # Policy clause match

    score += 0.10  # Baseline historical calibration

    return round(min(score, 1.0), 2)
