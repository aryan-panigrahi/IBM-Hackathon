import json
import os
from datetime import datetime, timezone


class AuditLedger:
    """Append-only audit trail and case archive."""

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)

    def log(self, case_id: str, event_type: str, details: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "event": event_type,
            "details": details,
        }
        log_file = os.path.join(self.log_dir, f"{case_id}.jsonl")
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry) + "\n")

    def save_full_case(self, case_dict: dict):
        """Save complete case record as JSON."""
        case_id = case_dict.get("case_id", "case")
        case_file = os.path.join(self.log_dir, f"{case_id}_full.json")
        with open(case_file, "w", encoding="utf-8") as f:
            json.dump(case_dict, f, indent=2)
