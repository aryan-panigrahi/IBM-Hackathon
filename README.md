# ⚖️ The Governance Tribunal
### IBM Bob 2.0 Hackathon — Forensic Compliance & Regression Arbiter

> **One agentic loop that simultaneously finds, fixes, and validates every functional regression *and* policy violation in your codebase — then issues an immutable, auditable verdict.**

---

## Problem Statement

Modern CI/CD pipelines are split across silos. Functional regressions surface in pytest. Security violations appear in `detect-secrets`. Privacy leaks show up in SAST scanners. When a developer rushes to fix a failing test, they often accidentally introduce a new violation — logging a payload to debug a crash, thereby leaking PII.

No existing tool treats these as the same class of problem.

---

## Solution

The Governance Tribunal connects **IBM Bob 2.0** (Agent Mode) to a **Dual-Validation Engine** that enforces an inviolable rule:

> A patch is only accepted when it passes **both** the full test suite **and** all policy scanners simultaneously.

Bob doesn't just autocomplete — it acts as a Forensic Investigator and Compliance Arbiter, reading policy documents, tracing git blame, generating surgical patches, and self-correcting when its own fix fails validation.

---

## Key Features

| Feature | Description |
|:--|:--|
| **Forensic Evidence Collection** | pytest + detect-secrets + PII scanner + Bandit SAST + git blame |
| **AI-Powered Root Cause Analysis** | Any OpenAI-compatible backend (LM Studio, IBM Bob 2.0, Ollama, OpenAI) |
| **LibCST Lossless Patching** | Byte-perfect AST transforms — preserves comments, whitespace, style |
| **Dual-Validation Engine** | 5-check gate: syntax + tests + secrets + PII + SAST security |
| **Self-Correction Loop** | Validation errors fed back to the agent for up to N retry attempts |
| **Human Approval Gate** | HIGH severity or low confidence (<0.75) requires explicit sign-off |
| **Immutable Audit Ledger** | Append-only JSONL + full case JSON for compliance teams |
| **Tribunal Docket** | Jinja2 Markdown verdict report with evidence, patch diff, and audit trail |
| **Bob MCP Integration** | Custom MCP server exposes Tribunal tools directly to IBM Bob 2.0 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    THE GOVERNANCE TRIBUNAL                   │
│                                                             │
│  CLI / launch.py                                            │
│       │                                                     │
│       ▼                                                     │
│  GovernanceTribunal (src/orchestrator/tribunal.py)          │
│  ┌──────────────────────────────────────────────────────┐   │
│  │ Phase 1: EvidenceCollector                           │   │
│  │   pytest · detect-secrets · PII scan · git blame     │   │
│  │                                                      │   │
│  │ Phase 2: Classifier                                  │   │
│  │   FUNCTIONAL | POLICY | COMBINED · HIGH/MED/LOW      │   │
│  │                                                      │   │
│  │ Phase 3: Agentic Loop  ◄──────────────────────┐     │   │
│  │   AI Agent.investigate() → patch_hunks         │     │   │
│  │   LibCST Transformers (safety net)             │     │   │
│  │        │                                       │     │   │
│  │        ▼                                       │     │   │
│  │   DualValidator (5 checks)                     │     │   │
│  │   syntax · pytest · secrets · PII · bandit     │     │   │
│  │        │ FAIL ──────────────────────────────────     │   │
│  │        │ PASS                                        │   │
│  │                                                      │   │
│  │ Phase 4: DocketGenerator  (Jinja2 + diff)           │   │
│  │ Phase 5: Human Approval Gate                        │   │
│  │ Phase 6: AuditLedger  (JSONL + full JSON)           │   │
│  └──────────────────────────────────────────────────────┘   │
└─────────────────────────────────────────────────────────────┘
```

---

## Tech Stack

| Layer | Technology |
|:--|:--|
| **Core Reasoning** | IBM Bob 2.0 Agent Mode / LM Studio / Ollama / OpenAI (via OpenAI-compatible API) |
| **MCP Integration** | Custom Python MCP server (stdio transport) |
| **Orchestration** | Python state machine (10 states) |
| **Code Repair** | LibCST (lossless CST transforms) + unified diff |
| **Scanners** | pytest-json-report · detect-secrets · Bandit SAST · custom PII regex |
| **CLI** | Typer + Rich |
| **Templating** | Jinja2 (Tribunal Docket) |
| **Git Integration** | GitPython |

---

## Project Structure

```
IBM Hackathon/
│
├── cli.py                        ← Main entry point
├── launch.py                     ← Cross-platform interactive launcher
├── launch.command                ← macOS double-click launcher
├── launch.bat                    ← Windows double-click launcher
├── requirements.txt
├── .env.example                  ← Copy to .env and configure
│
├── src/
│   ├── agent/
│   │   ├── base.py               ← AgentBackend ABC + prompt builders
│   │   ├── factory.py            ← Backend factory (reads .env)
│   │   └── openai_compatible.py  ← Universal OpenAI-compatible adapter
│   ├── orchestrator/
│   │   ├── tribunal.py           ← Master orchestrator
│   │   ├── case_manager.py       ← Case data model + state machine
│   │   └── classifier.py        ← Case type, severity, confidence scoring
│   ├── evidence/
│   │   └── collector.py          ← pytest, detect-secrets, PII scan, git blame
│   ├── validation/
│   │   └── dual_validator.py     ← 5-check dual-validation engine
│   ├── remediation/
│   │   ├── cst_transformers.py   ← LibCST MaskEmail + HardcodedSecret transformers
│   │   ├── patch_generator.py    ← Unified diff generator
│   │   └── patch_applier.py      ← git apply with rollback support
│   ├── reporting/
│   │   └── docket_generator.py   ← Tribunal Docket renderer
│   ├── ledger/
│   │   └── audit_ledger.py       ← Append-only JSONL audit log
│   ├── sandbox/
│   │   └── runner.py             ← Docker sandbox executor
│   └── policy/
│       └── policy_engine.py      ← YAML policy rule loader & evaluator
│
├── mcp_server/
│   └── tribunal_mcp_server.py    ← MCP server — exposes 4 tools to Bob
│
├── .bob/
│   └── mcp.json                  ← Registers the MCP server with Bob
│
├── demo_repo/                    ← Intentionally defective target repository
│   ├── payment_gateway.py        ← DEFECT 1: unbounded loop  DEFECT 2: PII log
│   ├── config.py                 ← DEFECT 3: hardcoded API key
│   ├── checkout_service.py
│   └── tests/
│       └── test_checkout.py      ← test_retry_payment_timeout FAILS in broken state
│
├── policies/
│   ├── privacy_policy.md         ← Agent reads this to understand PII rules
│   ├── security_policy.md
│   └── policies.yaml             ← Machine-readable policy rules
│
├── templates/
│   └── docket.md.j2              ← Tribunal Docket Jinja2 template
│
└── logs/                         ← Auto-generated at runtime (gitignored)
```

---

## Installation

```bash
# 1. Clone / open the repository
cd "IBM Hackathon"

# 2. Create and activate a virtual environment
python3 -m venv venv
source venv/bin/activate      # Windows: .\venv\Scripts\activate

# 3. Install all dependencies
pip install -r requirements.txt

# 4. Copy and configure the environment file
cp .env.example .env
# Edit .env — set AGENT_BACKEND and AGENT_MODEL to match your setup
```

---

## Environment Variables

Copy `.env.example` to `.env` and configure:

```env
# Which AI backend to use
AGENT_BACKEND=lmstudio        # lmstudio | ollama | bob | openai | groq | custom

# Which model to use
AGENT_MODEL=prism-bonsai-27b  # Match the model name in your backend's UI

# API endpoint (leave blank to use the default for your backend)
AGENT_BASE_URL=

# API key — leave as "none" for local models
AGENT_API_KEY=none

# Model tuning
AGENT_TEMPERATURE=0.1
AGENT_MAX_TOKENS=4096
AGENT_TIMEOUT=120
```

Backend default endpoints:

| Backend | Default URL |
|:--|:--|
| `lmstudio` | `http://localhost:1234/v1` |
| `ollama` | `http://localhost:11434/v1` |
| `bob` | `http://localhost:11435/v1` |
| `openai` | `https://api.openai.com/v1` |
| `groq` | `https://api.groq.com/openai/v1` |

---

## Running the Project

### Option A — Interactive Launcher (recommended for demos)

```bash
python launch.py        # macOS/Linux
launch.command          # macOS double-click
launch.bat              # Windows double-click
```

The launcher checks Python, sets up the venv, verifies your AI backend is online, then lets you pick a target repo interactively.

### Option B — Direct CLI

```bash
# Investigate the built-in demo repo
python cli.py investigate ./demo_repo

# Override the AI backend on the fly
python cli.py investigate ./demo_repo --agent ollama --model llama3.1
python cli.py investigate ./demo_repo --agent bob --model bob-2.0
python cli.py investigate ./demo_repo --agent openai --model gpt-4o

# CI/CD mode (no interactive prompt)
python cli.py investigate ./demo_repo --non-interactive

# List all supported backends
python cli.py backends
```

---

## Usage

After starting an investigation you will see five phases in the terminal:

```
⚖️  THE GOVERNANCE TRIBUNAL  ⚖️
Forensic Compliance & Regression Arbiter
AI Engine: LMSTUDIO / prism-bonsai-27b

📋 Phase 1: Collecting Evidence (The Subpoena)...
   Evidence Summary table — tests, secrets, PII, policies loaded

🔍 Phase 2: Classifying Case...
   Case ID, Type (COMBINED), Severity (HIGH)

⚖️  Phase 3: LMSTUDIO Investigating & Remediating...
   Agentic loop: investigate → patch → validate → iterate

📄 Phase 4: Generating Tribunal Docket...
   Full docket printed to terminal

👤 Phase 5: Human Approval Required
   Confidence Score / Severity shown
   Do you approve this remediation? [y/N]
```

The Tribunal Docket and full audit log are saved to `logs/`.

---

## The Demo Case

`demo_repo/` contains **3 intentional defects** that the Tribunal is designed to catch and fix:

| # | Defect | File | Type |
|:--|:--|:--|:--|
| 1 | `while not success:` — unbounded retry loop, crashes on `Timeout` | `payment_gateway.py` | Functional Regression |
| 2 | `logger.info(f"Processing for {user.email}")` — PII in plain text | `payment_gateway.py` | Privacy Violation |
| 3 | `API_KEY = "sk-abc123xyz..."` — hardcoded credential | `config.py` | Security Violation |

The `test_retry_payment_timeout` test **intentionally fails** on the broken code. Once the Tribunal patches `payment_gateway.py`, all 5 tests pass and all 3 policy scanners return clean.

---

## IBM Bob 2.0 Integration (MCP)

Opening this workspace folder in Bob automatically loads the custom MCP server registered in [`.bob/mcp.json`](.bob/mcp.json).

### Tools Exposed to Bob

| Tool | Purpose |
|:--|:--|
| `git_blame` | Trace a file/line to its culprit commit, author, and diff |
| `run_tests` | Execute pytest; get structured pass/fail JSON |
| `run_scanners` | Run detect-secrets + PII scanner; get combined findings |
| `write_file` | Apply a patch file (sandboxed — cannot write outside the repo) |

### Install the MCP dependency

```bash
pip install mcp>=1.0   # already in requirements.txt
```

---

## Responsible AI Guardrails

| Guardrail | Mechanism |
|:--|:--|
| **Human Approval Gate** | HIGH severity or confidence < 0.75 always prompts for Y/N sign-off |
| **Dual Validation** | 5 independent checks — Bob cannot skip or self-approve |
| **Immutable Audit Ledger** | Every state transition, hypothesis, and patch attempt written to append-only JSONL |
| **Prompt Injection Defence** | Source code wrapped in `<source_code>` XML tags; treated as inert data |
| **Sandbox Writes** | `write_file` MCP tool rejects any path escaping the target repo boundary |

---

## CI/CD Deployment

A GitHub Actions workflow is included at `.github/workflows/tribunal.yml`. It triggers on every PR and push to `main`, runs the full investigation in `--non-interactive` mode, and uploads the Tribunal Docket as a downloadable artifact.

```yaml
# Trigger on any push or PR
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

---

## Future Improvements

- GitHub PR creation after approved remediation (PyGithub integration stub already in `requirements.txt`)
- Docker sandbox isolation for validation runs (`src/sandbox/runner.py` already implemented)
- Streamlit dashboard for docket review and audit log browsing
- Support for multi-file, multi-hunk patches across larger codebases

---

*Built for the IBM Bob 2.0 Hackathon (Sept 2026).*
