"""
MCP ASDK Studio v0.9-4 | Professional Beta Server Hub
Auto-Launch Version (Target: Chrome / Full App UI)

This script bridges the Python backend logic to a standard web browser,
allowing index_pro.html to function outside of the pywebview container.
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

class ASDKAppServer(http.server.SimpleHTTPRequestHandler):
    """
    Handles static files for the App UI and provides a basic 
    API endpoint for Browser-to-Python communication.
    """
    def do_POST(self):
        # Placeholder for future REST API integration with ProBridgeAPI
        if self.path == '/api/call':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            logger.info(f"[API] Browser Call Received: {post_data.decode('utf-8')}")
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"status": "ok", "message": "Python received your command"}).encode())
        else:
            self.send_error(404)

    def log_message(self, format, *args):
        logger.debug("App Server request: " + (format % args))

def start_app_server(port=8080, directory="."):
    """Spins up the App UI server."""
    os.chdir(directory)
    handler = ASDKAppServer
    # Allow address reuse to prevent 'port in use' errors
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), handler) as httpd:
        logger.info(f"[SERVER] App UI Bridge active at http://localhost:{port}")
        httpd.serve_forever()

def check_environment():
    logger.info("--- Phase 1: Environment Integrity Check ---")
    root = Path(__file__).parent.absolute()
    required = ["user_data", "lim_chat_pro", "lim_chat_pro/engine/L5_Presentation/index_pro.html"]
    
    all_pass = True
    for item in required:
        if (root / item).exists():
            logger.info(f"[PASS] Essential Found: {item}")
        else:
            logger.warning(f"[FAIL] MISSING: {item}")
            all_pass = False
    return all_pass

def launch_web_app():
    """Starts the server and opens the ACTUAL App UI in Chrome."""
    logger.info("--- Launching App in Browser (Chrome/Auto) ---")
    
    # Target directory is the Presentation layer for L5 assets
    app_root = Path(__file__).parent.absolute()
    
    server_thread = threading.Thread(
        target=start_app_server, 
        args=(8080, str(app_root)),
        daemon=True
    )
    server_thread.start()
    time.sleep(1)
    
    try:
        # POINT TO THE REAL APP UI, NOT THE LANDING PAGE
        url = "http://localhost:8080/lim_chat_pro/engine/L5_Presentation/index_pro.html"
        webbrowser.open(url)
        logger.info(f"[SUCCESS] App UI launched in Browser at {url}")
        print("\n" + "="*50)
        print("  SERVER MODE ACTIVE")
        print("  Logic Bridge: Enabled (Experimental)")
        print("  Target UI: index_pro.html")
        print("="*50)
        print("\n[!] Press Ctrl+C to terminate the server hub.")
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Hub shut down.")
        sys.exit(0)
    except Exception as e:
        logger.error(f"[ERROR] Launch failed: {e}")

def main():
    clear_screen()
    print("====================================================")
    print("   MCP ASDK Studio v0.9-4 | BETA SERVER HUB")
    print("   Target: Integrated App Experience (Chrome)")
    print("====================================================\n")
    
    if not check_environment():
        print("\n[!] CRITICAL: Structure check fails. Check logs.")
        input("Press Enter to bypass, or Ctrl+C to abort...")

    print("\n[SELECT MODE]")
    print("1. Launch App in Browser (Default - AUTO in 3s)")
    print("2. Launch Native Desktop (pywebview)")
    print("3. Exit")

    import msvcrt
    print(f"\nASDK-HUB >> Starting App Server... (Press '2' for Desktop)", end="", flush=True)
    
    cmd = None
    start_time = time.time()
    while time.time() - start_time < 3.0:
        if msvcrt.kbhit():
            cmd = msvcrt.getch().decode('utf-8')
            break
        time.sleep(0.1)

    if cmd is None or cmd == '' or cmd == '1':
        launch_web_app()
    elif cmd == '2':
        logger.info("Starting Desktop...")
        subprocess.Popen([sys.executable, "main.py"])
    elif cmd == '3':
        sys.exit(0)
    else:
        launch_web_app()

if __name__ == "__main__":
    main()
