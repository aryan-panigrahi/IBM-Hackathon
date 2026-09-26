# ⚖️ Arbiter
### IBM Bob 2.0 Hackathon — Forensic Compliance & Regression Arbiter

> **One agentic loop that simultaneously finds, fixes, and validates every functional regression *and* policy violation in your codebase — then issues an immutable, auditable verdict.**

---

## Problem Statement

Modern CI/CD pipelines are split across silos. Functional regressions surface in pytest. Security violations appear in `detect-secrets`. Privacy leaks show up in SAST scanners. When a developer rushes to fix a failing test, they often accidentally introduce a new violation — logging a payload to debug a crash, thereby leaking PII.

No existing tool treats these as the same class of problem.

---

## Solution

**Arbiter** connects **IBM Bob 2.0** (Agent Mode) to a **Dual-Validation Engine** that enforces an inviolable rule:

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
| **Arbiter Docket** | Jinja2 Markdown verdict report with evidence, patch diff, and audit trail |
| **Bob MCP Integration** | Custom MCP server exposes Arbiter tools directly to IBM Bob 2.0 |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         ARBITER                             │
│                                                             │
│  CLI / launch.py                                            │
│       │                                                     │
│       ▼                                                     │
│  Arbiter (src/orchestrator/tribunal.py)                     │
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
| **Templating** | Jinja2 (Arbiter Docket) |
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
│   │   ├── tribunal.py           ← Master orchestrator (Arbiter class)
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
│   │   └── docket_generator.py   ← Arbiter Docket renderer
│   ├── ledger/
│   │   └── audit_ledger.py       ← Append-only JSONL audit log
│   ├── sandbox/
│   │   └── runner.py             ← Docker sandbox executor
│   └── policy/
│       └── policy_engine.py      ← YAML policy rule loader & evaluator
│
├── mcp_server/
│   └── arbiter_mcp_server.py     ← MCP server — exposes 4 tools to Bob
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
│   └── docket.md.j2              ← Arbiter Docket Jinja2 template
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
⚖️  ARBITER  ⚖️
Forensic Compliance & Regression Arbiter
AI Engine: LMSTUDIO / prism-bonsai-27b

📋 Phase 1: Collecting Evidence...
   Evidence Summary table — tests, secrets, PII, policies loaded

🔍 Phase 2: Classifying Case...
   Case ID, Type (COMBINED), Severity (HIGH)

⚖️  Phase 3: LMSTUDIO Investigating & Remediating...
   Agentic loop: investigate → patch → validate → iterate

📄 Phase 4: Generating Arbiter Docket...
   Full docket printed to terminal

👤 Phase 5: Human Approval Required
   Confidence Score / Severity shown
   Do you approve this remediation? [y/N]
```

The Arbiter Docket and full audit log are saved to `logs/`.

---

## The Demo Case

`demo_repo/` contains **3 intentional defects** that Arbiter is designed to catch and fix:

| # | Defect | File | Type |
|:--|:--|:--|:--|
| 1 | `while not success:` — unbounded retry loop, crashes on `Timeout` | `payment_gateway.py` | Functional Regression |
| 2 | `logger.info(f"Processing for {user.email}")` — PII in plain text | `payment_gateway.py` | Privacy Violation |
| 3 | `API_KEY = "sk-abc123xyz..."` — hardcoded credential | `config.py` | Security Violation |

The `test_retry_payment_timeout` test **intentionally fails** on the broken code. Once Arbiter patches `payment_gateway.py`, all 5 tests pass and all 3 policy scanners return clean.

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

A GitHub Actions workflow is included at `.github/workflows/arbiter.yml`. It triggers on every PR and push to `main`, runs the full investigation in `--non-interactive` mode, and uploads the Arbiter Docket as a downloadable artifact.

```yaml
# Trigger on any push or PR
on:
  pull_request:
    branches: [main]
  push:
    branches: [main]
```

---

## Phase Algorithms

### Phase 1 — Evidence Collection (`EvidenceCollector.collect_all`)

Runs **5 sub-algorithms** in sequence and bundles them into a single evidence dict.

#### 1a. `run_tests()` — Functional Regression Scan
```
1. subprocess: pytest <tests_dir> --json-report
2. IF json report exists:
     Parse report.json → extract all tests where outcome == "failed"
     For each failure: extract { test_id, file, line, message, longrepr }
     Return { passed: returncode==0, failures: [...] }
3. ELSE (fallback):
     Regex match stdout for "FAILED tests/X::Y - Z" pattern
     Return single failure entry
```

#### 1b. `run_secret_scan()` — Hardcoded Credential Detection
```
1. subprocess: detect-secrets scan <repo_path> → parse JSON results dict
2. Walk all .py files (skip .git / venv / __pycache__):
     For each line, apply regex patterns:
       - API_KEY\s*=\s*["'][^"']{8,}["']  → "Hardcoded API Key"
       - AWS_ACCESS_KEY_ID\s*=\s*[...]     → "AWS Secret Key"
       - DB_PASSWORD\s*=\s*[...]           → "Database Password"
     Skip lines containing os.getenv (already safe)
3. Merge detect-secrets findings + regex findings
4. Return { passed: findings==empty, findings: {...} }
```

#### 1c. `run_pii_scan()` — Privacy / GDPR Logging Scan
```
1. Walk all .py files
2. For each line:
     IF ("logger." in line OR "print(" in line)
     AND NOT ("mask_email" in line OR "mask_card" in line):
       Apply 4 PII regex patterns:
         Email:       [a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[...]
         Email_Var:   user\.email | user_email | \.email
         Card_Number: card\.number | card_number | credit_card
         SSN:         \b\d{3}-\d{2}-\d{4}\b
       On first match: record { file, line, type, content }
3. Return { passed: findings==empty, findings: [...] }
```

#### 1d. `run_security_scan()` — Bandit SAST
```
1. subprocess: bandit -r <repo_path> -f json
2. Filter results where issue_severity == "HIGH"
3. Return { passed: high_findings==empty, findings, total_issues }
```

#### 1e. `blame_line()` — Git Forensics
```
1. git.repo.blame("HEAD", <file>)
2. Walk blame hunks: find which commit owns the failing line_num
3. If commit has parents: get the diff for that file from parent→commit
4. Return { commit, author, date, message, diff }
```

---

### Phase 2 — Classification (`classify_case` + `compute_confidence`)

#### 2a. Case Type Classification
```
tests_failed  = NOT evidence.test_results.passed
secrets_found = NOT evidence.secret_scan.passed
pii_found     = NOT evidence.pii_scan.passed
policy_failed = secrets_found OR pii_found

IF tests_failed AND policy_failed → COMBINED
ELIF tests_failed                 → FUNCTIONAL
ELIF policy_failed                → POLICY
ELSE                              → UNKNOWN
```

#### 2b. Severity Scoring
```
Default severity = MEDIUM

IF secrets_found: severity = HIGH

FOR each changed_file in evidence.changed_files:
  IF any of ["auth","login","payment","checkout","crypto","secret","config"]
     is a substring of file name (case-insensitive):
       severity = HIGH; break

Return (case_type, severity)
```

#### 2c. Confidence Score Computation
```
score = 0.0
score += 0.40   if reproduction_success (test actually failed)
score += 0.25   if recent_commits exist
score += 0.15   if stack trace points to specific file/line
score += 0.10   if PII or secret violation found (policy match)
score += 0.10   baseline calibration (always)

Return min(score, 1.0) rounded to 2dp
```

Maximum achievable confidence score: **1.0** (all signals present).

---

### Phase 3 — Agentic Remediation Loop

This is the core self-correcting loop in `Arbiter.run_remediation_loop()`.

```
FOR attempt in range(max_retries):              ← default: 2 retries

  ── AI Agent Call ──────────────────────────────────────────────────────
  investigation = agent.investigate(evidence, policies)
    │  Sends structured prompt:
    │    - failing test IDs, file, line, 500-char traceback
    │    - hardcoded secret locations
    │    - PII violation locations
    │    - last 3 git commits
    │    - first 2 policy files (800 chars each)
    │  Receives strict JSON:
    │    { root_cause, patch_hunks[], parole_conditions, residual_risks }
    └─ ON (ConnectionError / TimeoutError / Exception):
         Fall back to deterministic scripted patch

  ── Patch Application ──────────────────────────────────────────────────
  FOR each hunk in investigation.patch_hunks:
    1. Read full file from disk
    2. IF original_snippet found verbatim → replace with fixed_snippet (1st occurrence)
       ELSE try whitespace-normalised regex match, then replace
    3. IF file changed: write to disk, generate unified diff

  ── CST Safety Pass ────────────────────────────────────────────────────
  FOR each .py file in repo:
    Apply MaskEmailTransformer  (LibCST)   — wraps PII in logger calls
    Apply HardcodedSecretTransformer (LibCST) — replaces string literals with os.getenv()
    IF changed: write to disk, append to diff

  ── Dual Validation Gate (5 checks, ALL must pass) ─────────────────────
  [1] syntax     = ast.parse() every .py file
  [2] functional = pytest full test suite
  [3] secrets    = detect-secrets + API_KEY regex scan
  [4] pii        = logger.*/print() + PII regex scan
  [5] security   = bandit -r (HIGH severity findings only)

  IF all 5 PASS:
    verdict = "GUILTY. REMEDIATED. READY FOR MERGE."
    return result                            ← EXIT LOOP ✓

  ELSE:
    Collect { functional_errors, syntax_errors, policy_errors }
    Inject → evidence["_last_validation_errors"]   ← agent sees on next attempt

── Max retries exhausted ──────────────────────────────────────────────────
verdict = "COULD NOT FULLY REMEDIATE. ESCALATED TO LEAD ENGINEER."
status  = ESCALATED
```

#### 3a. LibCST Transformers

**`MaskEmailTransformer`**
```
Match:     logger.info( <expr containing "email"> )
           where "mask_email" is NOT already in the expression
Transform: logger.info( mask_email(<original_expr>) )
```

**`HardcodedSecretTransformer`**
```
Match:     API_KEY = "sk-..."   (SimpleString assigned to a known sensitive variable)
Transform: API_KEY = os.getenv('API_KEY')
```

Fallback when LibCST is not installed: equivalent regex substitutions on raw source text.

---

### Phase 4 — Docket Generation

```
1. Render Jinja2 template (templates/docket.md.j2) with:
     case_id, severity, case_type, confidence_score,
     suspect (git blame result), root_cause, unified patch diff,
     5-row validation summary table, parole_conditions,
     residual_risks, UTC timestamp
2. Write rendered Markdown → logs/<case_id>_docket.md
```

---

### Phase 5 — Human Approval Gate

```
Triggered when: severity == HIGH   OR   confidence_score < 0.75

Display: confidence score, severity, docket summary
Prompt:  "Do you approve this remediation? [y/N]"
  y → status = CASE_CLOSED,   human_approved = True
  N → status = ESCALATED,     human_approved = False

CI/CD mode (--non-interactive): auto-approve, gate is bypassed
```

---

### Phase 6 — Immutable Audit Ledger

```
Every state transition appends one JSON line to logs/<case_id>.jsonl:
  {
    "timestamp": "<ISO-8601 UTC>",
    "case_id":   "GT-YYYYMMDD-XXXX",
    "event":     "evidence_collected" | "patch_attempt" | "validation_result" | ...,
    "details":   { <event-specific payload> }
  }
File is opened in append ("a") mode — existing entries are never modified.

On case close:
  Full case dict (evidence + history + verdict + patches)
  → logs/<case_id>_full.json
```

---

### State Machine (12 States)

```
TRIGGER_RECEIVED
  → EVIDENCE_COLLECTED
    → CASE_CLASSIFIED
      → ROOT_CAUSE_SELECTED
        → PATCH_GENERATED ─────────────────────────────────┐
          → VALIDATION_EXECUTED                             │ retry
               PASS → VERDICT_GENERATED                    │
                         → HUMAN_APPROVAL                  │
                           → CASE_CLOSED                   │
               FAIL ───────────────────────────────────────┘
                    → (max retries exhausted) → ESCALATED
```

---

## Future Improvements

- GitHub PR creation after approved remediation (PyGithub integration stub already in `requirements.txt`)
- Docker sandbox isolation for validation runs (`src/sandbox/runner.py` already implemented)
- Streamlit dashboard for docket review and audit log browsing
- Support for multi-file, multi-hunk patches across larger codebases

---

*Built for the IBM Bob 2.0 Hackathon (Sept 2026).*
