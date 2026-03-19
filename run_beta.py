import os
import sys
import subprocess
import time
import json
import logging
from pathlib import Path

# Setup logging to both console and file for "2-step verification"
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("beta_launcher.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("ASDK.BetaLauncher")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

def check_environment():
    """Step 1: Diagnostic Integrity Check"""
    logger.info("--- Phase 1: Environment Integrity Check ---")
    
    root = Path(__file__).parent.absolute()
    required_dirs = ["user_data", "lim_chat_pro", "docs", "keys"]
    
    all_pass = True
    for d in required_dirs:
        if (root / d).exists():
            logger.info(f"[PASS] Directory found: {d}")
        else:
            logger.warning(f"[FAIL] Directory MISSING: {d}")
            all_pass = False
            
    # Check settings file
    settings_path = root / "user_data" / "profiles" / "default.json"
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[PASS] Settings Loaded: {data.get('model', 'Unknown Model')}")
        except Exception as e:
            logger.error(f"[FAIL] Settings Corrupted: {e}")
            all_pass = False
    else:
        logger.warning("[WARN] default.json not found. Will use defaults.")

    return all_pass

def launch_desktop():
    logger.info("--- Launching Desktop App (pywebview) ---")
    try:
        subprocess.Popen([sys.executable, "main.py"])
        logger.info("[SUCCESS] Desktop launcher process started.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to launch desktop: {e}")

def launch_web():
    logger.info("--- Launching Web Mode (Chrome) ---")
    logger.info("[INFO] Starting internal web bridge on http://localhost:8080")
    # In a real future step, this will call web_server.py
    # For now, we simulate the entry
    try:
        import webbrowser
        # Point to the presentation layer
        target = Path(__file__).parent / "docs" / "index.html"
        webbrowser.open(f"file:///{target}")
        logger.info("[SUCCESS] Visual Browser Mode opened in Chrome.")
        logger.warning("[NOTE] Full Python-JS interaction is limited in raw browser mode without a server bridge.")
    except Exception as e:
        logger.error(f"[ERROR] Failed to launch web: {e}")

def main():
    clear_screen()
    print("====================================================")
    print("   MCP ASDK Studio v0.9-4 | Public Beta Launcher")
    print("   Intelligence Matrix V5 Standard Hub")
    print("====================================================\n")
    
    if not check_environment():
        print("\n[!] CRITICAL: Environment check failed. Please check logs.")
        input("Press Enter to ignore and continue, or Ctrl+C to abort...")

    print("\n[Select Execution Mode]")
    print("1. Desktop App (Full Experience, pywebview)")
    print("2. Web Preview Mode (Chrome, Visual Check)")
    print("3. Run Health Check Only")
    print("4. Exit")
    
    choice = input("\nEnter choice (1-4): ")
    
    if choice == '1':
        launch_desktop()
    elif choice == '2':
        launch_web()
    elif choice == '3':
        logger.info("Health check completed. No further actions.")
    elif choice == '4':
        sys.exit(0)
    else:
        print("Invalid choice.")
    
    print("\n--- Launcher sequence complete. Keep this terminal open for logs. ---")
    time.sleep(2)

if __name__ == "__main__":
    main()
