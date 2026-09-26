"""Audit Ledger — Append-only event log for full forensic auditability."""

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


class AuditLedger:
    """Immutable-style event log for Tribunal case investigations.

    Every action taken by the system is recorded with a timestamp,
    case ID, event type, and details. This provides the audit trail
    that judges and compliance teams require.
    """

    def __init__(self, log_dir: str = "logs"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

    def log(self, case_id: str, event_type: str, details: dict[str, Any]) -> None:
        """Append an event to the case-specific JSONL log file."""
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "event": event_type,
            "details": details,
        }
        log_file = self.log_dir / f"{case_id}.jsonl"
        with open(log_file, "a", encoding="utf-8") as f:
            f.write(json.dumps(entry, default=str) + "\n")

    def save_full_case(self, case_dict: dict[str, Any]) -> str:
        """Save the complete case record as a JSON file."""
        case_id = case_dict.get("case_id", "unknown")
        case_file = self.log_dir / f"{case_id}_full.json"
        with open(case_file, "w", encoding="utf-8") as f:
            json.dump(case_dict, f, indent=2, default=str)
        return str(case_file)

    def save_docket(self, case_id: str, docket_text: str) -> str:
        """Save the generated Tribunal Docket as a Markdown file."""
        docket_file = self.log_dir / f"{case_id}_docket.md"
        with open(docket_file, "w", encoding="utf-8") as f:
            f.write(docket_text)
        return str(docket_file)

    def get_case_log(self, case_id: str) -> list[dict[str, Any]]:
        """Read all events for a specific case."""
        log_file = self.log_dir / f"{case_id}.jsonl"
        if not log_file.exists():
            return []
        events = []
        with open(log_file, encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    events.append(json.loads(line))
        return events
