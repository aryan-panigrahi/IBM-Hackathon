"""Evidence Collector — Gathers forensic evidence from the target repository.

Collects: test results, secret scans, PII scans, git history, policy documents.
"""

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Optional


class EvidenceCollector:
    """Collects all forensic evidence needed for a Tribunal investigation."""

    PII_PATTERNS: dict[str, str] = {
        "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
        "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        "Phone": r"\b\d{3}[-.]?\d{3}[-.]?\d{4}\b",
        "CreditCard": r"\b(?:\d[ -]*?){13,16}\b",
    }

    PII_VARIABLE_PATTERN = re.compile(
        r"(\.email|user_email|user\.email|user_data|password|ssn|credit_card)",
        re.IGNORECASE,
    )

    def __init__(self, repo_path: str, policy_dir: str):
        self.repo_path = Path(repo_path).resolve()
        self.policy_dir = Path(policy_dir).resolve()

    def collect_all(self) -> dict[str, Any]:
        """Run all evidence collection steps and return combined results."""
        return {
            "test_results": self.run_tests(),
            "secret_scan": self.run_secret_scan(),
            "pii_scan": self.run_pii_scan(),
            "recent_commits": self.get_recent_commits(),
            "changed_files": self.get_changed_files(),
            "policies": self.load_policies(),
        }

    # ── Test Runner ──────────────────────────────────────────────

    def run_tests(self) -> dict[str, Any]:
        """Run pytest with JSON report and return structured results."""
        report_file = self.repo_path / "temp_report.json"
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
        except FileNotFoundError:
            return {"passed": False, "failures": [], "error": "pytest not found"}
        except subprocess.TimeoutExpired:
            return {"passed": False, "failures": [], "error": "pytest timed out"}

        try:
            with open(report_file) as f:
                report = json.load(f)
        except (FileNotFoundError, json.JSONDecodeError) as e:
            return {
                "passed": result.returncode == 0,
                "failures": [],
                "stdout": result.stdout,
                "stderr": result.stderr,
                "error": str(e),
            }

        failures = []
        for test in report.get("tests", []):
            if test["outcome"] == "failed":
                crash = test.get("call", {}).get("crash", {})
                failures.append({
                    "test_id": test["nodeid"],
                    "file": crash.get("path", ""),
                    "line": crash.get("lineno", 0),
                    "message": crash.get("message", ""),
                    "longrepr": test.get("call", {}).get("longrepr", ""),
                })

        return {
            "passed": len(failures) == 0,
            "total": report.get("summary", {}).get("total", 0),
            "failed_count": len(failures),
            "failures": failures,
        }

    # ── Secret Scanner ──────────────────────────────────────────

    def run_secret_scan(self) -> dict[str, Any]:
        """Run detect-secrets scan and return findings."""
        scan_path = str(self.repo_path / "src")
        try:
            result = subprocess.run(
                ["detect-secrets", "scan", scan_path],
                capture_output=True, text=True, timeout=30,
            )
            output = json.loads(result.stdout)
            findings = output.get("results", {})
            return {"passed": len(findings) == 0, "findings": findings}
        except FileNotFoundError:
            return {"passed": True, "findings": {}, "error": "detect-secrets not installed"}
        except (json.JSONDecodeError, subprocess.TimeoutExpired) as e:
            return {"passed": True, "findings": {}, "error": str(e)}

    # ── PII Scanner ─────────────────────────────────────────────

    def run_pii_scan(self) -> dict[str, Any]:
        """Scan Python source files for PII in logging/print statements."""
        findings: list[dict[str, Any]] = []
        src_dir = self.repo_path / "src"

        if not src_dir.exists():
            return {"passed": True, "findings": []}

        for py_file in src_dir.rglob("*.py"):
            try:
                content = py_file.read_text(encoding="utf-8")
            except (OSError, UnicodeDecodeError):
                continue

            for line_num, line in enumerate(content.splitlines(), 1):
                if not ("logger." in line or "logging." in line or "print(" in line):
                    continue

                # Check for PII variable patterns
                if self.PII_VARIABLE_PATTERN.search(line):
                    findings.append({
                        "file": str(py_file.relative_to(self.repo_path)),
                        "line": line_num,
                        "type": "PII_Variable",
                        "content": line.strip(),
                    })
                    continue

                # Check for PII data patterns
                for pii_type, pattern in self.PII_PATTERNS.items():
                    if re.search(pattern, line):
                        findings.append({
                            "file": str(py_file.relative_to(self.repo_path)),
                            "line": line_num,
                            "type": pii_type,
                            "content": line.strip(),
                        })
                        break  # One finding per line is enough

        return {"passed": len(findings) == 0, "findings": findings}

    # ── Git History ─────────────────────────────────────────────

    def get_recent_commits(self, n: int = 10) -> list[dict[str, str]]:
        """Get the N most recent commits."""
        try:
            result = subprocess.run(
                ["git", "log", f"-{n}", "--format=%H|%an|%aI|%s"],
                capture_output=True, text=True,
                cwd=str(self.repo_path),
            )
            commits = []
            for line in result.stdout.strip().splitlines():
                parts = line.split("|", 3)
                if len(parts) == 4:
                    commits.append({
                        "sha": parts[0][:7],
                        "author": parts[1],
                        "date": parts[2],
                        "message": parts[3],
                    })
            return commits
        except Exception:
            return []

    def get_changed_files(self) -> list[str]:
        """Get files changed in the most recent commit."""
        try:
            result = subprocess.run(
                ["git", "diff", "--name-only", "HEAD~1", "HEAD"],
                capture_output=True, text=True,
                cwd=str(self.repo_path),
            )
            return [f for f in result.stdout.strip().splitlines() if f]
        except Exception:
            return []

    def blame_line(self, file_path: str, line_num: int) -> Optional[dict[str, str]]:
        """Git blame a specific line to identify the culprit commit."""
        try:
            result = subprocess.run(
                ["git", "blame", "-L", f"{line_num},{line_num}",
                 "--porcelain", file_path],
                capture_output=True, text=True,
                cwd=str(self.repo_path),
            )
            lines = result.stdout.splitlines()
            if not lines:
                return None

            commit_sha = lines[0].split()[0]
            author = ""
            summary = ""
            for line in lines:
                if line.startswith("author "):
                    author = line[len("author "):]
                elif line.startswith("summary "):
                    summary = line[len("summary "):]

            # Get the diff for this commit
            diff_result = subprocess.run(
                ["git", "diff", f"{commit_sha}~1", commit_sha, "--", file_path],
                capture_output=True, text=True,
                cwd=str(self.repo_path),
            )

            return {
                "commit": commit_sha,
                "author": author,
                "message": summary,
                "diff": diff_result.stdout,
            }
        except Exception:
            return None

    # ── Policy Loader ───────────────────────────────────────────

    def load_policies(self) -> dict[str, str]:
        """Load all policy Markdown files from the policy directory."""
        policies: dict[str, str] = {}
        if not self.policy_dir.exists():
            return policies
        for md_file in self.policy_dir.glob("*.md"):
            try:
                policies[md_file.name] = md_file.read_text(encoding="utf-8")
            except OSError:
                continue
        return policies
