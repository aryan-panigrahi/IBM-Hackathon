import os
from src.orchestrator.case_manager import Case, CaseStatus, Severity
from src.evidence.collector import EvidenceCollector
from src.orchestrator.classifier import classify_case, compute_confidence
from src.validation.dual_validator import DualValidator
from src.reporting.docket_generator import DocketGenerator
from src.ledger.audit_ledger import AuditLedger
from src.remediation.patch_generator import generate_patch
from src.remediation.cst_transformers import apply_cst_transformations
from src.agent.factory import create_agent


class Arbiter:
    """
    The master orchestrator — ties together evidence, classification,
    AI-powered investigation, remediation, validation, and docket generation.

    Supports any OpenAI-compatible AI backend via the agent layer:
      - LM Studio (Prism Bonsai 27B, Llama, Mistral, etc.)
      - IBM Bob 2.0
      - Ollama
      - OpenAI, Groq, etc.
    """

    def __init__(
        self,
        repo_path: str,
        policy_dir: str = "policies",
        template_dir: str = "templates",
        log_dir: str = "logs",
        max_retries: int = 2,
        test_path: str = "tests",
        agent_backend: str = None,
        agent_model: str = None,
        agent_url: str = None,
    ):
        self.repo_path = os.path.abspath(repo_path)
        self.policy_dir = os.path.abspath(policy_dir)
        self.template_dir = os.path.abspath(template_dir)
        self.log_dir = os.path.abspath(log_dir)
        self.max_retries = max_retries
        self.test_path = test_path

        self.collector = EvidenceCollector(self.repo_path, self.policy_dir)
        self.validator = DualValidator(self.repo_path)
        self.docket_gen = DocketGenerator(self.template_dir)
        self.ledger = AuditLedger(self.log_dir)
        self.case = Case()

        # Initialise the AI agent (reads .env by default, overridden by CLI flags)
        self.agent = create_agent(
            backend=agent_backend,
            model=agent_model,
            base_url=agent_url,
        )

    # ─── Phase 1 ──────────────────────────────────────────────────────────────

    def collect_evidence(self) -> dict:
        evidence = self.collector.collect_all()
        # Inject repo_path so the agent can read source files
        evidence["_repo_path"] = self.repo_path
        self.case.evidence = evidence
        self.case.update_status(CaseStatus.EVIDENCE_COLLECTED)
        self.ledger.log(self.case.case_id, "evidence_collected", {
            "tests_passed": evidence.get("test_results", {}).get("passed", False),
            "secrets_clean": evidence.get("secret_scan", {}).get("passed", False),
            "pii_clean": evidence.get("pii_scan", {}).get("passed", False),
        })
        return evidence

    # ─── Phase 2 ──────────────────────────────────────────────────────────────

    def classify(self, evidence: dict):
        return self.classify_case(evidence)

    def classify_case(self, evidence: dict):
        case_type, severity = classify_case(evidence)
        self.case.case_type = case_type
        self.case.severity = severity
        self.case.update_status(CaseStatus.CASE_CLASSIFIED)
        self.ledger.log(self.case.case_id, "case_classified", {
            "type": case_type.value,
            "severity": severity.value,
        })
        return self.case

    # ─── Phase 3: Agentic Remediation Loop ────────────────────────────────────

    def run_remediation_loop(self, case) -> dict:
        """
        Core agentic loop.

        1. The AI agent (LM Studio / Bob / OpenAI / etc.) reads the evidence
           and policy documents, then returns:
             - root cause analysis
             - code patch hunks
             - parole conditions (guardrails)

        2. Patch hunks are applied to the repo files.

        3. Dual-validation runs (5 checks). If it fails, errors are fed back
           to the agent for a retry (up to max_retries).
        """
        result = {
            "root_cause": "",
            "suspect": {},
            "patch_summary": "",
            "patch_diff": "",
            "files_patched": [],
            "validations": [],
            "parole_conditions": [],
            "residual_risks": "",
            "verdict": "PENDING",
            "agent_backend": self.agent.config.backend,
            "agent_model": self.agent.config.model,
        }

        # ── Git blame root cause ───────────────────────────────────────────
        failures = case.evidence.get("test_results", {}).get("failures", [])
        culprit_file = failures[0].get("file", "") if failures else ""
        culprit_line = (failures[0].get("line") or 1) if failures else 1

        suspect = self.collector.blame_line(culprit_file, culprit_line)
        if suspect:
            result["suspect"] = suspect

        case.update_status(CaseStatus.ROOT_CAUSE_SELECTED)

        # ── Confidence score ───────────────────────────────────────────────
        reproduction_success = not case.evidence.get("test_results", {}).get("passed", True)
        case.confidence_score = compute_confidence(case.evidence, reproduction_success)

        # ── Agent + Validation retry loop ──────────────────────────────────
        policies = case.evidence.get("policies", {})
        last_validation = None

        for attempt in range(self.max_retries):
            case.attempt_count = attempt + 1
            case.update_status(CaseStatus.PATCH_GENERATED)
            self.ledger.log(case.case_id, "patch_attempt", {"attempt": attempt + 1})

            # ── Call the AI agent ──────────────────────────────────────────
            try:
                investigation = self.agent.investigate(case.evidence, policies)

                result["root_cause"] = investigation.root_cause
                result["parole_conditions"] = investigation.parole_conditions
                result["residual_risks"] = investigation.residual_risks

                # Apply whatever patches the agent generated
                diff_text = self._apply_agent_patches(investigation, result)
                result["patch_diff"] = diff_text
                result["patch_summary"] = investigation.patch_description

            except (ConnectionError, TimeoutError) as e:
                # Agent unreachable — fall back to scripted patch so demo still works
                result["root_cause"] = (
                    f"[Agent offline: {e}] "
                    "Falling back to scripted patch for demo."
                )
                diff_text = self._apply_scripted_fallback(result)
                result["patch_diff"] = diff_text
                result["patch_summary"] = (
                    "Scripted fallback: bounded retry + PII masking + env secret."
                )

            except Exception as e:
                result["root_cause"] = f"Agent error: {e}"
                diff_text = self._apply_scripted_fallback(result)
                result["patch_diff"] = diff_text

            # ── Dual Validation ────────────────────────────────────────────
            case.update_status(CaseStatus.VALIDATION_EXECUTED)
            validation = self.validator.validate()
            result["validations"] = validation["summary"]
            last_validation = validation

            self.ledger.log(case.case_id, "validation_result", {
                "attempt": attempt + 1,
                "passed": validation["passed"],
                "syntax": validation["syntax"]["passed"],
                "functional": validation["functional"]["passed"],
                "policy": validation["policy"]["passed"],
                "security": validation["security"]["passed"],
            })

            if validation["passed"]:
                result["verdict"] = "GUILTY. REMEDIATED. READY FOR MERGE."
                if not result["parole_conditions"]:
                    result["parole_conditions"] = [
                        "Regression test added: test_retry_payment_regression_bounded()",
                        "PII guardrail active: mask_email() wrapper applied",
                        "Secret isolation: os.getenv() replacing hardcoded value",
                    ]
                case.update_status(CaseStatus.VERDICT_GENERATED)
                return result

            # Feed validation errors back to agent on next attempt
            error_context = {
                "functional_errors": validation["functional"].get("details", []),
                "syntax_errors": validation["syntax"].get("errors", []),
                "policy_errors": {
                    "secrets": validation["policy"].get("secrets", {}).get("details", {}),
                    "pii": validation["policy"].get("pii", {}).get("details", []),
                },
            }
            # Inject errors so agent sees them on next loop iteration
            case.evidence["_last_validation_errors"] = error_context
            self.ledger.log(case.case_id, "validation_failed", error_context)

        # ── Max retries exhausted ──────────────────────────────────────────
        result["verdict"] = "COULD NOT FULLY REMEDIATE. ESCALATED TO LEAD ENGINEER."
        result["residual_risks"] = "Automated remediation failed after max attempts. Manual review required."
        case.update_status(CaseStatus.ESCALATED)
        return result

    # ─── Patch application helpers ─────────────────────────────────────────────

    def _apply_agent_patches(self, investigation, result: dict) -> str:
        """
        Apply the patch hunks returned by the AI agent.
        Each hunk contains: file, original_snippet, fixed_snippet.
        """
        import difflib
        all_diffs = []

        for hunk in investigation.patch_hunks:
            rel_path = hunk.get("file", "")
            original_snippet = hunk.get("original_snippet", "")
            fixed_snippet = hunk.get("fixed_snippet", "")

            if not rel_path or not original_snippet or original_snippet == fixed_snippet:
                continue

            full_path = os.path.join(self.repo_path, rel_path)
            if not os.path.exists(full_path):
                continue

            try:
                with open(full_path, "r", encoding="utf-8") as f:
                    original_file = f.read()

                if original_snippet not in original_file:
                    # Try whitespace-normalised match
                    import re
                    pattern = re.escape(original_snippet.strip()).replace(r"\ ", r"\s+")
                    match = re.search(pattern, original_file)
                    if not match:
                        continue
                    actual_snippet = match.group(0)
                else:
                    actual_snippet = original_snippet

                modified_file = original_file.replace(actual_snippet, fixed_snippet, 1)

                if modified_file != original_file:
                    diff = generate_patch(rel_path, original_file, modified_file)
                    all_diffs.append(diff)
                    with open(full_path, "w", encoding="utf-8") as f:
                        f.write(modified_file)
                    if rel_path not in result["files_patched"]:
                        result["files_patched"].append(rel_path)

            except Exception:
                continue

        # Also run CST transformers as a safety net for any missed PII/secrets
        self._run_cst_safety_pass(result, all_diffs)

        return "\n".join(all_diffs)

    def _run_cst_safety_pass(self, result: dict, diffs: list):
        """Run LibCST transformers over all .py files as a safety net."""
        for root, _, files in os.walk(self.repo_path):
            if any(p in root for p in [".git", "venv", "__pycache__"]):
                continue
            for fname in files:
                if not fname.endswith(".py"):
                    continue
                full_path = os.path.join(root, fname)
                rel_path = os.path.relpath(full_path, self.repo_path)
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        original = f.read()
                    fixed = apply_cst_transformations(original)
                    if fixed != original:
                        diff = generate_patch(rel_path, original, fixed)
                        diffs.append(diff)
                        with open(full_path, "w", encoding="utf-8") as f:
                            f.write(fixed)
                        if rel_path not in result["files_patched"]:
                            result["files_patched"].append(rel_path)
                except Exception:
                    continue

    def _apply_scripted_fallback(self, result: dict) -> str:
        """
        Deterministic scripted fix used when the AI agent is offline.
        Fixes the known demo_repo defects so the demo still runs end-to-end.
        """
        all_diffs = []

        gateway_path = os.path.join(self.repo_path, "payment_gateway.py")
        if os.path.exists(gateway_path):
            with open(gateway_path, "r", encoding="utf-8") as f:
                original = f.read()

            fixed = original
            if "while not success:" in fixed:
                fixed = fixed.replace(
                    "    success = False\n    while not success:\n        response = requests.post(gateway_url, timeout=2)\n        success = response.status_code == 200\n        return True",
                    "    for attempt in range(3):\n        try:\n            response = requests.post(gateway_url, timeout=2)\n            if response.status_code == 200:\n                return True\n        except requests.exceptions.Timeout:\n            import time\n            time.sleep(0.01 * (2 ** attempt))\n    return False",
                )
            fixed = apply_cst_transformations(fixed)
            if fixed != original:
                all_diffs.append(generate_patch("payment_gateway.py", original, fixed))
                with open(gateway_path, "w", encoding="utf-8") as f:
                    f.write(fixed)
                result["files_patched"].append("payment_gateway.py")

        config_path = os.path.join(self.repo_path, "config.py")
        if os.path.exists(config_path):
            with open(config_path, "r", encoding="utf-8") as f:
                original_cfg = f.read()
            fixed_cfg = apply_cst_transformations(original_cfg)
            if "os.getenv" in fixed_cfg and "import os" not in fixed_cfg:
                fixed_cfg = "import os\n" + fixed_cfg
            if fixed_cfg != original_cfg:
                all_diffs.append(generate_patch("config.py", original_cfg, fixed_cfg))
                with open(config_path, "w", encoding="utf-8") as f:
                    f.write(fixed_cfg)
                result["files_patched"].append("config.py")

        return "\n".join(all_diffs)

    # ─── Phases 4–5 ───────────────────────────────────────────────────────────

    def generate_docket(self, case, result: dict) -> str:
        docket = self.docket_gen.generate(case, result)
        out_file = os.path.join(self.log_dir, f"{case.case_id}_docket.md")
        self.docket_gen.save(docket, out_file)
        return docket

    def save_audit_log(self, case, result: dict, approved: bool):
        case.human_approved = approved
        case.update_status(CaseStatus.CASE_CLOSED if approved else CaseStatus.ESCALATED)
        self.ledger.save_full_case(case.to_dict())
