"""Case Manager — State machine and data model for Governance Tribunal cases."""

import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Optional


class CaseType(Enum):
    """Classification of the type of codebase defect."""
    FUNCTIONAL = "functional"      # Failing tests, broken builds
    POLICY = "policy"              # Security/privacy/licensing violations
    COMBINED = "combined"          # Both functional AND policy violations
    UNKNOWN = "unknown"            # Cannot determine


class CaseStatus(Enum):
    """States in the Tribunal investigation state machine."""
    TRIGGER_RECEIVED = "trigger_received"
    EVIDENCE_COLLECTED = "evidence_collected"
    CASE_CLASSIFIED = "case_classified"
    HYPOTHESES_GENERATED = "hypotheses_generated"
    REPRODUCTION_ATTEMPTED = "reproduction_attempted"
    ROOT_CAUSE_SELECTED = "root_cause_selected"
    PATCH_GENERATED = "patch_generated"
    VALIDATION_EXECUTED = "validation_executed"
    VERDICT_GENERATED = "verdict_generated"
    HUMAN_APPROVAL = "human_approval"
    CASE_CLOSED = "case_closed"
    ESCALATED = "escalated"


class Severity(Enum):
    """Severity classification for the defect."""
    HIGH = "high"       # auth, payments, secrets, privacy, DB migration
    MEDIUM = "medium"   # business logic, API behavior, tests
    LOW = "low"         # docs, formatting, minor refactor


class Case:
    """Represents a single Tribunal investigation case.
    
    Tracks the full lifecycle from trigger reception through
    evidence collection, investigation, remediation, validation,
    and final human approval.
    """

    def __init__(self):
        self.case_id: str = self._generate_case_id()
        self.created_at: str = datetime.now(timezone.utc).isoformat()
        self.status: CaseStatus = CaseStatus.TRIGGER_RECEIVED
        self.case_type: CaseType = CaseType.UNKNOWN
        self.severity: Severity = Severity.MEDIUM
        self.evidence: dict[str, Any] = {}
        self.hypotheses: list[dict[str, Any]] = []
        self.patch: Optional[dict[str, Any]] = None
        self.validation_results: dict[str, Any] = {}
        self.confidence_score: float = 0.0
        self.verdict: Optional[str] = None
        self.human_approved: Optional[bool] = None
        self.attempt_count: int = 0
        self.history: list[dict[str, Any]] = []

    @staticmethod
    def _generate_case_id() -> str:
        """Generate a unique case ID with timestamp prefix."""
        timestamp = datetime.now(timezone.utc).strftime("%Y%m%d")
        short_uuid = uuid.uuid4().hex[:4].upper()
        return f"GT-{timestamp}-{short_uuid}"

    def log_event(self, event_type: str, details: dict[str, Any]) -> None:
        """Append an event to the case history for audit trail."""
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "details": details,
        })

    def update_status(self, new_status: CaseStatus) -> None:
        """Transition to a new state and log the change."""
        old_status = self.status
        self.status = new_status
        self.log_event("status_change", {
            "from": old_status.value,
            "to": new_status.value,
        })

    def add_hypothesis(self, description: str, confidence: float) -> None:
        """Add a root cause hypothesis with confidence score."""
        self.hypotheses.append({
            "id": f"H{len(self.hypotheses) + 1}",
            "description": description,
            "confidence": round(confidence, 2),
        })

    def to_dict(self) -> dict[str, Any]:
        """Serialize the case to a dictionary for JSON export."""
        return {
            "case_id": self.case_id,
            "created_at": self.created_at,
            "status": self.status.value,
            "case_type": self.case_type.value,
            "severity": self.severity.value,
            "evidence": self.evidence,
            "hypotheses": self.hypotheses,
            "patch": self.patch,
            "validation_results": self.validation_results,
            "confidence_score": self.confidence_score,
            "verdict": self.verdict,
            "human_approved": self.human_approved,
            "attempt_count": self.attempt_count,
            "history": self.history,
        }

    def __repr__(self) -> str:
        return f"Case(id={self.case_id}, type={self.case_type.value}, status={self.status.value})"
