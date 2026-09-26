# ⚖️ The Governance Tribunal
### IBM Bob 2.0 Hackathon — Forensic Compliance & Regression Arbiter

> Treating functional bugs and policy violations as the **exact same class of forensic problem** — investigated, patched, and validated by IBM Bob 2.0 in a single agentic loop.

---

## What It Does

Most CI/CD pipelines run tests in one silo and security scanners in another. Developers are left manually cross-referencing pytest tracebacks, `git blame` output, and policy documentation to figure out what broke and whether the fix is safe. When they rush, they introduce new violations (e.g. logging an email to debug a crash).

**The Governance Tribunal collapses all of that into a single agentic loop:**

1. **Collects Evidence** — runs pytest, `detect-secrets`, a PII regex scanner, and `git blame` on the target repo.
2. **Classifies the Case** — determines whether the defect is Functional, Policy, or Combined, and assigns a severity.
3. **Generates Hypotheses** — correlates git history with failures to identify the culprit commit.
4. **Bob Patches** — IBM Bob 2.0 (via MCP tools) reads the failures and policies, then writes a fix.
5. **Dual Validates** — the patch must pass **both** the test suite and all policy scanners before being accepted. If either fails, Bob self-corrects and retries.
6. **Issues a Tribunal Docket** — a structured Markdown verdict report with charges, evidence, patch summary, and audit trail.
7. **Human Approval Gate** — high-severity or low-confidence fixes require explicit Y/N sign-off before any code is merged.

---

## Project Structure

```
IBM Hackathon/
│
├── .bob/
│   └── mcp.json                        ← Registers the Tribunal MCP server with Bob
│
└── governance-tribunal/
    ├── cli.py                          ← CLI entry point  (python cli.py investigate ./demo_repo)
    ├── requirements.txt
    ├── .env.example
    │
    ├── mcp_server/
    │   └── tribunal_mcp_server.py      ← MCP server exposing 4 tools to Bob (stdio transport)
    │
    ├── src/
    │   ├── orchestrator/
    │   │   ├── tribunal.py             ← Master orchestrator — GovernanceTribunal class
    │   │   ├── case_manager.py         ← Case state machine & data model (10 states)
    │   │   └── classifier.py           ← Case type, severity & confidence scoring
    │   ├── evidence/
    │   │   └── collector.py            ← pytest runner, detect-secrets, PII scan, git blame
    │   ├── validation/
    │   │   └── dual_validator.py       ← Dual-validation engine (tests AND policy must pass)
    │   ├── reporting/
    │   │   └── docket_generator.py     ← Jinja2 Tribunal Docket renderer
    │   └── ledger/
    │       └── audit_ledger.py         ← Append-only JSONL audit log
    │
    ├── demo_repo/                      ← Intentionally defective target repository
    │   ├── src/
    │   │   ├── auth/login.py           ← DEFECT 2: PII leak — logs user.email in plain text
    │   │   ├── checkout/service.py     ← DEFECT 1: unbounded retry loop  |  DEFECT 4: PII in retry
    │   │   └── config.py              ← DEFECT 3: hardcoded AWS credentials
    │   └── tests/
    │       ├── test_login.py
    │       └── test_checkout.py        ← test_checkout_timeout() will FAIL (hangs forever)
    │
    ├── policies/
    │   ├── privacy-policy.md           ← Bob reads this to understand why PII logging is illegal
    │   └── security-policy.md
    │
    ├── templates/
    │   └── docket_template.md          ← Jinja2 template for the Tribunal Docket
    │
    └── logs/                           ← Auto-generated audit logs (gitignored)
```

---

## Quick Start

### 1. Install Dependencies

```bash
cd "governance-tribunal"
python3 -m venv venv
source venv/bin/activate        # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
```

### 2. Set Up the Demo Repo

The demo repo needs at least one git commit so `git blame` has history to trace:

```bash
cd demo_repo
git init && git add -A && git commit -m "Initial buggy commit"
cd ..
```

### 3. Run the Investigation

```bash
python cli.py investigate ./demo_repo --max-retries 3
```

You'll see the Tribunal work through each phase in the terminal:

```
⚖️  THE GOVERNANCE TRIBUNAL  ⚖️
Forensic Compliance & Regression Arbiter
Powered by IBM Bob 2.0

📋 Phase 1: Collecting Evidence (The Subpoena)...
🔍 Phase 2: Classifying Case...           [COMBINED — HIGH severity]
⚖️  Phase 3: Bob Investigating & Remediating...
📄 Phase 4: Generating Tribunal Docket...
👤 Phase 5: Human Approval Required

Do you approve this remediation? [y/N]
```

---

## The Demo Case (4 Layered Defects)

| # | Defect | File | Type |
|:--|:--|:--|:--|
| 1 | Unbounded `while True:` retry loop → hangs forever when DB is down | `checkout/service.py` | Functional Regression |
| 2 | `logger.info(f"User login attempt: {user.email}")` — PII in plain text | `auth/login.py` | Privacy Violation |
| 3 | `AWS_ACCESS_KEY_ID = "AKIAIOSFODNN7EXAMPLE"` — hardcoded credential | `config.py` | Secret Violation |
| 4 | `logger.info(f"Retrying checkout for {user.email}")` — PII in retry log | `checkout/service.py` | Combined (Functional + Policy) |

The Tribunal detects all four, generates a hypothesis for each, applies scripted fixes (mimicking what Bob writes), then runs Dual Validation to confirm all tests pass and all scanners are clean before issuing the Docket.

---

## IBM Bob 2.0 Integration (MCP)

The file `.bob/mcp.json` at the workspace root registers a custom MCP server with Bob. When you open this folder in Bob, it automatically hot-loads the server.

### MCP Tools Exposed to Bob

| Tool | What Bob uses it for |
|:--|:--|
| `git_blame` | Trace a failing line to its culprit commit + author + diff |
| `run_tests` | Run pytest; get structured pass/fail counts and stack traces |
| `run_scanners` | Run `detect-secrets` + PII regex; get combined findings JSON |
| `write_file` | Apply a generated patch (sandboxed — cannot write outside the target repo) |

### How the Agentic Loop Works

```
Bob reads policies/privacy-policy.md
        ↓
Bob calls run_tests()  →  gets failing test + stack trace
        ↓
Bob calls git_blame()  →  finds culprit commit
        ↓
Bob reads the offending source file
        ↓
Bob calls write_file()  →  applies the fix
        ↓
Bob calls run_tests() + run_scanners()
        ↓
    Both pass?  →  Generate Docket  →  Human Approval
    Either fails? → Read new errors → Self-correct → retry
```

The **Dual-Validation Engine** is Bob's adversary — Bob cannot skip it. A patch that fixes the failing test but leaks PII is rejected, and Bob must try again with a clean solution.

### MCP Server Config (`.bob/mcp.json`)

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

## Responsible AI Guardrails

| Guardrail | How It Works |
|:--|:--|
| **Human Approval Gate** | Any HIGH severity case or confidence < 0.75 requires explicit Y/N sign-off |
| **Dual Validation** | Patches must pass tests AND policy scanners — Bob cannot self-approve |
| **Immutable Audit Ledger** | Every state transition, hypothesis, and patch attempt is logged to `logs/{case_id}.jsonl` |
| **Prompt Injection Defense** | Source code is passed to Bob in strict `<source_code>` XML tags; instructions inside are treated as data |
| **Sandbox Writes** | `write_file` MCP tool refuses any path that escapes the target repo boundary |

See [`docs/responsible-ai.md`](governance-tribunal/docs/responsible-ai.md) for the full framework.

---

## Architecture

The Tribunal is a **10-state deterministic state machine**:

```
TRIGGER_RECEIVED → EVIDENCE_COLLECTED → CASE_CLASSIFIED
    → HYPOTHESES_GENERATED → ROOT_CAUSE_SELECTED
    → PATCH_GENERATED → VALIDATION_EXECUTED
    → VERDICT_GENERATED → HUMAN_APPROVAL
    → CASE_CLOSED  (or ESCALATED on failure)
```

See [`docs/architecture.md`](governance-tribunal/docs/architecture.md) for the full Mermaid diagrams.

---

*Built for the IBM Bob 2.0 Hackathon (Sept 2026).*
