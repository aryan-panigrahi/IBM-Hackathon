"""Governance Tribunal — Main orchestrator that ties all components together.

This is the brain of the system. It coordinates:
1. Evidence collection
2. Case classification  
3. Root cause investigation
4. Patch generation (via IBM Bob 2.0)
5. Dual validation (tests + policy scans)
6. Docket generation
7. Human approval
8. Audit logging
"""

import sys
from pathlib import Path
from typing import Any

# Add project root to path for imports
project_root = Path(__file__).resolve().parent.parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from src.orchestrator.case_manager import Case, CaseStatus, CaseType, Severity
from src.orchestrator.classifier import (
    classify_case_type,
    classify_severity,
    compute_confidence,
    should_require_human_approval,
)
from src.evidence.collector import EvidenceCollector
from src.validation.dual_validator import DualValidator
from src.reporting.docket_generator import DocketGenerator
from src.ledger.audit_ledger import AuditLedger


class GovernanceTribunal:
    """The master orchestrator for forensic compliance investigations.

    Coordinates the full lifecycle:
    TRIGGER -> EVIDENCE -> CLASSIFY -> INVESTIGATE -> PATCH -> VALIDATE -> DOCKET -> APPROVE
    """

    def __init__(
        self,
        repo_path: str,
        test_path: str = "tests",
        policy_dir: str = "policies",
        template_dir: str = "templates",
        log_dir: str = "logs",
        max_retries: int = 2,
    ):
        self.repo_path = Path(repo_path).resolve()
        self.max_retries = max_retries

        # Resolve paths relative to project root if not absolute
        policy_path = Path(policy_dir)
        if not policy_path.is_absolute():
            policy_path = project_root / policy_dir

        template_path = Path(template_dir)
        if not template_path.is_absolute():
            template_path = project_root / template_dir

        log_path = Path(log_dir)
        if not log_path.is_absolute():
            log_path = project_root / log_dir

        # Initialize components
        self.collector = EvidenceCollector(str(self.repo_path), str(policy_path))
        self.validator = DualValidator(str(self.repo_path))
        self.docket_gen = DocketGenerator(str(template_path))
        self.ledger = AuditLedger(str(log_path))
        self.case = Case()

    def collect_evidence(self) -> dict[str, Any]:
        """Phase 1: The Subpoena — Collect all forensic evidence."""
        evidence = self.collector.collect_all()
        self.case.evidence = evidence
        self.case.update_status(CaseStatus.EVIDENCE_COLLECTED)

        self.ledger.log(self.case.case_id, "evidence_collected", {
            "tests_passed": evidence["test_results"]["passed"],
            "test_failures": evidence["test_results"].get("failed_count", 0),
            "secrets_clean": evidence["secret_scan"]["passed"],
            "pii_clean": evidence["pii_scan"]["passed"],
            "policies_loaded": list(evidence["policies"].keys()),
            "changed_files": evidence["changed_files"],
        })
        return evidence

    def classify(self, evidence: dict[str, Any]) -> Case:
        """Phase 2: Classification — Determine case type and severity."""
        case_type_str = classify_case_type(evidence)
        severity_str = classify_severity(evidence)

        self.case.case_type = CaseType(case_type_str)
        self.case.severity = Severity(severity_str)
        self.case.update_status(CaseStatus.CASE_CLASSIFIED)

        self.ledger.log(self.case.case_id, "case_classified", {
            "type": case_type_str,
            "severity": severity_str,
        })
        return self.case

    def run_remediation_loop(self, case: Case) -> dict[str, Any]:
        """Phase 3-5: The Investigation → Patch → Dual Validation loop.

        This is THE CORE AGENTIC LOOP.
        In a full implementation, IBM Bob 2.0 handles steps 3-4 via MCP tools.
        For MVP, we demonstrate the loop structure with scripted fixes.
        """
        result: dict[str, Any] = {
            "root_cause": "",
            "suspect": {},
            "patch_summary": "",
            "files_patched": [],
            "validations": [],
            "parole_conditions": [],
            "residual_risks": "None identified.",
            "verdict": "PENDING",
        }

        # ── INVESTIGATION: Trace root cause via git blame ──
        failures = case.evidence.get("test_results", {}).get("failures", [])
        if failures:
            first = failures[0]
            suspect = self.collector.blame_line(
                first.get("file", ""), first.get("line", 0)
            )
            if suspect:
                result["suspect"] = suspect
                result["root_cause"] = (
                    f"Commit {suspect['commit'][:7]} by {suspect['author']}: "
                    f"{suspect['message']}"
                )
                case.add_hypothesis(
                    f"Code change in commit {suspect['commit'][:7]} introduced the defect",
                    0.85,
                )

        # Add policy-related hypotheses
        if not case.evidence.get("secret_scan", {}).get("passed", True):
            case.add_hypothesis("Hardcoded secrets introduced in recent commit", 0.95)
        if not case.evidence.get("pii_scan", {}).get("passed", True):
            case.add_hypothesis("PII data exposed in logging statements", 0.90)

        case.update_status(CaseStatus.HYPOTHESES_GENERATED)
        case.update_status(CaseStatus.ROOT_CAUSE_SELECTED)

        # Compute confidence
        reproduction_success = not case.evidence["test_results"]["passed"]
        case.confidence_score = compute_confidence(case.evidence, reproduction_success)

        self.ledger.log(case.case_id, "investigation_complete", {
            "hypotheses": case.hypotheses,
            "confidence_score": case.confidence_score,
            "root_cause": result["root_cause"],
        })

        # ── REMEDIATION LOOP: Bob patches → validate → retry ──
        for attempt in range(1, self.max_retries + 1):
            case.attempt_count = attempt
            case.update_status(CaseStatus.PATCH_GENERATED)

            self.ledger.log(case.case_id, "patch_attempt", {
                "attempt": attempt,
                "max_retries": self.max_retries,
            })

            # ══════════════════════════════════════════════════════
            # BOB 2.0 WRITES THE PATCH HERE
            # In production: Bob reads errors + policies + code,
            # then generates a fix using write_file MCP tool.
            #
            # For demo: apply_scripted_fix() applies the known fix
            # to the demo repository's intentional defects.
            # ══════════════════════════════════════════════════════
            patch_applied = self._apply_fix(case, attempt)
            if not patch_applied:
                continue

            # ── DUAL VALIDATION ──
            case.update_status(CaseStatus.VALIDATION_EXECUTED)
            validation = self.validator.validate()
            result["validations"] = validation["summary"]

            self.ledger.log(case.case_id, "validation_result", {
                "attempt": attempt,
                "overall_passed": validation["passed"],
                "functional_passed": validation["functional"]["passed"],
                "policy_passed": validation["policy"]["passed"],
            })

            if validation["passed"]:
                # ✅ SUCCESS — Both tests and policy pass
                result["verdict"] = "GUILTY. REMEDIATED. AWAITING HUMAN PAROLE APPROVAL."
                result["patch_summary"] = self._describe_patch(case)
                result["files_patched"] = self._get_patched_files(case)
                result["parole_conditions"] = [
                    "Added regression test: test_no_pii_in_logs()",
                    "Pre-commit hook recommended to block raw PII logging",
                    "Secrets moved to environment variables",
                ]
                case.update_status(CaseStatus.VERDICT_GENERATED)
                return result

        # ❌ MAX RETRIES EXHAUSTED — Escalate
        result["verdict"] = "COULD NOT REMEDIATE. ESCALATED TO HUMAN ENGINEER."
        result["residual_risks"] = (
            f"Automated remediation failed after {self.max_retries} attempts. "
            "Manual intervention required."
        )
        case.update_status(CaseStatus.ESCALATED)
        return result

    def _apply_fix(self, case: Case, attempt: int) -> bool:
        """Apply a fix to the demo repository.

        In the real hackathon demo, IBM Bob 2.0 generates this fix
        via Agent Mode. For MVP, we apply scripted fixes to the
        known intentional defects in the demo repository.
        """
        src_dir = self.repo_path / "src"
        if not src_dir.exists():
            return False

        fixed_any = False

        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
                original = content

                # Fix DEFECT 2: PII in login — email logged in plain text
                content = content.replace(
                    'logger.info(f"User login attempt: {user.email}")',
                    'logger.info(f"User login attempt: {hash(user.email)}")',
                )
                content = content.replace(
                    'logger.warning(f"Login failed for {user.email}")',
                    'logger.warning("Login failed for user")',
                )

                # Fix DEFECT 4: PII in checkout retry logging
                content = content.replace(
                    'logger.info(f"Retrying checkout for {user.email}")',
                    'logger.info(f"Retrying for user_{hash(user.email) % 10000}")',
                )

                # Fix DEFECT 3: Hardcoded AWS credentials → env vars
                content = content.replace(
                    'AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"',
                    'AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID", "")',
                )
                content = content.replace(
                    'AWS_SECRET_ACCESS_KEY = "wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY"',
                    'AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY", "")',
                )

                # Fix DEFECT 1: Unbounded retry loop → bounded for loop
                content = content.replace(
                    "    while True:\n"
                    "        try:\n"
                    "            result = process_payment(cart)\n"
                    "            logger.info(f\"Checkout completed: ${cart.total}\")\n"
                    "            return result\n"
                    "        except DatabaseError:\n"
                    "            time.sleep(0.1)  # No max retries — infinite loop!",
                    "    for _retry in range(3):  # Bounded retry\n"
                    "        try:\n"
                    "            result = process_payment(cart)\n"
                    "            logger.info(f\"Checkout completed: ${cart.total}\")\n"
                    "            return result\n"
                    "        except DatabaseError:\n"
                    "            time.sleep(0.1)\n"
                    "    raise TimeoutError(\"Checkout failed after 3 retries\")",
                )

                if content != original:
                    py_file.write_text(content, encoding="utf-8")
                    fixed_any = True

            except (OSError, UnicodeDecodeError):
                continue

        return fixed_any

    def _describe_patch(self, case: Case) -> str:
        """Generate a human-readable description of what was patched."""
        descriptions = []
        if not case.evidence.get("pii_scan", {}).get("passed", True):
            descriptions.append("Replaced PII logging with hashed identifiers")
        if not case.evidence.get("secret_scan", {}).get("passed", True):
            descriptions.append("Moved hardcoded secrets to environment variables")
        if not case.evidence.get("test_results", {}).get("passed", True):
            descriptions.append("Fixed unbounded retry loop with bounded retries")
        return ". ".join(descriptions) or "Patch applied."

    def _get_patched_files(self, case: Case) -> list[str]:
        """List files that were patched."""
        files = set()
        for f in case.evidence.get("test_results", {}).get("failures", []):
            if f.get("file"):
                files.add(f["file"])
        for f in case.evidence.get("pii_scan", {}).get("findings", []):
            if f.get("file"):
                files.add(f["file"])
        for filepath in case.evidence.get("secret_scan", {}).get("findings", {}).keys():
            files.add(filepath)
        return list(files) or ["unknown"]

    def generate_docket(self, case: Case, result: dict[str, Any]) -> str:
        """Phase 6: Generate the Tribunal Docket."""
        docket = self.docket_gen.generate(case, result)
        self.ledger.save_docket(case.case_id, docket)
        return docket

    def save_audit_log(self, case: Case, result: dict[str, Any], approved: bool) -> None:
        """Phase 7: Save the final audit trail."""
        case.human_approved = approved
        case.update_status(
            CaseStatus.CASE_CLOSED if approved else CaseStatus.ESCALATED
        )
        case.verdict = result.get("verdict", "UNKNOWN")

        self.ledger.log(case.case_id, "human_decision", {
            "approved": approved,
            "verdict": case.verdict,
        })
        self.ledger.save_full_case(case.to_dict())
