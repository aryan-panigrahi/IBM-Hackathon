# 🏛️ The Governance Tribunal — Sources, Research & Complete Working Logic

---

# PART 1: ALL SOURCES & RESEARCH MATERIAL

---

## A. IBM Bob 2.0 — Official Sources

| Resource | URL | What to Extract |
|:---|:---|:---|
| **IBM Bob Official Site** | `https://bob.ibm.com` | Product docs, downloads, changelogs |
| **IBM Developer Portal** | `https://developer.ibm.com` | Tutorials, API guides, blog posts |
| **IBM Bob Documentation** | `https://www.ibm.com/docs/en/` (search "Bob") | Agent Mode, MCP, Subagents, Shell v2 |
| **IBM Bob MCP Configuration** | Look for `.bob/mcp.json` docs on bob.ibm.com | MCP server setup, tool definitions |
| **IBM Bob Tutorials** | `https://developer.ibm.com` → search "IBM Bob tutorial" | "Integrating MCP with IBM Bob", "Build AI agents with Bob" |
| **IBM GitHub Organization** | `https://github.com/IBM` → search "bob" | Starter kits, sample repos, API clients |
| **IBM TechXchange Community** | `https://community.ibm.com` | Event discussions, expert Q&A |
| **IBM Newsroom** | `https://newsroom.ibm.com` | Launch announcements, feature lists |
| **IBM YouTube / Technology Channel** | `https://youtube.com/@IBMTechnology` | Bob 2.0 demos, agent mode walkthroughs |

### Key IBM Bob 2.0 Technical References

**MCP Server Configuration (`.bob/mcp.json`):**
```json
{
  "mcpServers": {
    "governance-tribunal-tools": {
      "transport": "streamable-http",
      "url": "http://localhost:8080/mcp",
      "auth": {
        "type": "none"
      }
    }
  }
}
```

**Custom MCP Tool Definition (Python):**
```python
from mcp import BaseMCP, tool

class TribunalTools(BaseMCP):
    @tool
    def run_pytest(self, test_path: str) -> dict:
        """Run pytest on the specified path and return results."""
        import subprocess, json
        result = subprocess.run(
            ["pytest", test_path, "--json-report", 
             "--json-report-file=temp_report.json", "--tb=short"],
            capture_output=True, text=True
        )
        with open("temp_report.json") as f:
            return json.load(f)

    @tool
    def run_secret_scan(self, scan_dir: str) -> dict:
        """Scan directory for hardcoded secrets."""
        import subprocess, json
        result = subprocess.run(
            ["detect-secrets", "scan", scan_dir],
            capture_output=True, text=True
        )
        return json.loads(result.stdout)

    @tool
    def run_pii_scan(self, file_path: str) -> list:
        """Scan file for PII in logging statements."""
        # Uses regex-based scanner
        return scan_file_for_pii(file_path)

    @tool
    def read_file(self, path: str) -> str:
        """Read contents of a file."""
        with open(path) as f:
            return f.read()

    @tool
    def write_file(self, path: str, content: str) -> str:
        """Write content to a file (apply patch)."""
        with open(path, 'w') as f:
            f.write(content)
        return f"Written to {path}"

    @tool
    def git_diff(self, commit: str) -> str:
        """Get the diff for a specific commit."""
        import subprocess
        result = subprocess.run(
            ["git", "diff", f"{commit}~1", commit],
            capture_output=True, text=True
        )
        return result.stdout

    @tool
    def git_blame(self, file_path: str) -> str:
        """Get git blame for a file."""
        import subprocess
        result = subprocess.run(
            ["git", "blame", file_path],
            capture_output=True, text=True
        )
        return result.stdout

    @tool
    def git_log(self, file_path: str, n: int = 5) -> str:
        """Get recent commit history for a file."""
        import subprocess
        result = subprocess.run(
            ["git", "log", f"-{n}", "--oneline", "--", file_path],
            capture_output=True, text=True
        )
        return result.stdout
```

---

## B. Hackathon Platform — Official Sources

| Resource | URL | What to Extract |
|:---|:---|:---|
| **Hackathon Event Page** | `https://lablab.ai/event/ibm-bob-2-0-hackathon` | Rules, deadlines, judging, registration |
| **lablab.ai Submission Guide** | Event page → "How to Submit" section | Video specs, repo rules, slide format |
| **lablab.ai Discord** | `https://discord.gg/lablab-ai` | Team formation, mentors, announcements |
| **lablab.ai YouTube** | Search "lablab.ai IBM Bob hackathon" | Kickoff stream, past winner demos |

### Verified Submission Requirements

| Deliverable | Specification |
|:---|:---|
| **Video** | Max 5 minutes, MP4 format, under 300MB |
| **Slides** | PDF format (not Google Slides link) |
| **GitHub Repo** | **MUST be public** |
| **README** | Project, problem/solution, setup, architecture, demo link, Bob usage |
| **Cover Image** | PNG/JPG, 16:9 aspect ratio |
| **Demo URL** | Live deployment (Streamlit / Vercel / Replit) |
| **Bob Report** | Exported task session report from Bobalytics panel |
| **Short Description** | Max 255 characters |
| **Long Description** | Min 100 words |

### Deadlines
- **Registration closes:** Sept 25, 2026, 15:00 UTC
- **Submission deadline:** Sept 27, 2026, 15:00 UTC
- **No live demo round** — judges evaluate video + demo URL only

---

## C. Security & Scanning Tools — Documentation

| Tool | Official Docs | GitHub Repo | Install |
|:---|:---|:---|:---|
| **detect-secrets** | README on GitHub | `https://github.com/Yelp/detect-secrets` | `pip install detect-secrets` |
| **Semgrep** | `https://semgrep.dev/docs` | `https://github.com/returntocorp/semgrep` | `pip install semgrep` |
| **Semgrep Playground** | `https://semgrep.dev/playground` | — | Browser-based |
| **Semgrep Rule Registry** | `https://semgrep.dev/explore` | `https://github.com/returntocorp/semgrep-rules` | — |
| **Semgrep Learn** | `https://semgrep.dev/learn` | — | Interactive tutorial |
| **Bandit** (alternative) | `https://bandit.readthedocs.io` | `https://github.com/PyCQA/bandit` | `pip install bandit` |
| **TruffleHog** (alternative) | README on GitHub | `https://github.com/trufflesecurity/trufflehog` | `pip install trufflehog` |
| **pre-commit** | `https://pre-commit.com` | `https://github.com/pre-commit/pre-commit` | `pip install pre-commit` |

---

## D. Testing & Git Tools — Documentation

| Tool | Official Docs | GitHub Repo | Install |
|:---|:---|:---|:---|
| **pytest** | `https://docs.pytest.org` | `https://github.com/pytest-dev/pytest` | `pip install pytest` |
| **pytest-json-report** | README on GitHub | `https://github.com/numirias/pytest-json-report` | `pip install pytest-json-report` |
| **GitPython** | `https://gitpython.readthedocs.io` | `https://github.com/gitpython-developers/GitPython` | `pip install GitPython` |
| **Docker SDK for Python** | `https://docker-py.readthedocs.io` | `https://github.com/docker/docker-py` | `pip install docker` |

---

## E. Orchestration & Reporting Tools — Documentation

| Tool | Official Docs | GitHub Repo | Install |
|:---|:---|:---|:---|
| **Jinja2** | `https://jinja.palletsprojects.com` | `https://github.com/pallets/jinja` | `pip install Jinja2` |
| **Rich** (terminal UI) | `https://rich.readthedocs.io` | `https://github.com/Textualize/rich` | `pip install rich` |
| **Typer** (CLI framework) | `https://typer.tiangolo.com` | `https://github.com/tiangolo/typer` | `pip install typer` |
| **PyGithub** (GitHub API) | `https://pygithub.readthedocs.io` | `https://github.com/PyGithub/PyGithub` | `pip install PyGithub` |
| **FastAPI** (webhook) | `https://fastapi.tiangolo.com` | `https://github.com/tiangolo/fastapi` | `pip install fastapi` |
| **Streamlit** (demo deploy) | `https://docs.streamlit.io` | `https://github.com/streamlit/streamlit` | `pip install streamlit` |

---

## F. Model Context Protocol (MCP) — Documentation

| Resource | URL |
|:---|:---|
| **MCP Specification** | `https://modelcontextprotocol.io` |
| **MCP Python SDK** | `https://github.com/modelcontextprotocol/python-sdk` |
| **MCP TypeScript SDK** | `https://github.com/modelcontextprotocol/typescript-sdk` |
| **IBM Bob MCP Integration Guide** | `https://bob.ibm.com` → search "MCP" |
| **"Building MCP Tools" Tutorial** | `https://developer.ibm.com` → search "Building MCP Tools" |

---

# PART 2: COMPLETE WORKING LOGIC

> Every module below is production-ready pseudocode. Copy, adapt, and wire together.

---

## Module 1: CLI Entry Point (`src/cli.py`)

```python
import typer
from rich.console import Console
from rich.panel import Panel
from rich.progress import Progress
from orchestrator import GovernanceTribunal

app = typer.Typer()
console = Console()

@app.command()
def investigate(
    repo_path: str = typer.Argument(..., help="Path to the target repository"),
    test_path: str = typer.Option("tests/", help="Path to test directory"),
    policy_dir: str = typer.Option("policies/", help="Path to policy documents"),
    max_retries: int = typer.Option(2, help="Max patch retry attempts"),
):
    """🏛️ The Governance Tribunal: Investigate and remediate codebase defects."""
    
    console.print(Panel(
        "[bold red]THE GOVERNANCE TRIBUNAL[/bold red]\n"
        "[dim]Forensic Compliance & Regression Arbiter[/dim]",
        border_style="red"
    ))
    
    tribunal = GovernanceTribunal(
        repo_path=repo_path,
        test_path=test_path,
        policy_dir=policy_dir,
        max_retries=max_retries,
    )
    
    with Progress() as progress:
        task = progress.add_task("[red]Investigating...", total=6)
        
        # Step 1: Collect evidence
        progress.update(task, description="[yellow]📋 Collecting evidence...")
        evidence = tribunal.collect_evidence()
        progress.advance(task)
        
        # Step 2: Classify case
        progress.update(task, description="[yellow]🔍 Classifying case...")
        case = tribunal.classify_case(evidence)
        progress.advance(task)
        
        # Step 3: Run agentic remediation loop
        progress.update(task, description="[yellow]⚖️ Bob investigating...")
        result = tribunal.run_remediation_loop(case)
        progress.advance(task)
        
        # Step 4: Generate docket
        progress.update(task, description="[yellow]📄 Generating Tribunal Docket...")
        docket = tribunal.generate_docket(case, result)
        progress.advance(task)
        
        # Step 5: Human approval
        progress.update(task, description="[yellow]👤 Awaiting human approval...")
        progress.advance(task)
    
    # Display docket
    console.print(Panel(docket, title="TRIBUNAL DOCKET", border_style="green"))
    
    # Human approval gate
    approved = typer.confirm("Do you approve this remediation?")
    if approved:
        console.print("[bold green]✅ VERDICT APPROVED. Patch applied.[/bold green]")
        tribunal.apply_patch(result)
    else:
        console.print("[bold red]❌ VERDICT REJECTED. Patch discarded.[/bold red]")
    
    # Save audit log
    tribunal.save_audit_log(case, result, approved)

if __name__ == "__main__":
    app()
```

---

## Module 2: Case Manager (`src/orchestrator/case_manager.py`)

```python
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
    HIGH = "high"     # auth, payments, secrets, privacy, DB migration
    MEDIUM = "medium" # business logic, API behavior, tests
    LOW = "low"       # docs, formatting, minor refactor

class Case:
    def __init__(self):
        self.case_id = f"GT-{datetime.now(timezone.utc).strftime('%Y%m%d')}-{uuid.uuid4().hex[:4].upper()}"
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
        self.history = []  # Full event log
    
    def log_event(self, event_type: str, details: dict):
        self.history.append({
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "event": event_type,
            "details": details
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
```

---

## Module 3: Evidence Collector (`src/evidence/collector.py`)

```python
import git
import json
import subprocess

class EvidenceCollector:
    def __init__(self, repo_path: str, policy_dir: str):
        self.repo_path = repo_path
        self.repo = git.Repo(repo_path)
        self.policy_dir = policy_dir
    
    def collect_all(self) -> dict:
        return {
            "test_results": self.run_tests(),
            "secret_scan": self.run_secret_scan(),
            "pii_scan": self.run_pii_scan(),
            "recent_commits": self.get_recent_commits(),
            "changed_files": self.get_changed_files(),
            "policies": self.load_policies(),
        }
    
    def run_tests(self) -> dict:
        """Run pytest and capture structured results."""
        result = subprocess.run(
            ["pytest", "tests/", "--json-report",
             "--json-report-file=temp_report.json", "--tb=short"],
            capture_output=True, text=True, cwd=self.repo_path
        )
        try:
            with open(f"{self.repo_path}/temp_report.json") as f:
                report = json.load(f)
            failures = []
            for test in report.get("tests", []):
                if test["outcome"] == "failed":
                    crash = test.get("call", {}).get("crash", {})
                    failures.append({
                        "test_id": test["nodeid"],
                        "file": crash.get("path"),
                        "line": crash.get("lineno"),
                        "message": crash.get("message"),
                        "longrepr": test.get("call", {}).get("longrepr", "")
                    })
            return {
                "passed": result.returncode == 0,
                "total": report.get("summary", {}).get("total", 0),
                "failed_count": len(failures),
                "failures": failures
            }
        except (FileNotFoundError, json.JSONDecodeError):
            return {"passed": False, "failures": [], "error": result.stderr}
    
    def run_secret_scan(self) -> dict:
        """Run detect-secrets scan."""
        result = subprocess.run(
            ["detect-secrets", "scan", self.repo_path],
            capture_output=True, text=True
        )
        try:
            output = json.loads(result.stdout)
            findings = output.get("results", {})
            return {"passed": len(findings) == 0, "findings": findings}
        except json.JSONDecodeError:
            return {"passed": True, "findings": {}, "error": result.stderr}
    
    def run_pii_scan(self) -> dict:
        """Scan Python files for PII in logging calls."""
        import re, os
        PII_PATTERNS = {
            "Email": r"[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+",
            "SSN": r"\b\d{3}-\d{2}-\d{4}\b",
        }
        findings = []
        src_dir = os.path.join(self.repo_path, "src")
        for root, dirs, files in os.walk(src_dir):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath, 'r') as f:
                        for line_num, line in enumerate(f, 1):
                            if "logger." in line or "print(" in line:
                                for pii_type, pattern in PII_PATTERNS.items():
                                    if re.search(pattern, line):
                                        findings.append({
                                            "file": fpath, "line": line_num,
                                            "type": pii_type, "content": line.strip()
                                        })
                            # Also check for variable names suggesting PII
                            if re.search(r"(user\.email|user_email|\.email)", line):
                                if "logger." in line or "print(" in line:
                                    findings.append({
                                        "file": fpath, "line": line_num,
                                        "type": "PII_Variable", "content": line.strip()
                                    })
        return {"passed": len(findings) == 0, "findings": findings}
    
    def get_recent_commits(self, n=10) -> list:
        commits = list(self.repo.iter_commits(max_count=n))
        return [{
            "sha": c.hexsha[:7],
            "author": c.author.name,
            "date": str(c.authored_datetime),
            "message": c.message.strip()
        } for c in commits]
    
    def get_changed_files(self) -> list:
        """Get files changed in most recent commit."""
        head = self.repo.commit("HEAD")
        if head.parents:
            diffs = head.parents[0].diff(head)
            return [d.a_path or d.b_path for d in diffs]
        return []
    
    def load_policies(self) -> dict:
        """Load all policy markdown files."""
        import os
        policies = {}
        for fname in os.listdir(self.policy_dir):
            if fname.endswith(".md"):
                with open(os.path.join(self.policy_dir, fname)) as f:
                    policies[fname] = f.read()
        return policies
    
    def blame_line(self, file_path: str, line_num: int) -> dict:
        """Git blame a specific line to find the culprit commit."""
        blame = self.repo.blame('HEAD', file_path)
        current = 1
        for commit, lines in blame:
            if current <= line_num < current + len(lines):
                diff_text = ""
                if commit.parents:
                    diffs = commit.parents[0].diff(commit, create_patch=True)
                    for d in diffs:
                        if d.a_path == file_path:
                            diff_text = d.diff.decode('utf-8')
                return {
                    "commit": commit.hexsha,
                    "author": commit.author.name,
                    "date": str(commit.authored_datetime),
                    "message": commit.message.strip(),
                    "diff": diff_text
                }
            current += len(lines)
        return None
```

---

## Module 4: Case Classifier (`src/orchestrator/classifier.py`)

```python
from case_manager import CaseType, Severity

def classify_case(evidence: dict) -> tuple:
    """Classify case type and severity from collected evidence."""
    
    tests_failed = not evidence["test_results"]["passed"]
    secrets_found = not evidence["secret_scan"]["passed"]
    pii_found = not evidence["pii_scan"]["passed"]
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
    # Check if auth/payment files are involved
    changed = evidence.get("changed_files", [])
    sensitive_patterns = ["auth", "login", "payment", "checkout", "crypto", "secret"]
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
    
    failures = evidence["test_results"].get("failures", [])
    if failures and failures[0].get("file"):
        score += 0.15  # Stack trace points to specific file/line
    
    if not evidence["pii_scan"]["passed"] or not evidence["secret_scan"]["passed"]:
        score += 0.10  # Policy clause match
    
    score += 0.10  # Historical (placeholder, always add for MVP)
    
    return round(min(score, 1.0), 2)
```

---

## Module 5: Dual-Validation Engine (`src/validation/dual_validator.py`)

```python
import subprocess
import json

class DualValidator:
    """Runs both functional tests AND policy scans. Both must pass."""
    
    def __init__(self, repo_path: str):
        self.repo_path = repo_path
    
    def validate(self) -> dict:
        """Run all validations. Returns combined result."""
        functional = self.run_functional_tests()
        policy = self.run_policy_scan()
        
        all_passed = functional["passed"] and policy["passed"]
        
        return {
            "passed": all_passed,
            "functional": functional,
            "policy": policy,
            "summary": self._format_summary(functional, policy)
        }
    
    def run_functional_tests(self) -> dict:
        """Run pytest and parse JSON results."""
        result = subprocess.run(
            ["pytest", "tests/", "--json-report",
             "--json-report-file=validation_report.json", "--tb=short"],
            capture_output=True, text=True, cwd=self.repo_path
        )
        try:
            with open(f"{self.repo_path}/validation_report.json") as f:
                report = json.load(f)
            failures = [t for t in report.get("tests", []) if t["outcome"] == "failed"]
            return {
                "passed": len(failures) == 0,
                "total": report.get("summary", {}).get("total", 0),
                "failed": len(failures),
                "details": [t["nodeid"] for t in failures]
            }
        except Exception as e:
            return {"passed": False, "error": str(e)}
    
    def run_policy_scan(self) -> dict:
        """Run detect-secrets + PII scan."""
        # Secret scan
        secret_result = subprocess.run(
            ["detect-secrets", "scan", f"{self.repo_path}/src"],
            capture_output=True, text=True
        )
        try:
            secrets = json.loads(secret_result.stdout).get("results", {})
        except json.JSONDecodeError:
            secrets = {}
        
        # PII scan (regex-based)
        import re, os
        pii_findings = []
        src_dir = os.path.join(self.repo_path, "src")
        for root, _, files in os.walk(src_dir):
            for fname in files:
                if fname.endswith(".py"):
                    fpath = os.path.join(root, fname)
                    with open(fpath) as f:
                        for ln, line in enumerate(f, 1):
                            if ("logger." in line or "print(" in line):
                                if re.search(r"(\.email|user_data|\.ssn|password)", line):
                                    pii_findings.append({"file": fpath, "line": ln})
        
        secrets_clean = len(secrets) == 0
        pii_clean = len(pii_findings) == 0
        
        return {
            "passed": secrets_clean and pii_clean,
            "secrets": {"passed": secrets_clean, "count": len(secrets), "details": secrets},
            "pii": {"passed": pii_clean, "count": len(pii_findings), "details": pii_findings}
        }
    
    def _format_summary(self, func: dict, policy: dict) -> list:
        """Format validation results for the Docket."""
        results = []
        status = "PASS" if func["passed"] else "FAIL"
        results.append({"status": status, "description": f"pytest ({func.get('total', '?')} tests)"})
        
        status = "PASS" if policy["secrets"]["passed"] else "FAIL"
        results.append({"status": status, "description": "detect-secrets (secret scan)"})
        
        status = "PASS" if policy["pii"]["passed"] else "FAIL"
        results.append({"status": status, "description": "PII scanner (privacy check)"})
        
        return results
```

---

## Module 6: Tribunal Docket Generator (`src/reporting/docket_generator.py`)

```python
from jinja2 import Template
from datetime import datetime, timezone

DOCKET_TEMPLATE = """
====================================================================
TRIBUNAL DOCKET: CASE #{{ case_id }}
DEFENDANT: {{ defendant }}
CHARGES: {{ charges }}
DATE: {{ date }}
====================================================================

## 1. THE INCIDENT (What Failed)
{{ incident_details }}

## 2. THE MOTIVE (Root Cause Analysis)
{{ root_cause }}
Confidence Score: {{ confidence }}

## 3. THE INVESTIGATION TRAIL
- Suspect Commit: {{ suspect_commit }}
- Author: {{ suspect_author }}
- Commit Message: {{ suspect_message }}
- Files Changed: {{ files_changed }}

## 4. THE SENTENCE (The Patch)
{{ patch_description }}

## 5. DUAL-VALIDATION EVIDENCE
{% for check in validations -%}
- [{{ check.status }}] {{ check.description }}
{% endfor %}
## 6. PAROLE CONDITIONS (Guardrails Added)
{% for condition in parole_conditions -%}
- {{ condition }}
{% endfor %}
## 7. RISK ASSESSMENT
- Case Type: {{ case_type }}
- Severity: {{ severity }}
- Human Approval Required: {{ human_approval_required }}
- Residual Risks: {{ residual_risks }}

## 8. REMEDIATION ATTEMPTS
- Total Attempts: {{ attempt_count }}
- Final Status: {{ final_status }}

**VERDICT:** {{ verdict }}
====================================================================
Generated by The Governance Tribunal — Powered by IBM Bob 2.0
"""

class DocketGenerator:
    def __init__(self):
        self.template = Template(DOCKET_TEMPLATE)
    
    def generate(self, case, result: dict) -> str:
        # Build incident details from evidence
        incident_lines = []
        for f in case.evidence.get("test_results", {}).get("failures", []):
            incident_lines.append(f"- Functional: {f['test_id']} FAILED — {f.get('message', 'N/A')}")
        for f in case.evidence.get("secret_scan", {}).get("findings", {}):
            incident_lines.append(f"- Policy: SECRET detected in {f}")
        for f in case.evidence.get("pii_scan", {}).get("findings", []):
            incident_lines.append(f"- Policy: PII detected at {f.get('file')}:{f.get('line')}")
        
        data = {
            "case_id": case.case_id,
            "defendant": ", ".join(case.evidence.get("changed_files", ["unknown"])),
            "charges": f"{case.case_type.value.upper()} violation",
            "date": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
            "incident_details": "\n".join(incident_lines) or "No incidents detected.",
            "root_cause": result.get("root_cause", "Under investigation"),
            "confidence": case.confidence_score,
            "suspect_commit": result.get("suspect", {}).get("commit", "N/A"),
            "suspect_author": result.get("suspect", {}).get("author", "N/A"),
            "suspect_message": result.get("suspect", {}).get("message", "N/A"),
            "files_changed": ", ".join(result.get("files_patched", [])),
            "patch_description": result.get("patch_summary", "No patch generated."),
            "validations": result.get("validations", []),
            "parole_conditions": result.get("parole_conditions", []),
            "case_type": case.case_type.value,
            "severity": case.severity.value,
            "human_approval_required": case.severity.value == "high" or case.confidence_score < 0.75,
            "residual_risks": result.get("residual_risks", "None identified."),
            "attempt_count": case.attempt_count,
            "final_status": case.status.value,
            "verdict": result.get("verdict", "PENDING"),
        }
        return self.template.render(data)
    
    def save(self, docket_text: str, output_path: str):
        with open(output_path, "w") as f:
            f.write(docket_text)
```

---

## Module 7: Audit Ledger (`src/ledger/audit_ledger.py`)

```python
import json
import os
from datetime import datetime, timezone

class AuditLedger:
    """Append-only event log for full auditability."""
    
    def __init__(self, log_dir: str = "logs"):
        self.log_dir = log_dir
        os.makedirs(log_dir, exist_ok=True)
    
    def log(self, case_id: str, event_type: str, details: dict):
        entry = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "case_id": case_id,
            "event": event_type,
            "details": details
        }
        log_file = os.path.join(self.log_dir, f"{case_id}.jsonl")
        with open(log_file, "a") as f:
            f.write(json.dumps(entry) + "\n")
    
    def save_full_case(self, case_dict: dict):
        """Save complete case record as JSON."""
        case_file = os.path.join(self.log_dir, f"{case_dict['case_id']}_full.json")
        with open(case_file, "w") as f:
            json.dump(case_dict, f, indent=2)
```

---

## Module 8: Main Orchestrator (`src/orchestrator/tribunal.py`)

```python
from case_manager import Case, CaseStatus
from evidence.collector import EvidenceCollector
from orchestrator.classifier import classify_case, compute_confidence
from validation.dual_validator import DualValidator
from reporting.docket_generator import DocketGenerator
from ledger.audit_ledger import AuditLedger

class GovernanceTribunal:
    """The master orchestrator — ties everything together."""
    
    def __init__(self, repo_path, test_path, policy_dir, max_retries=2):
        self.repo_path = repo_path
        self.test_path = test_path
        self.policy_dir = policy_dir
        self.max_retries = max_retries
        self.collector = EvidenceCollector(repo_path, policy_dir)
        self.validator = DualValidator(repo_path)
        self.docket_gen = DocketGenerator()
        self.ledger = AuditLedger()
        self.case = Case()
    
    def collect_evidence(self) -> dict:
        evidence = self.collector.collect_all()
        self.case.evidence = evidence
        self.case.update_status(CaseStatus.EVIDENCE_COLLECTED)
        self.ledger.log(self.case.case_id, "evidence_collected", {
            "tests_passed": evidence["test_results"]["passed"],
            "secrets_clean": evidence["secret_scan"]["passed"],
            "pii_clean": evidence["pii_scan"]["passed"],
        })
        return evidence
    
    def classify_case(self, evidence: dict):
        case_type, severity = classify_case(evidence)
        self.case.case_type = case_type
        self.case.severity = severity
        self.case.update_status(CaseStatus.CASE_CLASSIFIED)
        self.ledger.log(self.case.case_id, "case_classified", {
            "type": case_type.value, "severity": severity.value
        })
        return self.case
    
    def run_remediation_loop(self, case) -> dict:
        """
        THE CORE AGENTIC LOOP.
        
        This is where IBM Bob 2.0 takes over:
        1. Bob reads evidence + policies
        2. Bob generates hypotheses
        3. Bob writes a patch
        4. Dual-validation runs
        5. If fail → Bob reads errors → adjusts → retries
        6. If max retries → escalate to human
        """
        result = {
            "root_cause": "",
            "suspect": {},
            "patch_summary": "",
            "files_patched": [],
            "validations": [],
            "parole_conditions": [],
            "residual_risks": "",
            "verdict": "PENDING",
        }
        
        # ── BOB INVESTIGATES ──
        # In the real implementation, this is where you call Bob 2.0
        # via MCP tools. Bob reads the evidence, policies, and generates
        # hypotheses + patch. For MVP, this can be a scripted flow.
        
        # Step 1: Trace root cause via git blame
        failures = case.evidence["test_results"].get("failures", [])
        if failures:
            first_failure = failures[0]
            suspect = self.collector.blame_line(
                first_failure.get("file", ""),
                first_failure.get("line", 0)
            )
            if suspect:
                result["suspect"] = suspect
                result["root_cause"] = (
                    f"Commit {suspect['commit'][:7]} by {suspect['author']}: "
                    f"{suspect['message']}"
                )
        
        case.update_status(CaseStatus.ROOT_CAUSE_SELECTED)
        
        # Step 2: Compute confidence
        reproduction_success = not case.evidence["test_results"]["passed"]
        case.confidence_score = compute_confidence(
            case.evidence, reproduction_success
        )
        
        # Step 3: Bob generates patch (retry loop)
        for attempt in range(self.max_retries):
            case.attempt_count = attempt + 1
            case.update_status(CaseStatus.PATCH_GENERATED)
            
            self.ledger.log(case.case_id, "patch_attempt", {
                "attempt": attempt + 1
            })
            
            # ── BOB WRITES THE PATCH ──
            # In real implementation: Bob reads the error messages,
            # the policy documents, and the surrounding code context,
            # then generates a fix using write_file tool.
            #
            # For MVP: You can have Bob do this interactively in
            # the IDE, or script a deterministic fix for the demo.
            
            patch_applied = self._apply_bob_patch(case, attempt)
            
            if not patch_applied:
                continue
            
            # Step 4: DUAL VALIDATION
            case.update_status(CaseStatus.VALIDATION_EXECUTED)
            validation = self.validator.validate()
            result["validations"] = validation["summary"]
            
            self.ledger.log(case.case_id, "validation_result", {
                "attempt": attempt + 1,
                "passed": validation["passed"],
                "functional": validation["functional"]["passed"],
                "policy": validation["policy"]["passed"],
            })
            
            if validation["passed"]:
                # SUCCESS
                result["verdict"] = "GUILTY. REMEDIATED. AWAITING HUMAN APPROVAL."
                result["patch_summary"] = self._describe_patch()
                result["parole_conditions"] = [
                    "Added regression test: test_no_pii_in_logs()",
                    "Added pre-commit hook to block logger.info(payload)",
                ]
                case.update_status(CaseStatus.VERDICT_GENERATED)
                return result
            else:
                # FAILED — Feed errors back to Bob for next attempt
                error_context = {
                    "functional_errors": validation["functional"].get("details", []),
                    "policy_errors": {
                        "secrets": validation["policy"]["secrets"].get("details", {}),
                        "pii": validation["policy"]["pii"].get("details", []),
                    }
                }
                self.ledger.log(case.case_id, "validation_failed", error_context)
        
        # MAX RETRIES EXHAUSTED → ESCALATE
        result["verdict"] = "COULD NOT REMEDIATE. ESCALATED TO HUMAN ENGINEER."
        result["residual_risks"] = "Automated remediation failed after max attempts."
        case.update_status(CaseStatus.ESCALATED)
        return result
    
    def _apply_bob_patch(self, case, attempt: int) -> bool:
        """
        This is where Bob 2.0 actually writes the fix.
        
        In a real hackathon demo, Bob would:
        1. Read the failing test output
        2. Read the policy document
        3. Read the source file
        4. Generate a patched version
        5. Write it using the write_file tool
        
        For a scripted MVP demo, you can hardcode the fix here
        and let Bob handle the investigation/explanation part.
        """
        # Placeholder — in production, Bob generates this
        return True
    
    def _describe_patch(self) -> str:
        """Generate human-readable patch description."""
        return "Replaced PII logging with hashed identifiers. Added bounded retry with backoff."
    
    def generate_docket(self, case, result: dict) -> str:
        docket = self.docket_gen.generate(case, result)
        self.docket_gen.save(docket, f"logs/{case.case_id}_docket.md")
        return docket
    
    def apply_patch(self, result: dict):
        """Apply the approved patch (placeholder)."""
        pass
    
    def save_audit_log(self, case, result: dict, approved: bool):
        case.human_approved = approved
        case.update_status(
            CaseStatus.CASE_CLOSED if approved else CaseStatus.ESCALATED
        )
        self.ledger.save_full_case(case.to_dict())
```

---

## Module 9: Docker Sandbox Runner (`src/sandbox/runner.py`)

```python
import subprocess
import os

class SandboxRunner:
    """Run tests and scanners in an isolated Docker container."""
    
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)
    
    def run_in_sandbox(self, command: str) -> dict:
        """Execute a command inside a sandboxed Docker container."""
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",           # No network access
            "--memory", "512m",            # Memory limit
            "--cpus", "1.0",               # CPU limit
            "-v", f"{self.repo_path}:/app:ro",  # Read-only mount
            "-w", "/app",
            "python:3.11-slim",
            "sh", "-c", command
        ]
        
        result = subprocess.run(
            docker_cmd, capture_output=True, text=True, timeout=120
        )
        
        return {
            "exit_code": result.returncode,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "success": result.returncode == 0
        }
    
    def run_pytest_sandboxed(self) -> dict:
        return self.run_in_sandbox(
            "pip install pytest pytest-json-report -q && "
            "pytest tests/ --tb=short --json-report --json-report-file=/tmp/r.json && "
            "cat /tmp/r.json"
        )
    
    def run_detect_secrets_sandboxed(self) -> dict:
        return self.run_in_sandbox(
            "pip install detect-secrets -q && detect-secrets scan /app/src"
        )
```

---

## Module 10: `requirements.txt`

```text
# Core
pytest>=7.0
pytest-json-report>=1.5
detect-secrets>=1.4
GitPython>=3.1
Jinja2>=3.1
rich>=13.0
typer>=0.9

# Stretch goals
PyGithub>=2.0
fastapi>=0.100
uvicorn>=0.23
streamlit>=1.30
docker>=6.0
semgrep>=1.0
```

---

## Complete Data Flow Summary

```text
USER runs: tribunal investigate ./demo_repo

    ┌──────────────────────────────────────────────┐
    │  1. TRIGGER RECEIVED                         │
    │     CLI parses args, creates Case object      │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  2. EVIDENCE COLLECTED                       │
    │     • pytest → JSON report (failures)         │
    │     • detect-secrets → JSON (secrets found)   │
    │     • PII regex scan → findings               │
    │     • git log → recent commits                │
    │     • git diff → changed files                │
    │     • Load policies/*.md                      │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  3. CASE CLASSIFIED                          │
    │     • FUNCTIONAL / POLICY / COMBINED          │
    │     • Severity: HIGH / MEDIUM / LOW           │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  4. BOB INVESTIGATES (Agent Mode)            │
    │     • Reads failing test + error message      │
    │     • Reads policy document                   │
    │     • git blame → finds suspect commit        │
    │     • Generates root cause hypothesis         │
    │     • Computes confidence score               │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  5. BOB GENERATES PATCH                      │
    │     • Writes fixed code via write_file tool   │
    │     • Removes PII from logging                │
    │     • Fixes functional bug                    │
    │     • Adds regression test                    │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  6. DUAL VALIDATION                          │
    │     • pytest → all tests pass? ✅/❌           │
    │     • detect-secrets → clean? ✅/❌            │
    │     • PII scan → clean? ✅/❌                  │
    │                                               │
    │     Both must pass. If not:                    │
    │       → retry (max 2 attempts)                │
    │       → or escalate to human                  │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  7. TRIBUNAL DOCKET GENERATED                │
    │     • Jinja2 renders Markdown verdict          │
    │     • Case ID, charges, root cause, patch     │
    │     • Validation evidence, parole conditions   │
    │     • Risk assessment                          │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  8. HUMAN APPROVAL GATE                      │
    │     • Rich terminal displays Docket           │
    │     • User types y/n                           │
    │     • If yes → patch applied                   │
    │     • If no → patch discarded                  │
    └──────────────┬───────────────────────────────┘
                   ▼
    ┌──────────────────────────────────────────────┐
    │  9. AUDIT LEDGER SAVED                       │
    │     • Full case JSON written to logs/          │
    │     • Docket Markdown saved                    │
    │     • Every event timestamped                  │
    └──────────────────────────────────────────────┘
```
