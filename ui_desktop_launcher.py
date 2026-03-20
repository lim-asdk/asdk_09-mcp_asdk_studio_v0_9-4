"""Public desktop launcher for the legacy studio.

Original entry point: main.py
Keep this file tiny so humans and AI assistants can find the launch path
without digging through the engine code.
"""

import sys
from pathlib import Path


def _bootstrap_repo_root() -> Path:
    """Add the repository root to sys.path so main.py can import engine modules."""
    root = Path(__file__).resolve().parent
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    return root


def main() -> None:
    _bootstrap_repo_root()

    try:
        print("==========================================================")
        print("   MCP ASDK STUDIO v0.9-5 | DESKTOP LAUNCHER")
        print("   Mode: Standard Desktop (Native Window)")
        print("==========================================================\n")

        # Original desktop entry point lives in main.py.
        from main import main as studio_main

        studio_main()
    except Exception as exc:
        print(f"Error launching Desktop version: {exc}")
        input("\nPress Enter to exit...")


if __name__ == "__main__":
    main()
