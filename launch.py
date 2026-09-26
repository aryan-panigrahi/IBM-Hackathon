"""
The Governance Tribunal — Cross-Platform Launcher
==================================================
Called by launch.command (Mac) and launch.bat (Windows).
Handles: Python check, venv setup, dependency install, agent health, then launches the CLI.
"""

import os
import sys
import subprocess
import platform
import shutil
from pathlib import Path

# ── Colours (works on Mac terminal and Windows 10+ cmd/powershell) ────────────
class C:
    RED    = "\033[91m"
    GREEN  = "\033[92m"
    YELLOW = "\033[93m"
    CYAN   = "\033[96m"
    BOLD   = "\033[1m"
    DIM    = "\033[2m"
    RESET  = "\033[0m"

IS_WINDOWS = platform.system() == "Windows"

def banner():
    print(f"""
{C.RED}{C.BOLD}
  ⚖️  ══════════════════════════════════════════ ⚖️
       THE GOVERNANCE TRIBUNAL
       Forensic Compliance & Regression Arbiter
       Powered by IBM Bob 2.0 / LM Studio / Ollama
  ⚖️  ══════════════════════════════════════════ ⚖️
{C.RESET}""")

def step(msg: str):
    print(f"{C.CYAN}{C.BOLD}▶  {msg}{C.RESET}")

def ok(msg: str):
    print(f"{C.GREEN}   ✅ {msg}{C.RESET}")

def warn(msg: str):
    print(f"{C.YELLOW}   ⚠️  {msg}{C.RESET}")

def fail(msg: str):
    print(f"{C.RED}   ❌ {msg}{C.RESET}")

def separator():
    print(f"{C.DIM}{'─' * 56}{C.RESET}")


def check_python():
    step("Checking Python version...")
    v = sys.version_info
    if v.major < 3 or (v.major == 3 and v.minor < 8):
        fail(f"Python 3.8+ required. You have {v.major}.{v.minor}.")
        fail("Download from: https://www.python.org/downloads/")
        input("\nPress Enter to exit...")
        sys.exit(1)
    ok(f"Python {v.major}.{v.minor}.{v.micro}")


def setup_venv(root: Path):
    step("Setting up virtual environment...")
    venv_path = root / "venv"

    if IS_WINDOWS:
        python_bin = venv_path / "Scripts" / "python.exe"
        pip_bin    = venv_path / "Scripts" / "pip.exe"
    else:
        python_bin = venv_path / "bin" / "python"
        pip_bin    = venv_path / "bin" / "pip"

    if not venv_path.exists():
        warn("No venv found — creating one (one-time setup, ~30 seconds)...")
        subprocess.run([sys.executable, "-m", "venv", str(venv_path)], check=True)
        ok("Virtual environment created.")
    else:
        ok("Virtual environment already exists.")

    return python_bin, pip_bin


def install_deps(root: Path, pip_bin: Path):
    step("Checking dependencies...")
    req_file = root / "requirements.txt"

    # Quick check: if openai importable, deps are likely already installed
    result = subprocess.run(
        [str(pip_bin), "show", "openai"],
        capture_output=True, text=True
    )
    if result.returncode == 0:
        ok("All dependencies already installed.")
        return

    warn("Installing dependencies (first run only, ~1-2 minutes)...")
    subprocess.run(
        [str(pip_bin), "install", "-r", str(req_file), "--quiet"],
        check=True
    )
    ok("Dependencies installed.")


def check_env(root: Path):
    step("Checking .env configuration...")
    env_file = root / ".env"
    example_file = root / ".env.example"

    if not env_file.exists():
        warn(".env not found — copying from .env.example")
        shutil.copy(str(example_file), str(env_file))
        warn("Edit .env to set your AGENT_BACKEND and AGENT_MODEL if needed.")
    else:
        ok(".env found.")

    # Read and display current agent config
    backend = "lmstudio"
    model   = "prism-bonsai-27b"
    try:
        with open(env_file) as f:
            for line in f:
                line = line.strip()
                if line.startswith("AGENT_BACKEND="):
                    backend = line.split("=", 1)[1].strip()
                if line.startswith("AGENT_MODEL="):
                    model = line.split("=", 1)[1].strip()
    except Exception:
        pass

    print(f"{C.DIM}   Agent backend : {backend}{C.RESET}")
    print(f"{C.DIM}   Agent model   : {model}{C.RESET}")
    return backend, model


def check_agent(python_bin: Path, backend: str, model: str):
    step(f"Checking {backend.upper()} connection ({model})...")

    check_script = """
import sys
sys.path.insert(0, '.')
from src.agent.factory import create_agent
try:
    agent = create_agent()
    result = agent.health_check()
    print('online' if result else 'offline')
except Exception as e:
    print('offline')
"""
    result = subprocess.run(
        [str(python_bin), "-c", check_script],
        capture_output=True, text=True,
        cwd=str(python_bin.parent.parent.parent)  # repo root
    )
    status = result.stdout.strip()

    if status == "online":
        ok(f"{backend.upper()} is online and ready.")
        return True
    else:
        warn(f"{backend.upper()} is not reachable.")
        if backend == "lmstudio":
            warn("→ Open LM Studio and click 'Start Server' (port 1234)")
            warn(f"→ Make sure '{model}' is loaded")
        elif backend == "bob":
            warn("→ Make sure IBM Bob 2.0 is running")
        elif backend == "ollama":
            warn("→ Run: ollama serve")
            warn(f"→ Then: ollama pull {model}")
        warn("The system will use scripted fallback patch if agent stays offline.")
        return False


def pick_target(root: Path):
    separator()
    print(f"\n{C.BOLD}Which repository do you want to investigate?{C.RESET}")
    print(f"  {C.CYAN}1{C.RESET}  demo_repo  (built-in demo with 3 intentional defects)")
    print(f"  {C.CYAN}2{C.RESET}  Enter a custom path")
    print()

    choice = input("Enter 1 or 2 [default: 1]: ").strip() or "1"

    if choice == "2":
        custom = input("Enter the full path to your repository: ").strip()
        if not Path(custom).exists():
            fail(f"Path does not exist: {custom}")
            input("Press Enter to exit...")
            sys.exit(1)
        return custom
    else:
        demo = root / "demo_repo"
        ok(f"Using demo_repo: {demo}")
        return str(demo)


def pick_agent_override():
    separator()
    print(f"\n{C.BOLD}Agent override (press Enter to use .env defaults):{C.RESET}")
    print(f"  {C.CYAN}1{C.RESET}  Use .env defaults")
    print(f"  {C.CYAN}2{C.RESET}  LM Studio  (localhost:1234)")
    print(f"  {C.CYAN}3{C.RESET}  IBM Bob 2.0")
    print(f"  {C.CYAN}4{C.RESET}  Ollama     (localhost:11434)")
    print(f"  {C.CYAN}5{C.RESET}  OpenAI     (needs API key in .env)")
    print(f"  {C.CYAN}6{C.RESET}  Custom URL")
    print()

    choice = input("Enter 1-6 [default: 1]: ").strip() or "1"

    map_ = {
        "1": (None, None, None),
        "2": ("lmstudio", None, None),
        "3": ("bob", "bob-2.0", None),
        "4": ("ollama", None, None),
        "5": ("openai", None, None),
        "6": ("custom", None, None),
    }

    backend, model, url = map_.get(choice, (None, None, None))

    if choice == "4":
        model = input("  Ollama model name [llama3.1]: ").strip() or "llama3.1"
    elif choice == "2":
        model = input("  LM Studio model name [prism-bonsai-27b]: ").strip() or "prism-bonsai-27b"
    elif choice == "6":
        url   = input("  Full API URL (e.g. http://localhost:5000/v1): ").strip()
        model = input("  Model name: ").strip()

    return backend, model, url


def launch_tribunal(python_bin: Path, repo_root: Path, target: str, backend, model, url):
    separator()
    print(f"\n{C.RED}{C.BOLD}🚀 Launching The Governance Tribunal...{C.RESET}\n")

    cmd = [str(python_bin), "cli.py", "investigate", target]
    if backend:
        cmd += ["--agent", backend]
    if model:
        cmd += ["--model", model]
    if url:
        cmd += ["--agent-url", url]

    subprocess.run(cmd, cwd=str(repo_root))


def main():
    # Enable ANSI colours on Windows
    if IS_WINDOWS:
        os.system("color")
        os.system("")

    # Find repo root (this script lives in the root)
    root = Path(__file__).resolve().parent

    banner()
    separator()

    check_python()
    python_bin, pip_bin = setup_venv(root)
    install_deps(root, pip_bin)
    backend, model = check_env(root)
    check_agent(python_bin, backend, model)

    separator()
    target = pick_target(root)
    agent_b, agent_m, agent_url = pick_agent_override()

    launch_tribunal(python_bin, root, target, agent_b, agent_m, agent_url)

    separator()
    print(f"\n{C.GREEN}{C.BOLD}✅ Tribunal session complete.{C.RESET}")
    print(f"{C.DIM}Audit logs saved in: {root / 'logs'}{C.RESET}\n")

    if IS_WINDOWS:
        input("Press Enter to close...")


if __name__ == "__main__":
    main()
