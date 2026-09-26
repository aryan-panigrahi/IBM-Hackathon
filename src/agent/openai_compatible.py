"""
OpenAI-Compatible Backend
==========================
Works with ANY service that exposes an OpenAI-compatible /v1/chat/completions endpoint:

  - LM Studio       → http://localhost:1234/v1         (Prism Bonsai 27B, Llama, etc.)
  - Ollama          → http://localhost:11434/v1
  - IBM Bob 2.0     → http://localhost:11435/v1  (Bob's local API)
  - OpenAI          → https://api.openai.com/v1
  - Azure OpenAI    → https://your-resource.openai.azure.com/
  - Groq            → https://api.groq.com/openai/v1
  - Together AI     → https://api.together.xyz/v1

Just change AGENT_BASE_URL and AGENT_MODEL in your .env file.
"""

import json
import re
from openai import OpenAI, APIConnectionError, APITimeoutError

from src.agent.base import AgentBackend, AgentConfig, InvestigationResult


class OpenAICompatibleBackend(AgentBackend):
    """Universal adapter for any OpenAI-compatible AI backend."""

    def __init__(self, config: AgentConfig):
        super().__init__(config)
        self.client = OpenAI(
            base_url=config.base_url,
            api_key=config.api_key,
            timeout=config.timeout,
        )

    def health_check(self) -> bool:
        """Ping the models endpoint to verify the server is running."""
        try:
            models = self.client.models.list()
            return True
        except Exception:
            return False

    def investigate(self, evidence: dict, policies: dict) -> InvestigationResult:
        """Send evidence to the model and get a structured investigation back."""
        system_prompt = self._build_system_prompt()
        user_prompt = self._build_user_prompt(evidence, policies)

        # Also inject the actual source files so the model can see the code
        source_context = self._load_source_files(evidence)
        if source_context:
            user_prompt += f"\n\n### ACTUAL SOURCE CODE:\n{source_context}"

        try:
            response = self.client.chat.completions.create(
                model=self.config.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.config.temperature,
                max_tokens=self.config.max_tokens,
            )

            raw = response.choices[0].message.content.strip()
            return self._parse_response(raw)

        except APIConnectionError:
            raise ConnectionError(
                f"Cannot reach {self.config.backend} at {self.config.base_url}\n"
                f"→ Make sure LM Studio / your server is running and the model is loaded."
            )
        except APITimeoutError:
            raise TimeoutError(
                f"Model timed out after {self.config.timeout}s. "
                f"Try a smaller model or increase AGENT_TIMEOUT in .env"
            )

    def _load_source_files(self, evidence: dict) -> str:
        """Read and include the actual source files from the repo."""
        import os
        repo_path = evidence.get("_repo_path", ".")
        result_parts = []

        target_files = []

        # Add files from failing tests
        for f in evidence.get("test_results", {}).get("failures", []):
            fp = f.get("file", "")
            if fp:
                target_files.append(fp)

        # Add files from secret scan
        for path in evidence.get("secret_scan", {}).get("findings", {}).keys():
            target_files.append(path)

        # Add files from PII scan
        for f in evidence.get("pii_scan", {}).get("findings", []):
            target_files.append(f.get("file", ""))

        # Deduplicate and read
        seen = set()
        for fpath in target_files:
            if not fpath or fpath in seen:
                continue
            seen.add(fpath)
            full_path = fpath if os.path.isabs(fpath) else os.path.join(repo_path, fpath)
            if os.path.exists(full_path):
                try:
                    with open(full_path, "r", encoding="utf-8") as f:
                        content = f.read()
                    rel = os.path.relpath(full_path, repo_path)
                    result_parts.append(f"```python\n# FILE: {rel}\n{content}\n```")
                except Exception:
                    pass

        return "\n\n".join(result_parts)

    def _parse_response(self, raw: str) -> InvestigationResult:
        """Parse the model's JSON response into a structured result."""
        # Strip markdown code fences if model wraps in them
        cleaned = re.sub(r"^```(?:json)?\s*", "", raw, flags=re.MULTILINE)
        cleaned = re.sub(r"\s*```$", "", cleaned, flags=re.MULTILINE)
        cleaned = cleaned.strip()

        # Find the JSON object
        json_match = re.search(r"\{.*\}", cleaned, re.DOTALL)
        if json_match:
            cleaned = json_match.group(0)

        try:
            data = json.loads(cleaned)
        except json.JSONDecodeError:
            # Model didn't return valid JSON — wrap the raw text as the root cause
            return InvestigationResult(
                root_cause=raw[:500] if raw else "Model returned no parseable response.",
                patch_hunks=[],
                patch_description="Model response was not valid JSON. Manual review required.",
                parole_conditions=[],
                residual_risks="Full manual review required.",
                confidence_explanation="Low — JSON parse failed.",
                raw_response=raw,
            )

        return InvestigationResult(
            root_cause=data.get("root_cause", "Unknown root cause."),
            patch_hunks=data.get("patch_hunks", []),
            patch_description=data.get("patch_description", ""),
            parole_conditions=data.get("parole_conditions", []),
            residual_risks=data.get("residual_risks", "None identified."),
            confidence_explanation=data.get("confidence_explanation", ""),
            raw_response=raw,
        )
