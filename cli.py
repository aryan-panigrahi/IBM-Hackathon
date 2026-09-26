"""The Governance Tribunal — CLI Entry Point.

Usage:
    # Use whatever backend is set in .env (default: LM Studio + Prism Bonsai 27B)
    python cli.py investigate ./demo_repo

    # Override backend and model from the command line
    python cli.py investigate ./demo_repo --agent lmstudio --model prism-bonsai-27b
    python cli.py investigate ./demo_repo --agent bob      --model bob-2.0
    python cli.py investigate ./demo_repo --agent ollama   --model llama3.1
    python cli.py investigate ./demo_repo --agent openai   --model gpt-4o

    # List all supported backends
    python cli.py backends
"""

import sys
from pathlib import Path

project_root = Path(__file__).resolve().parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import typer
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich import box

from src.orchestrator.tribunal import GovernanceTribunal
from src.agent.factory import list_supported_backends

app = typer.Typer(
    name="tribunal",
    help="⚖️  The Governance Tribunal — Forensic Compliance & Regression Arbiter",
    add_completion=False,
)
console = Console()


def print_banner(backend: str, model: str):
    banner = Text()
    banner.append("⚖️  THE GOVERNANCE TRIBUNAL  ⚖️\n", style="bold red")
    banner.append("Forensic Compliance & Regression Arbiter\n", style="dim")
    banner.append(f"AI Engine: {backend.upper()} / {model}", style="italic cyan")
    console.print(Panel(banner, border_style="red", box=box.DOUBLE))


def print_evidence_table(evidence: dict):
    table = Table(title="📋 Evidence Summary", box=box.ROUNDED)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    tests = evidence.get("test_results", {})
    status = "✅ PASS" if tests.get("passed") else "❌ FAIL"
    table.add_row("Functional Tests", status, f"{tests.get('failed_count', 0)} failures")

    secrets = evidence.get("secret_scan", {})
    status = "✅ CLEAN" if secrets.get("passed") else "🚨 SECRETS FOUND"
    count = sum(len(v) if isinstance(v, list) else 1 for v in secrets.get("findings", {}).values())
    table.add_row("Secret Scan", status, f"{count} findings")

    pii = evidence.get("pii_scan", {})
    status = "✅ CLEAN" if pii.get("passed") else "🚨 PII DETECTED"
    table.add_row("PII Scan", status, f"{len(pii.get('findings', []))} findings")

    policies = evidence.get("policies", {})
    table.add_row("Policies Loaded", "📄", ", ".join(policies.keys()) or "none")

    console.print(table)


def print_case_info(case):
    severity_colors = {"high": "red", "medium": "yellow", "low": "green"}
    sev_color = severity_colors.get(case.severity.value, "white")

    table = Table(title="🔍 Case Classification", box=box.ROUNDED)
    table.add_column("Field", style="cyan")
    table.add_column("Value")

    table.add_row("Case ID", f"[bold]{case.case_id}[/bold]")
    table.add_row("Type", case.case_type.value.upper())
    table.add_row("Severity", f"[{sev_color}]{case.severity.value.upper()}[/{sev_color}]")
    console.print(table)


@app.command()
def investigate(
    repo_path: str = typer.Argument(..., help="Path to the target repository to investigate"),
    policy_dir: str = typer.Option("policies", help="Path to policy documents directory"),
    template_dir: str = typer.Option("templates", help="Path to report template directory"),
    log_dir: str = typer.Option("logs", help="Path to audit log directory"),
    max_retries: int = typer.Option(2, help="Maximum patch retry attempts before escalation"),
    agent: str = typer.Option(None, "--agent", "-a", help="AI backend: lmstudio | bob | ollama | openai | groq"),
    model: str = typer.Option(None, "--model", "-m", help="Model name (e.g. prism-bonsai-27b, bob-2.0, gpt-4o)"),
    agent_url: str = typer.Option(None, "--agent-url", help="Override the backend API URL"),
    non_interactive: bool = typer.Option(False, "--non-interactive", help="Skip human approval prompt (for CI/CD use)"),
):
    """⚖️  Investigate a repository for functional regressions and policy violations."""

    # Resolve backend/model for display (reads .env if not set via CLI)
    import os
    from dotenv import load_dotenv
    load_dotenv()
    display_backend = agent or os.getenv("AGENT_BACKEND", "lmstudio")
    display_model = model or os.getenv("AGENT_MODEL", "prism-bonsai-27b")

    print_banner(display_backend, display_model)
    console.print()

    # ── Health check the AI agent ──────────────────────────────────────────
    console.print(f"[dim]🔌 Connecting to {display_backend.upper()} ({display_model})...[/dim]")
    tribunal = GovernanceTribunal(
        repo_path=repo_path,
        policy_dir=policy_dir,
        template_dir=template_dir,
        log_dir=log_dir,
        max_retries=max_retries,
        agent_backend=agent,
        agent_model=model,
        agent_url=agent_url,
    )

    if tribunal.agent.health_check():
        console.print(f"[green]✅ {display_backend.upper()} is online — {display_model} ready.[/green]\n")
    else:
        console.print(
            f"[yellow]⚠️  {display_backend.upper()} is not reachable at "
            f"{tribunal.agent.config.base_url}\n"
            f"   Continuing with scripted fallback patch...[/yellow]\n"
        )

    # ── Phase 1: Collect Evidence ──────────────────────────────────────────
    console.print("[bold yellow]📋 Phase 1: Collecting Evidence (The Subpoena)...[/bold yellow]")
    evidence = tribunal.collect_evidence()
    print_evidence_table(evidence)
    console.print()

    # ── Phase 2: Classify Case ─────────────────────────────────────────────
    console.print("[bold yellow]🔍 Phase 2: Classifying Case...[/bold yellow]")
    case = tribunal.classify(evidence)
    print_case_info(case)
    console.print()

    if case.case_type.value == "unknown":
        console.print(Panel(
            "[green]✅ No defects detected. The codebase is clean.[/green]",
            title="VERDICT", border_style="green",
        ))
        return

    # ── Phase 3: AI Investigates & Remediates ─────────────────────────────
    console.print(f"[bold yellow]⚖️  Phase 3: {display_backend.upper()} ({display_model}) Investigating...[/bold yellow]")
    console.print("[dim]  Running agentic loop: investigate → patch → validate → iterate[/dim]\n")

    result = tribunal.run_remediation_loop(case)

    # ── Phase 4: Generate Tribunal Docket ─────────────────────────────────
    console.print("[bold yellow]📄 Phase 4: Generating Tribunal Docket...[/bold yellow]")
    docket = tribunal.generate_docket(case, result)
    console.print()

    console.print(Panel(
        docket,
        title="⚖️  TRIBUNAL DOCKET",
        border_style="bold red",
        box=box.DOUBLE,
    ))
    console.print()

    # ── Phase 5: Human Approval Gate ──────────────────────────────────────
    console.print("[bold yellow]👤 Phase 5: Human Approval Required[/bold yellow]")
    console.print(f"  Confidence Score: [bold]{case.confidence_score}[/bold]")
    console.print(f"  Severity: [bold]{case.severity.value.upper()}[/bold]")
    console.print(f"  AI Engine: [cyan]{display_backend.upper()} / {display_model}[/cyan]")
    console.print()

    if non_interactive:
        approved = result.get("verdict", "").startswith("GUILTY")
        status = "AUTO-APPROVED (CI mode)" if approved else "AUTO-REJECTED (remediation failed)"
        console.print(Panel(f"[bold yellow]🤖 {status}[/bold yellow]", border_style="yellow"))
    else:
        approved = typer.confirm("Do you approve this remediation?")
        if approved:
            console.print(Panel(
                "[bold green]✅ VERDICT APPROVED\nPatch accepted. Case closed.[/bold green]",
                border_style="green",
            ))
        else:
            console.print(Panel(
                "[bold red]❌ VERDICT REJECTED\nPatch discarded. Escalating to human engineer.[/bold red]",
                border_style="red",
            ))

    tribunal.save_audit_log(case, result, approved)
    console.print(f"\n[dim]Audit log saved to: logs/{case.case_id}_full.json[/dim]")
    console.print(f"[dim]Docket saved to:    logs/{case.case_id}_docket.md[/dim]")


@app.command()
def backends():
    """📋 List all supported AI backends and their default endpoints."""
    table = Table(title="Supported AI Backends", box=box.ROUNDED)
    table.add_column("Backend", style="cyan")
    table.add_column("Default URL", style="dim")
    table.add_column("Example Model")

    examples = {
        "lmstudio": "prism-bonsai-27b  (or any model loaded in LM Studio)",
        "ollama":   "llama3.1  (run: ollama pull llama3.1)",
        "bob":      "bob-2.0",
        "openai":   "gpt-4o",
        "groq":     "llama3-70b-8192",
        "custom":   "any-model-name",
    }

    for backend, url in list_supported_backends().items():
        table.add_row(backend, url or "(set AGENT_BASE_URL)", examples.get(backend, ""))

    console.print(table)
    console.print("\n[dim]Configure via .env or CLI flags --agent / --model / --agent-url[/dim]")


if __name__ == "__main__":
    app()
