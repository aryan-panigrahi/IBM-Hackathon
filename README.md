# 🏛️ The Governance Tribunal
### IBM Bob 2.0 Hackathon 2026 — Forensic Compliance & Regression Arbiter

---

## What It Does

The Governance Tribunal is an **agentic DevSecOps system** powered by **IBM Bob 2.0** that automatically detects, investigates, and remediates code defects before they reach production. It combines:

- **Functional regression detection** (pytest + structured failure analysis)
- **Policy violation scanning** (PII logging, hardcoded secrets via `detect-secrets` + Bandit SAST)
- **Forensic root cause tracing** (git blame → culprit commit identification)
- **Surgical code repair** (LibCST AST transformers for lossless patching)
- **Dual-validation** (tests + policy must both pass)
- **Human-in-the-loop approval gate** before any merge
- **Immutable audit ledger** (JSONL + full case JSON)
- **Tribunal Docket** (Jinja2 Markdown verdict report)

---

## Project Structure

```
IBM Hackathon/
├── cli.py                          ← CLI entry point
├── requirements.txt
├── .env.example
├── .gitignore
├── .bobignore
│
├── src/
│   ├── orchestrator/
│   │   ├── case_manager.py         ← Case state machine & data model
│   │   ├── classifier.py           ← Case type & severity classifier
│   │   └── tribunal.py             ← Master orchestrator (GovernanceTribunal)
│   ├── evidence/
│   │   └── collector.py            ← pytest, detect-secrets, PII scan, git blame
│   ├── validation/
│   │   └── dual_validator.py       ← AST syntax + pytest + policy + Bandit
│   ├── remediation/
│   │   ├── cst_transformers.py     ← LibCST transformers (mask_email, getenv)
│   │   ├── patch_generator.py      ← Unified diff generator
│   │   └── patch_applier.py        ← git apply with rollback support
│   ├── reporting/
│   │   └── docket_generator.py     ← Jinja2 Tribunal Docket renderer
│   ├── ledger/
│   │   └── audit_ledger.py         ← Append-only JSONL audit log
│   ├── sandbox/
│   │   └── runner.py               ← Docker sandbox executor
│   └── policy/
│       └── policy_engine.py        ← YAML policy rule loader & evaluator
│
├── policies/
│   ├── privacy_policy.md
│   ├── security_policy.md
│   └── policies.yaml               ← Machine-readable policy rules
│
├── templates/
│   └── docket.md.j2                ← Tribunal Docket Jinja2 template
│
├── logs/                           ← Auto-generated audit logs (gitignored)
│
└── demo_repo/                      ← Intentionally defective target repo
    ├── payment_gateway.py          ← BUG: unbounded loop + PII leak
    ├── config.py                   ← BUG: hardcoded secret
    ├── checkout_service.py
    └── tests/
        └── test_checkout.py        ← Failing tests that Bob must fix
```

---

## Quick Start

### 1. Set Up Environment
```bash
cd "IBM Hackathon"
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run the Tribunal Against the Demo Repo
```bash
python cli.py investigate ./demo_repo
```

### 3. What You'll See
```
⚖️  THE GOVERNANCE TRIBUNAL  ⚖️
Forensic Compliance & Regression Arbiter
Powered by IBM Bob 2.0

📋 Phase 1: Collecting Evidence...
🔍 Phase 2: Classifying Case... [COMBINED — HIGH severity]
⚖️  Phase 3: Bob Investigating & Remediating...
📄 Phase 4: Generating Tribunal Docket...
👤 Phase 5: Human Approval Required

Do you approve this remediation? [y/N]
```

---

## The Demo Case (Killer Scenario)

The `demo_repo/` contains **3 intentional defects** layered together:

| # | Defect | File | Type |
|:--|:--|:--|:--|
| 1 | Unbounded retry loop → `TimeoutError` | `payment_gateway.py:43` | Functional Regression |
| 2 | PII logged: `logger.info(user.email)` | `payment_gateway.py:12` | Privacy Violation |
| 3 | Hardcoded secret: `API_KEY = "sk-abc123..."` | `config.py:2` | Security Violation |

**Bob fixes all three simultaneously** — bounded loop, LibCST email masking, `os.getenv` secret extraction — then validates with a 5-check Dual Validation suite.

---

## IBM Bob 2.0 Integration

Bob operates in **Agent Mode** using these MCP tools:

| Tool | Purpose |
|:--|:--|
| `read_file` | Evidence collection |
| `write_file` | Apply patches |
| `run_shell` | Execute pytest, scanners |
| `git_blame` | Root cause tracing |
| `create_report` | Docket generation |

Configure `.bob/mcp.json` to point to your MCP server, and run Bob in the IDE with the **"Forensic Compliance Arbiter"** system prompt from `governance_tribunal_research.md`.

---

## Key Innovation

> The Tribunal is the **only hackathon entry that applies LibCST lossless AST transformations** for code repair, preserving comments, whitespace, and style — exactly as a senior engineer would review and merge a patch.

---

## Hackathon Submission

- **Prize Pool:** $10,000–$12,000
- **Deadline:** Sept 27, 2026 @ 15:00 UTC
- **Video:** 5-minute MP4 demo required
- See `governance_tribunal_research.md` for full submission checklist
