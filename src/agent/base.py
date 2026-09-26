"""
Agent Backend Base Class
========================
All AI backends (LM Studio, Bob 2.0, OpenAI, Ollama, etc.) implement this interface.
The Tribunal doesn't care which model is running — it just calls .investigate().
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Optional


@dataclass
class AgentConfig:
    """Universal config for any AI backend."""
    backend: str          # "lmstudio" | "bob" | "openai" | "ollama" | "anthropic"
    model: str            # e.g. "prism-bonsai-27b", "gpt-4o", "llama3"
    base_url: str         # API endpoint
    api_key: str = "none" # "none" for local models
    temperature: float = 0.1
    max_tokens: int = 4096
    timeout: int = 120


@dataclass
class InvestigationResult:
    """Structured output from the AI agent's investigation."""
    root_cause: str
    patch_hunks: list          # List of {file, original_snippet, fixed_snippet}
    patch_description: str
    parole_conditions: list    # Guardrails the model recommends
    residual_risks: str
    confidence_explanation: str
    raw_response: str = ""


class AgentBackend(ABC):
    """Abstract base — every AI backend must implement these two methods."""

    def __init__(self, config: AgentConfig):
        self.config = config

    @abstractmethod
    def investigate(self, evidence: dict, policies: dict) -> InvestigationResult:
        """
        Given collected evidence + policy docs, return a full investigation result
        including root cause analysis and code patches.
        """
        pass

    @abstractmethod
    def health_check(self) -> bool:
        """Returns True if the backend is reachable and responding."""
        pass

    def _build_system_prompt(self) -> str:
        return """You are the Forensic Compliance Arbiter for The Governance Tribunal — a senior DevSecOps engineer with 20 years of experience.

Your job is to investigate code defects and policy violations, generate surgical patches, and produce structured JSON reports.

RULES:
1. Always respond with valid JSON only — no markdown, no prose outside the JSON.
2. Be surgical — fix only what is broken, preserve everything else.
3. Patches must be minimal and targeted — do not refactor unrelated code.
4. Every fix must address BOTH functional AND policy violations simultaneously.
5. Confidence must be honest — if you are unsure, say so.

OUTPUT FORMAT (strict JSON):
{
  "root_cause": "One sentence description of what caused the failure",
  "patch_hunks": [
    {
      "file": "relative/path/to/file.py",
      "original_snippet": "exact lines to replace (3-5 lines of context)",
      "fixed_snippet": "replacement lines"
    }
  ],
  "patch_description": "Human-readable summary of all changes made",
  "parole_conditions": [
    "Guardrail or regression test added",
    "Another condition..."
  ],
  "residual_risks": "Any remaining risks or None",
  "confidence_explanation": "Why you are confident (or not) in this fix"
}"""

    def _build_user_prompt(self, evidence: dict, policies: dict) -> str:
        import json

        failures = evidence.get("test_results", {}).get("failures", [])
        secrets = evidence.get("secret_scan", {}).get("findings", {})
        pii = evidence.get("pii_scan", {}).get("findings", [])
        recent_commits = evidence.get("recent_commits", [])

        prompt_parts = ["## EVIDENCE COLLECTED BY THE TRIBUNAL\n"]

        if failures:
            prompt_parts.append("### FAILING TESTS:")
            for f in failures:
                prompt_parts.append(f"- Test: {f.get('test_id')}")
                prompt_parts.append(f"  File: {f.get('file')}, Line: {f.get('line')}")
                prompt_parts.append(f"  Error: {f.get('message')}")
                if f.get('longrepr'):
                    prompt_parts.append(f"  Detail: {f.get('longrepr')[:500]}")

        if secrets:
            prompt_parts.append("\n### HARDCODED SECRETS DETECTED:")
            for path, issues in secrets.items():
                prompt_parts.append(f"- File: {path}")
                for issue in (issues if isinstance(issues, list) else [issues]):
                    prompt_parts.append(f"  Line {issue.get('line_number', '?')}: {issue.get('line', '?')}")

        if pii:
            prompt_parts.append("\n### PII VIOLATIONS IN LOGS:")
            for p in pii:
                prompt_parts.append(f"- File: {p.get('file')}, Line: {p.get('line')}: {p.get('content')}")

        if recent_commits:
            prompt_parts.append("\n### RECENT COMMITS (root cause candidates):")
            for c in recent_commits[:3]:
                prompt_parts.append(f"- [{c.get('sha')}] {c.get('author')}: {c.get('message')}")

        if policies:
            prompt_parts.append("\n### ACTIVE POLICY RULES:")
            for name, content in list(policies.items())[:2]:
                prompt_parts.append(f"--- {name} ---")
                prompt_parts.append(content[:800])

        prompt_parts.append("\n## SOURCE FILES TO PATCH")
        prompt_parts.append("Read the failing test messages and policy violations above.")
        prompt_parts.append("Now provide your investigation result as strict JSON.")

        return "\n".join(prompt_parts)
