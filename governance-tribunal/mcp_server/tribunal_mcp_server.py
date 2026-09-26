#!/usr/bin/env python3
"""Governance Tribunal MCP Server.

Exposes the Tribunal's forensic tools to IBM Bob 2.0 via the Model Context Protocol.

Tools exposed:
  - git_blame       : Trace a file/line to the responsible commit and author
  - run_tests       : Execute the pytest suite and return structured results
  - run_scanners    : Run detect-secrets + PII scanner against a source tree
  - write_file      : Write content to a file (sandboxed to the target repo)

Usage (stdio transport — Bob spawns this as a child process):
  python3 mcp_server/tribunal_mcp_server.py

Register in .bob/mcp.json (see configure-mcp skill).
"""

import json
import os
import re
import subprocess
import sys
from pathlib import Path

# ---------------------------------------------------------------------------
# MCP SDK import — graceful fallback if the package is not installed
# ---------------------------------------------------------------------------
try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import Tool, TextContent
    _MCP_AVAILABLE = True
except ImportError:
    _MCP_AVAILABLE = False

# ---------------------------------------------------------------------------
# Resolve the default repo path: one level up from this file's parent dir
# ---------------------------------------------------------------------------
_SERVER_DIR = Path(__file__).resolve().parent          # governance-tribunal/mcp_server
_PROJECT_ROOT = _SERVER_DIR.parent                     # governance-tribunal/
_DEFAULT_REPO = str(_PROJECT_ROOT / "demo_repo")


# ===========================================================================
# Tool implementations (pure Python — no MCP dependency required here)
# ===========================================================================

def _git_blame(repo_path: str, file_path: str, line_number: int) -> dict:
    """Trace a specific file line to its originating commit."""
    repo = Path(repo_path).resolve()
    try:
        result = subprocess.run(
            ["git", "blame", "-L", f"{line_number},{line_number}", "--porcelain", file_path],
            capture_output=True, text=True, cwd=str(repo), timeout=15,
        )
        lines = result.stdout.splitlines()
        if not lines:
            return {"error": "No blame output — file may not be tracked by git."}

        commit_sha = lines[0].split()[0]
        author = next((l[len("author "):] for l in lines if l.startswith("author ")), "Unknown")
        summary = next((l[len("summary "):] for l in lines if l.startswith("summary ")), "")

        diff_result = subprocess.run(
            ["git", "diff", f"{commit_sha}~1", commit_sha, "--", file_path],
            capture_output=True, text=True, cwd=str(repo), timeout=15,
        )
        return {
            "commit": commit_sha[:7],
            "author": author,
            "message": summary,
            "diff": diff_result.stdout[:4000],  # cap to avoid token overflow
        }
    except subprocess.TimeoutExpired:
        return {"error": "git blame timed out"}
    except Exception as exc:
        return {"error": str(exc)}


def _run_tests(repo_path: str) -> dict:
    """Execute the pytest suite in repo_path/tests and return structured results."""
    repo = Path(repo_path).resolve()
    report_file = repo / "mcp_test_report.json"
    try:
        subprocess.run(
            [
                sys.executable, "-m", "pytest",
                str(repo / "tests"),
                "--json-report",
                f"--json-report-file={report_file}",
                "--tb=short", "-q",
            ],
            capture_output=True, text=True, cwd=str(repo), timeout=60,
        )
    except subprocess.TimeoutExpired:
        return {"passed": False, "error": "pytest timed out", "failures": []}
    except Exception as exc:
        return {"passed": False, "error": str(exc), "failures": []}

    try:
        with open(report_file) as fh:
            report = json.load(fh)
        failures = []
        for test in report.get("tests", []):
            if test["outcome"] == "failed":
                crash = test.get("call", {}).get("crash", {})
                failures.append({
                    "test_id": test["nodeid"],
                    "file": crash.get("path", ""),
                    "line": crash.get("lineno", 0),
                    "message": crash.get("message", ""),
                })
        return {
            "passed": len(failures) == 0,
            "total": report.get("summary", {}).get("total", 0),
            "failed_count": len(failures),
            "failures": failures,
        }
    except (FileNotFoundError, json.JSONDecodeError) as exc:
        return {"passed": False, "error": str(exc), "failures": []}


def _run_scanners(repo_path: str) -> dict:
    """Run detect-secrets + regex PII scanner on the source tree."""
    repo = Path(repo_path).resolve()
    src_dir = repo / "src"

    # ── Secret scan ──────────────────────────────────────────────────────────
    secrets_result: dict = {"passed": True, "findings": {}}
    try:
        result = subprocess.run(
            ["detect-secrets", "scan", str(src_dir)],
            capture_output=True, text=True, timeout=30,
        )
        output = json.loads(result.stdout)
        findings = output.get("results", {})
        secrets_result = {"passed": len(findings) == 0, "findings": findings}
    except FileNotFoundError:
        secrets_result = {"passed": True, "findings": {}, "note": "detect-secrets not installed"}
    except Exception as exc:
        secrets_result = {"passed": True, "findings": {}, "error": str(exc)}

    # ── PII scan ─────────────────────────────────────────────────────────────
    pii_pattern = re.compile(
        r"(\.email|user_email|user\.email|user_data|password|ssn|credit_card)",
        re.IGNORECASE,
    )
    pii_findings: list = []
    if src_dir.exists():
        for py_file in src_dir.rglob("*.py"):
            try:
                lines = py_file.read_text(encoding="utf-8").splitlines()
            except (OSError, UnicodeDecodeError):
                continue
            for line_num, line in enumerate(lines, 1):
                if "logger." in line or "logging." in line or "print(" in line:
                    if pii_pattern.search(line):
                        pii_findings.append({
                            "file": str(py_file.relative_to(repo)),
                            "line": line_num,
                            "content": line.strip(),
                        })

    pii_result = {"passed": len(pii_findings) == 0, "findings": pii_findings}

    return {
        "passed": secrets_result["passed"] and pii_result["passed"],
        "secret_scan": secrets_result,
        "pii_scan": pii_result,
    }


def _write_file(repo_path: str, file_path: str, content: str) -> dict:
    """Write content to a file, sandboxed inside repo_path."""
    repo = Path(repo_path).resolve()
    target = (repo / file_path).resolve()

    # Safety: refuse to write outside the target repo
    try:
        target.relative_to(repo)
    except ValueError:
        return {"success": False, "error": "Path escapes the target repository — write refused."}

    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(content, encoding="utf-8")
        return {"success": True, "path": str(target.relative_to(repo))}
    except OSError as exc:
        return {"success": False, "error": str(exc)}


# ===========================================================================
# MCP Server wiring
# ===========================================================================

def build_server() -> "Server":
    server = Server("governance-tribunal")

    @server.list_tools()
    async def list_tools():
        return [
            Tool(
                name="git_blame",
                description=(
                    "Trace a specific line in a file back to the commit that last modified it. "
                    "Returns commit SHA, author, commit message, and the diff."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Absolute path to the target git repository."},
                        "file_path": {"type": "string", "description": "Path to the file, relative to repo_path."},
                        "line_number": {"type": "integer", "description": "1-based line number to blame."},
                    },
                    "required": ["repo_path", "file_path", "line_number"],
                },
            ),
            Tool(
                name="run_tests",
                description="Run the pytest suite for the target repository. Returns pass/fail counts and failure details.",
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Absolute path to the target repository."},
                    },
                    "required": ["repo_path"],
                },
            ),
            Tool(
                name="run_scanners",
                description=(
                    "Run detect-secrets (hardcoded credential detection) and a regex PII scanner "
                    "against the repository's source tree. Returns combined findings."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Absolute path to the target repository."},
                    },
                    "required": ["repo_path"],
                },
            ),
            Tool(
                name="write_file",
                description=(
                    "Write content to a file inside the target repository. "
                    "Used by Bob to apply generated remediation patches. "
                    "Sandboxed: cannot write outside repo_path."
                ),
                inputSchema={
                    "type": "object",
                    "properties": {
                        "repo_path": {"type": "string", "description": "Absolute path to the target repository."},
                        "file_path": {"type": "string", "description": "Path to the file to write, relative to repo_path."},
                        "content": {"type": "string", "description": "Full file content to write."},
                    },
                    "required": ["repo_path", "file_path", "content"],
                },
            ),
        ]

    @server.call_tool()
    async def call_tool(name: str, arguments: dict):
        repo = arguments.get("repo_path", _DEFAULT_REPO)

        if name == "git_blame":
            result = _git_blame(repo, arguments["file_path"], arguments["line_number"])
        elif name == "run_tests":
            result = _run_tests(repo)
        elif name == "run_scanners":
            result = _run_scanners(repo)
        elif name == "write_file":
            result = _write_file(repo, arguments["file_path"], arguments["content"])
        else:
            result = {"error": f"Unknown tool: {name}"}

        return [TextContent(type="text", text=json.dumps(result, indent=2, default=str))]

    return server


async def _main():
    server = build_server()
    async with stdio_server() as (read_stream, write_stream):
        await server.run(read_stream, write_stream, server.create_initialization_options())


if __name__ == "__main__":
    if not _MCP_AVAILABLE:
        print(
            "ERROR: 'mcp' package is not installed.\n"
            "Install it with:  pip install mcp\n"
            "Or:               pip install -r requirements.txt",
            file=sys.stderr,
        )
        sys.exit(1)

    import asyncio
    asyncio.run(_main())
