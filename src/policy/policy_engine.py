import os
import re
try:
    import yaml
    YAML_AVAILABLE = True
except ImportError:
    YAML_AVAILABLE = False


class PolicyEngine:
    def __init__(self, policy_file: str = "policies/policies.yaml"):
        self.policy_file = policy_file
        self.rules = self.load_rules()

    def load_rules(self) -> list:
        if not os.path.exists(self.policy_file):
            return [
                {
                    "id": "POL-GDPR-01",
                    "description": "User email addresses must not be logged in plaintext.",
                    "severity": "HIGH",
                    "pattern": r"logger\.info\(.*user\.email",
                },
                {
                    "id": "SEC-001",
                    "description": "API keys and secrets must not be hardcoded.",
                    "severity": "HIGH",
                    "pattern": r'API_KEY\s*=\s*["\']sk-[^"\']+["\']',
                },
            ]

        if YAML_AVAILABLE:
            try:
                with open(self.policy_file, "r", encoding="utf-8") as f:
                    data = yaml.safe_load(f)
                    return data.get("rules", [])
            except Exception:
                pass
        return []

    def evaluate_file(self, file_path: str) -> list:
        violations = []
        if not os.path.exists(file_path):
            return violations
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()

            for rule in self.rules:
                pattern = rule.get("pattern", "")
                if pattern and re.search(pattern, content):
                    violations.append({
                        "id": rule.get("id"),
                        "description": rule.get("description"),
                        "severity": rule.get("severity"),
                        "file": file_path,
                    })
        except Exception:
            pass
        return violations
