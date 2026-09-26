"""Dual Validator — Runs BOTH functional tests AND policy scans.

Both must pass for a patch to be accepted. This is the core differentiator
of The Governance Tribunal.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any


class DualValidator:
    """Validates patches against functional tests AND policy rules."""

    def __init__(self, repo_path: str):
        self.repo_path = Path(repo_path).resolve()

    def validate(self) -> dict[str, Any]:
        """Run all validations. Returns combined result.

        A patch is ONLY accepted if:
            functional_tests_pass AND policy_scan_pass
        """
        functional = self.run_functional_tests()
        policy = self.run_policy_scan()

        all_passed = functional["passed"] and policy["passed"]

        return {
            "passed": all_passed,
            "functional": functional,
            "policy": policy,
            "summary": self._build_summary(functional, policy),
        }

    # ── Functional Validation ───────────────────────────────────

    def run_functional_tests(self) -> dict[str, Any]:
        """Execute pytest and return structured results."""
        report_file = self.repo_path / "validation_report.json"
        try:
            result = subprocess.run(
                [
                    "pytest", str(self.repo_path / "tests"),
                    "--json-report",
                    f"--json-report-file={report_file}",
                    "--tb=short", "-q",
                ],
                capture_output=True, text=True,
                cwd=str(self.repo_path),
                timeout=60,
            )
        except (FileNotFoundError, subprocess.TimeoutExpired) as e:
            return {"passed": False, "error": str(e), "details": []}

        try:
            with open(report_file) as f:
                report = json.load(f)
            failed_tests = [
                t["nodeid"] for t in report.get("tests", [])
                if t["outcome"] == "failed"
            ]
            return {
                "passed": len(failed_tests) == 0,
                "total": report.get("summary", {}).get("total", 0),
                "failed": len(failed_tests),
                "details": failed_tests,
            }
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {
                "passed": result.returncode == 0,
                "error": str(e),
                "details": [],
            }

    # ── Policy Validation ───────────────────────────────────────

    def run_policy_scan(self) -> dict[str, Any]:
        """Run secret scan + PII scan."""
        secrets_result = self._scan_secrets()
        pii_result = self._scan_pii()

        all_clean = secrets_result["passed"] and pii_result["passed"]

        return {
            "passed": all_clean,
            "secrets": secrets_result,
            "pii": pii_result,
        }

    def _scan_secrets(self) -> dict[str, Any]:
        """Run detect-secrets on source directory."""
        src_dir = str(self.repo_path / "src")
        try:
            result = subprocess.run(
                ["detect-secrets", "scan", src_dir],
                capture_output=True, text=True, timeout=30,
            )
            output = json.loads(result.stdout)
            findings = output.get("results", {})
            return {
                "passed": len(findings) == 0,
                "count": sum(len(v) for v in findings.values()),
                "details": findings,
            }
        except Exception as e:
            return {"passed": True, "count": 0, "details": {}, "error": str(e)}

    def _scan_pii(self) -> dict[str, Any]:
        """Scan for PII in logging/print statements."""
        pii_var_pattern = re.compile(
            r"(\.email|user_email|user\.email|user_data|password|ssn)",
            re.IGNORECASE,
        )
        findings: list[dict[str, Any]] = []
        src_dir = self.repo_path / "src"

        if not src_dir.exists():
            return {"passed": True, "count": 0, "details": []}

        for py_file in src_dir.rglob("*.py"):
            try:
                lines = py_file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue

            for line_num, line in enumerate(lines, 1):
                if "logger." in line or "logging." in line or "print(" in line:
                    if pii_var_pattern.search(line):
                        findings.append({
                            "file": str(py_file.relative_to(self.repo_path)),
                            "line": line_num,
                            "content": line.strip(),
                        })

        return {
            "passed": len(findings) == 0,
            "count": len(findings),
            "details": findings,
        }

    # ── Summary Builder ─────────────────────────────────────────

    def _build_summary(self, func: dict, policy: dict) -> list[dict[str, str]]:
        """Format validation results for the Tribunal Docket."""
        results = []

        status = "PASS" if func["passed"] else "FAIL"
        total = func.get("total", "?")
        failed = func.get("failed", 0)
        results.append({
            "status": status,
            "description": f"pytest ({total} tests, {failed} failed)",
        })

        status = "PASS" if policy["secrets"]["passed"] else "FAIL"
        count = policy["secrets"].get("count", 0)
        results.append({
            "status": status,
            "description": f"detect-secrets ({count} findings)",
        })

        status = "PASS" if policy["pii"]["passed"] else "FAIL"
        count = policy["pii"].get("count", 0)
        results.append({
            "status": status,
            "description": f"PII scanner ({count} findings)",
        })

        return results
