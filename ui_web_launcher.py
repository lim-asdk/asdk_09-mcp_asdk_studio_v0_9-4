"""Public web launcher for the legacy studio.

Original entry point: run_beta_server.py
This wrapper keeps the browser launcher easy to discover from the repository
root while leaving the actual server logic untouched.
"""

import sys
from pathlib import Path


def _bootstrap_repo_root() -> Path:
    """Add the repository root to sys.path so the web hub can import the engine."""
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def main() -> None:
    _bootstrap_repo_root()

    try:
        print("==========================================================")
        print("   MCP ASDK STUDIO v0.9-5 | WEB LAUNCHER")
        print("   Mode: Web Hub (HTTP Port 2026)")
        print("==========================================================\n")

        # Original browser/web entry point lives in run_beta_server.py.
        from run_beta_server import start_hub

        start_hub()
    except Exception as exc:
        print(f"Error launching Web version: {exc}")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
