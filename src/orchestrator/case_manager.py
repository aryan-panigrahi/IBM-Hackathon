import uuid
from datetime import datetime, timezone
from enum import Enum


class CaseType(Enum):
    FUNCTIONAL = "functional"
    POLICY = "policy"
    COMBINED = "combined"
    UNKNOWN = "unknown"


class CaseStatus(Enum):
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
    HIGH = "high"      # auth, payments, secrets, privacy, DB migration
    MEDIUM = "medium"  # business logic, API behavior, tests
    LOW = "low"        # docs, formatting, minor refactor


class Case:
    def __init__(self, case_id: str = None):
        self.case_id = case_id or f"GT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
        self.created_at = datetime.now(timezone.utc).isoformat()
        self.status = CaseStatus.TRIGGER_RECEIVED
        self.case_type = CaseType.UNKNOWN
        self.severity = Severity.MEDIUM
        self.evidence = {}
        self.hypotheses = []
        self.patch = None
        self.validation_results = {}
        self.confidence_score = 0.0
        self.verdict = None
        self.human_approved = None
        self.attempt_count = 0
        self.history = []

    def log_event(self, event_type: str, details: dict):
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "details": details,
        })

    def update_status(self, new_status: CaseStatus):
        self.status = new_status
        self.log_event("status_change", {"new_status": new_status.value})

    def to_dict(self) -> dict:
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
