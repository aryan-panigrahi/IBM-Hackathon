"""The Governance Tribunal — CLI Entry Point.

Usage:
    python cli.py investigate ./demo_repo
    python cli.py investigate ./demo_repo --max-retries 3
"""

import sys
from pathlib import Path

# Add project root to path
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

app = typer.Typer(
    name="tribunal",
    help="🏛️ The Governance Tribunal — Forensic Compliance & Regression Arbiter",
    add_completion=False,
)
console = Console()


def print_banner():
    """Display the Tribunal banner."""
    banner = Text()
    banner.append("⚖️  THE GOVERNANCE TRIBUNAL  ⚖️\n", style="bold red")
    banner.append("Forensic Compliance & Regression Arbiter\n", style="dim")
    banner.append("Powered by IBM Bob 2.0", style="italic cyan")
    console.print(Panel(banner, border_style="red", box=box.DOUBLE))


def print_evidence_table(evidence: dict):
    """Display collected evidence in a Rich table."""
    table = Table(title="📋 Evidence Summary", box=box.ROUNDED)
    table.add_column("Check", style="cyan")
    table.add_column("Status", justify="center")
    table.add_column("Details", style="dim")

    # Test results
    tests = evidence["test_results"]
    status = "✅ PASS" if tests["passed"] else "❌ FAIL"
    details = f"{tests.get('failed_count', 0)} failures"
    table.add_row("Functional Tests", status, details)

    # Secret scan
    secrets = evidence["secret_scan"]
    status = "✅ CLEAN" if secrets["passed"] else "🚨 SECRETS FOUND"
    count = sum(len(v) for v in secrets.get("findings", {}).values())
    table.add_row("Secret Scan", status, f"{count} findings")

    # PII scan
    pii = evidence["pii_scan"]
    status = "✅ CLEAN" if pii["passed"] else "🚨 PII DETECTED"
    table.add_row("PII Scan", status, f"{len(pii.get('findings', []))} findings")

    # Policies
    policies = evidence["policies"]
    table.add_row("Policies Loaded", "📄", ", ".join(policies.keys()))

    console.print(table)


def print_case_info(case):
    """Display case classification."""
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
    repo_path: str = typer.Argument(
        ..., help="Path to the target repository to investigate"
    ),
    policy_dir: str = typer.Option(
        "policies", help="Path to policy documents directory"
    ),
    template_dir: str = typer.Option(
        "templates", help="Path to report template directory"
    ),
    log_dir: str = typer.Option(
        "logs", help="Path to audit log directory"
    ),
    max_retries: int = typer.Option(
        2, help="Maximum patch retry attempts before escalation"
    ),
):
    """🏛️ Investigate a repository for functional regressions and policy violations."""
    print_banner()
    console.print()

    # Initialize tribunal
    tribunal = GovernanceTribunal(
        repo_path=repo_path,
        policy_dir=policy_dir,
        template_dir=template_dir,
        log_dir=log_dir,
        max_retries=max_retries,
    )

    # ── Phase 1: Collect Evidence ──
    console.print("[bold yellow]📋 Phase 1: Collecting Evidence (The Subpoena)...[/bold yellow]")
    evidence = tribunal.collect_evidence()
    print_evidence_table(evidence)
    console.print()

    # ── Phase 2: Classify Case ──
    console.print("[bold yellow]🔍 Phase 2: Classifying Case...[/bold yellow]")
    case = tribunal.classify(evidence)
    print_case_info(case)
    console.print()

    # Check if there's anything to investigate
    if case.case_type.value == "unknown":
        console.print(Panel(
            "[green]✅ No defects detected. The codebase is clean.[/green]",
            title="VERDICT", border_style="green",
        ))
        return

    # ── Phase 3-5: Investigation & Remediation Loop ──
    console.print("[bold yellow]⚖️  Phase 3: Bob Investigating & Remediating...[/bold yellow]")
    console.print("[dim]  Running agentic loop: investigate → patch → validate → iterate[/dim]")
    console.print()

    result = tribunal.run_remediation_loop(case)

    # ── Phase 6: Generate Tribunal Docket ──
    console.print("[bold yellow]📄 Phase 4: Generating Tribunal Docket...[/bold yellow]")
    docket = tribunal.generate_docket(case, result)
    console.print()

    # Display the Docket
    console.print(Panel(
        docket,
        title="⚖️  TRIBUNAL DOCKET",
        border_style="bold red",
        box=box.DOUBLE,
    ))
    console.print()

    # ── Phase 7: Human Approval Gate ──
    console.print("[bold yellow]👤 Phase 5: Human Approval Required[/bold yellow]")
    console.print(f"  Confidence Score: [bold]{case.confidence_score}[/bold]")
    console.print(f"  Severity: [bold]{case.severity.value.upper()}[/bold]")
    console.print()

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

    # Save audit log
    tribunal.save_audit_log(case, result, approved)
    console.print(f"\n[dim]Audit log saved to: logs/{case.case_id}_full.json[/dim]")
    console.print(f"[dim]Docket saved to: logs/{case.case_id}_docket.md[/dim]")


if __name__ == "__main__":
    app()
