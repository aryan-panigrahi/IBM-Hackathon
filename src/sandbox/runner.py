import os
import subprocess


class SandboxRunner:
    """Execute code & validation securely."""

    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def run_in_docker(self, command: str) -> dict:
        """Run command in a locked-down container with no network."""
        docker_cmd = [
            "docker", "run", "--rm",
            "--network", "none",
            "--memory", "512m",
            "--cpus", "1.0",
            "-v", f"{self.repo_path}:/app:ro",
            "-w", "/app",
            "python:3.11-slim",
            "sh", "-c", command,
        ]
        try:
            res = subprocess.run(docker_cmd, capture_output=True, text=True, timeout=90)
            return {"success": res.returncode == 0, "stdout": res.stdout, "stderr": res.stderr}
        except Exception as e:
            return {"success": False, "error": str(e)}

    def run_local_isolated(self, command_list: list, cwd: str = None) -> dict:
        """Run locally in repository environment."""
        target_cwd = cwd or self.repo_path
        try:
            res = subprocess.run(command_list, capture_output=True, text=True, cwd=target_cwd, timeout=60)
            return {
                "success": res.returncode == 0,
                "stdout": res.stdout,
                "stderr": res.stderr,
                "returncode": res.returncode,
            }
        except Exception as e:
            return {"success": False, "error": str(e)}
