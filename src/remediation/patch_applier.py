import os
import subprocess
from datetime import datetime


class PatchApplier:
    def __init__(self, repo_path: str):
        self.repo_path = os.path.abspath(repo_path)

    def create_isolated_branch(self, base_branch: str = "main") -> str:
        branch_name = f"bob/fix-{datetime.now().strftime('%Y%m%d-%H%M%S')}"
        try:
            subprocess.run(
                ["git", "checkout", "-b", branch_name],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
                check=True,
            )
            return branch_name
        except Exception:
            return ""

    def apply_patch(self, patch_content: str, target_file: str = None) -> bool:
        patch_file = os.path.join(self.repo_path, ".bob_temp.patch")
        try:
            with open(patch_file, "w", encoding="utf-8") as f:
                f.write(patch_content)

            # Dry run check
            check = subprocess.run(
                ["git", "apply", "--check", patch_file],
                cwd=self.repo_path,
                capture_output=True,
                text=True,
            )
            if check.returncode == 0:
                apply_res = subprocess.run(
                    ["git", "apply", patch_file],
                    cwd=self.repo_path,
                    capture_output=True,
                    text=True,
                )
                if apply_res.returncode == 0:
                    return True
        except Exception:
            pass
        finally:
            if os.path.exists(patch_file):
                os.remove(patch_file)

        return False

    def rollback(self, branch_name: str, base_branch: str = "main"):
        if not branch_name:
            return
        try:
            subprocess.run(["git", "checkout", base_branch], cwd=self.repo_path, capture_output=True)
            subprocess.run(["git", "branch", "-D", branch_name], cwd=self.repo_path, capture_output=True)
        except Exception:
            pass
