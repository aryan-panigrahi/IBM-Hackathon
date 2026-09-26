# 🏛️ The Governance Tribunal (Forensic Compliance & Regression Arbiter)

![The Governance Tribunal Cover](assets/cover.png)

> **IBM Bob 2.0 Hackathon Submission** 
> *A paradigm shift in codebase integrity: Treating functional bugs and policy violations as the exact same class of forensic problem.*

## 📖 One-Sentence Pitch
An agentic forensic engine where IBM Bob 2.0 investigates CI failures and policy violations, traces the root cause, generates compliant remediation patches, validates them against both test suites and governance rules, and issues an auditable **"Tribunal Docket."**

---

## 🚀 The Problem We're Solving

Current CI/CD pipelines are fractured:
1. **Tests** run in one silo (functional regressions).
2. **Security Scanners** (detect-secrets, Semgrep, checkov) run in another (policy violations).
3. **Developers** are stuck in the middle, manually piecing together tracebacks, git blame, and policy docs to figure out how to fix the mess.

When a developer rushes to fix a failing test, they often accidentally introduce a security vulnerability (e.g., logging a payload to figure out why it crashed, thereby leaking PII).

## 💡 The Solution: The Governance Tribunal

We built an orchestrator that treats **Codebase Defects** holistically.

By connecting **IBM Bob 2.0** (Agent Mode) to our `Dual-Validation Engine`, Bob isn't just fixing bugs—Bob is acting as a Forensic Investigator and Compliance Arbiter. 

When a trigger fires, The Tribunal:
1. **Collects Evidence:** Grabs test failures, detects secrets, scans for PII leaks, and pulls the `git blame` for the suspect commit.
2. **Generates a Hypothesis:** Uses Agent Mode reasoning to determine *why* the defect occurred.
3. **Sentences (Patches):** Bob writes a remediation patch.
4. **The Appeals Process (Dual Validation):** The patch is run against *both* the test suite AND the policy scanners. If it fixes the bug but leaks PII, the patch is rejected, and Bob tries again.
5. **The Verdict:** Outputs a stunning, Markdown-formatted **Tribunal Docket** for human approval, complete with a confidence score and audit trail.

---

## 🛠️ Architecture & Tech Stack

- **Core Reasoning Engine:** IBM Bob 2.0 Agent Mode (Granite 34B)
- **Tool Integration:** Model Context Protocol (MCP) Server defining `write_file`, `git_blame`, `run_tests`, and `run_scanners`.
- **Orchestration:** Python (State Machine pattern)
- **Scanners:** `pytest` (with JSON reporting), `detect-secrets`, custom Regex PII engine
- **CLI Framework:** `Typer` + `Rich` (for that beautiful courtroom aesthetic)
- **Reporting:** `Jinja2` (Docket generation)

---

## 🧠 How We Used IBM Bob 2.0

We built a custom MCP server (`mcp_server/tribunal_mcp_server.py`) registered in `.bob/mcp.json`.
Instead of just autocomplete, we use **Agent Mode** to give Bob full autonomy over a sandboxed forensic environment.

### MCP Tools Exposed to Bob

| Tool | Description |
|---|---|
| `git_blame` | Trace a file/line to the responsible commit, author, and diff |
| `run_tests` | Execute the pytest suite; returns structured pass/fail + stack traces |
| `run_scanners` | Run `detect-secrets` + PII regex scanner; returns combined findings |
| `write_file` | Write a remediation patch into the repo (sandboxed to the target path) |

### Bob's Agentic Investigation Loop

1. **Document Understanding:** Bob reads `policies/privacy-policy.md` to understand *why* logging an email is illegal.
2. **Multi-step Reasoning:** Bob receives the JSON test failure, calls `git_blame` to find the culprit commit, reads the source file, and formulates a fix.
3. **Self-Correction:** Bob calls `run_tests` + `run_scanners` after each patch. If the patch passes tests but leaks PII, Bob reads the scanner output and self-corrects — the **Dual-Validation Engine** is Bob's adversary.
4. **Patch Application:** Bob calls `write_file` to apply the fix directly to the sandboxed repo.

### Installing the MCP Server

```bash
# Install dependencies (includes the MCP Python SDK)
pip install -r requirements.txt

# The MCP server is auto-registered via .bob/mcp.json
# Bob hot-reloads it when you open this workspace folder.
```

The `.bob/mcp.json` at the workspace root registers the server with a single entry:

```json
{
  "mcpServers": {
    "governance-tribunal": {
      "command": "python3",
      "args": ["${workspaceFolder}/governance-tribunal/mcp_server/tribunal_mcp_server.py"]
    }
  }
}
```

---

## 💻 Running the Demo Locally

We have provided a `demo_repo` with 4 intentional defects:
- An unbounded retry loop (Hangs forever)
- A hardcoded AWS Secret
- A PII Leak (`logger.info(user.email)`)
- **The Combined Defect:** A function that fixes the retry loop but introduces a new PII leak.

### Installation

```bash
# 1. Clone the repository
git clone https://github.com/yourusername/governance-tribunal.git
cd governance-tribunal

# 2. Set up virtual environment
python -m venv venv
source venv/bin/activate  # Or `.\venv\Scripts\activate` on Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Initialize the demo repo (to track git blame)
cd demo_repo
git init && git add -A && git commit -m "Initial buggy commit"
cd ..
```

### Run the Investigation

```bash
# Summon The Governance Tribunal
python cli.py investigate ./demo_repo --max-retries 3
```

Watch as the Rich terminal UI collects evidence, classifies the case severity, runs Bob's remediation loop, and finally presents you with the **Tribunal Docket** for approval.

---

## 🛡️ Responsible AI & Governance

AI shouldn't deploy code blindly. The Tribunal implements strict guardrails:
- **Human Approval Gate:** Any defect touching sensitive files (auth, payments) or scoring < 0.75 confidence requires explicit human Y/N approval.
- **Append-Only Audit Ledger:** Every state transition, hypothesis, and patch attempt is logged to `logs/case_id.jsonl` for compliance teams.
- **Prompt Injection Defense:** Untrusted code strings are strictly typed and wrapped when passed to the Agent prompt.

*(Read our full Responsible AI manifesto in `docs/responsible-ai.md`)*

---

*Built with ❤️ for the IBM Bob 2.0 Hackathon (Sept 2026).*
