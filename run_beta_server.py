"""
MCP ASDK Studio v0.9-4 | Professional Beta Server Hub
Auto-Launch Version (Target: Chrome / Web Mode)

This script provides a unified diagnostic gateway and automatically launches the 
Web Preview Mode in Chrome unless interrupted.
"""

import os
import sys
import subprocess
import time
import json
import logging
import threading
import http.server
import socketserver
import webbrowser
from pathlib import Path

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("beta_server.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("ASDK.BetaHub")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class ASDKVisualServer(http.server.SimpleHTTPRequestHandler):
    def log_message(self, format, *args):
        logger.debug("Web request: " + (format % args))

def start_local_server(port=8080, directory="."):
    """Spins up a lightweight HTTP server in a separate thread."""
    os.chdir(directory)
    handler = ASDKVisualServer
    with socketserver.TCPServer(("", port), handler) as httpd:
        logger.info(f"[SERVER] Active at http://localhost:{port}")
        httpd.serve_forever()

def check_environment():
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
            
    settings_path = root / "user_data" / "profiles" / "default.json"
    if settings_path.exists():
        try:
            with open(settings_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                logger.info(f"[PASS] Settings Loaded: {data.get('model', 'Unknown')}")
        except Exception as e:
            logger.error(f"[FAIL] Settings Corrupted: {e}")
            all_pass = False
    return all_pass

def launch_web():
    logger.info("--- Launching Web Mode (Chrome/Auto) ---")
    server_thread = threading.Thread(
        target=start_local_server, 
        args=(8080, str(Path(__file__).parent)),
        daemon=True
    )
    server_thread.start()
    time.sleep(1)
    
    try:
        url = "http://localhost:8080/docs/index.html"
        webbrowser.open(url)
        logger.info(f"[SUCCESS] Browser launched at {url}")
        print("\n[!] Web Server is RUNNING. Press Ctrl+C to stop.")
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Server shut down.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[ERROR] Launch failed: {e}")

def main():
    clear_screen()
    print("====================================================")
    print("   MCP ASDK Studio v0.9-4 | GLOBAL BETA SERVER HUB")
    print("   Auto-Launch Target: Chrome / Web Mode")
    print("====================================================\n")
    
    if not check_environment():
        print("\n[!] CRITICAL: Environment check fails. Check logs.")
        input("Press Enter to bypass, or Ctrl+C to abort...")

    print("\n[EXECUTION]")
    print("1. Web Server Mode (Default - AUTO-LAUNCHING in 3s)")
    print("2. Desktop App Mode (pywebview)")
    print("3. Exit")

    # Countdown Logic
    import msvcrt
    print(f"\nASDK-HUB >> Starting Chrome Preview... (Press '2' for Desktop, '3' to Exit)", end="", flush=True)
    
    cmd = None
    start_time = time.time()
    while time.time() - start_time < 3.0:
        if msvcrt.kbhit():
            cmd = msvcrt.getch().decode('utf-8')
            break
        time.sleep(0.1)

    if cmd is None or cmd == '' or cmd == '1':
        launch_web()
    elif cmd == '2':
        logger.info("Switching to Desktop Mode...")
        subprocess.Popen([sys.executable, "main.py"])
        logger.info("Desktop process started.")
    elif cmd == '3':
        sys.exit(0)
    else:
        launch_web()

if __name__ == "__main__":
    main()
