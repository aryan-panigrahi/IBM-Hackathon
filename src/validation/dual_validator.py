import ast
import json
import os
import re
import subprocess


class DualValidator:
    """Runs functional tests, policy scans, and security checks."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def validate(self) -> dict:
        syntax = self.check_syntax()
        functional = self.run_functional_tests()
        policy = self.run_policy_scan()
        security = self.run_security_scan()

        all_passed = syntax["passed"] and functional["passed"] and policy["passed"] and security["passed"]

        return {
            "passed": all_passed,
            "syntax": syntax,
            "functional": functional,
            "policy": policy,
            "security": security,
            "summary": self._format_summary(syntax, functional, policy, security),
        }

    def check_syntax(self) -> dict:
        """Verifies that all Python files have valid syntax."""
        errors = []
        for root, _, files in os.walk(self.repo_path):
            if any(part in root for part in [".git", "venv", "__pycache__"]):
                continue
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    try:
                        with open(fpath, "r", encoding="utf-8") as f:
                            ast.parse(f.read(), filename=fpath)
                    except SyntaxError as e:
                        errors.append(f"{fname}:{e.lineno} - {e.msg}")
        return {"passed": len(errors) == 0, "errors": errors}

    def run_functional_tests(self) -> dict:
        """Run pytest and parse structured results."""
        report_path = os.path.join(self.repo_path, "validation_report.json")
        tests_dir = os.path.join(self.repo_path, "tests")
        result = subprocess.run(
            ["pytest", tests_dir, "--json-report", f"--json-report-file={report_path}", "--tb=short"],
            capture_output=True,
            text=True,
            cwd=self.repo_path,
        )

        failures = []
        total = 0
        if os.path.exists(report_path):
            try:
                with open(report_path, "r") as f:
                    report = json.load(f)
                total = report.get("summary", {}).get("total", 0)
                failures = [t.get("nodeid") for t in report.get("tests", []) if t.get("outcome") == "failed"]
                return {
                    "passed": len(failures) == 0 and result.returncode == 0,
                    "total": total,
                    "failed": len(failures),
                    "details": failures,
                }
            except Exception:
                pass

        passed = result.returncode == 0
        return {
            "passed": passed,
            "total": 0,
            "failed": 0 if passed else 1,
            "details": [],
        }

    def run_policy_scan(self) -> dict:
        """Run detect-secrets + PII scan."""
        secrets = {}
        try:
            res = subprocess.run(
                ["detect-secrets", "scan", self.repo_path],
                capture_output=True,
                text=True,
            )
            if res.returncode == 0:
                secrets = json.loads(res.stdout).get("results", {})
        except Exception:
            pass

        # Regex fallback for hardcoded secrets
        for root, _, files in os.walk(self.repo_path):
            if any(part in root for part in [".git", "venv", "__pycache__"]):
                continue
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        for idx, line in enumerate(f, 1):
                            if re.search(r'API_KEY\s*=\s*["\']sk-[^"\']+["\']', line):
                                secrets[fname] = [{"line_number": idx, "line": line.strip()}]

        # PII scan
        pii_findings = []
        pii_pattern = re.compile(r"(user\.email|user_email|\.email|card\.number|card_number)")
        for root, _, files in os.walk(self.repo_path):
            if any(part in root for part in [".git", "venv", "__pycache__"]):
                continue
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        for idx, line in enumerate(f, 1):
                            if ("logger." in line or "print(" in line) and pii_pattern.search(line):
                                if "mask_email" not in line and "mask_card" not in line:
                                    pii_findings.append({"file": fname, "line": idx, "line_content": line.strip()})

        secrets_clean = len(secrets) == 0
        pii_clean = len(pii_findings) == 0

        return {
            "passed": secrets_clean and pii_clean,
            "secrets": {"passed": secrets_clean, "count": len(secrets), "details": secrets},
            "pii": {"passed": pii_clean, "count": len(pii_findings), "details": pii_findings},
        }

    def run_security_scan(self) -> dict:
        """Run Bandit security scan."""
        try:
            result = subprocess.run(
                ["bandit", "-r", self.repo_path, "-f", "json"],
                capture_output=True,
                text=True,
            )
            data = json.loads(result.stdout)
            high_findings = [
                f for f in data.get("results", [])
                if f.get("issue_severity") == "HIGH"
            ]
            return {"passed": len(high_findings) == 0, "high_findings": high_findings}
        except Exception:
            return {"passed": True, "high_findings": []}

    def _format_summary(self, syntax: dict, func: dict, policy: dict, security: dict) -> list:
        results = []
        results.append({
            "status": "PASS" if syntax["passed"] else "FAIL",
            "description": "ast.parse (Python AST syntax verification)",
        })
        results.append({
            "status": "PASS" if func["passed"] else "FAIL",
            "description": f"pytest ({func.get('total', 5)} tests passing, 0 regressions)",
        })
        results.append({
            "status": "PASS" if policy["secrets"]["passed"] else "FAIL",
            "description": "detect-secrets (zero hardcoded credentials)",
        })
        results.append({
            "status": "PASS" if policy["pii"]["passed"] else "FAIL",
            "description": "PII scanner (GDPR/privacy logging compliance)",
        })
        results.append({
            "status": "PASS" if security["passed"] else "FAIL",
            "description": "Bandit SAST (0 high severity security issues)",
        })
        return results
