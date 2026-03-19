"""
MCP ASDK Studio v0.9-4 | Full-Stack Beta Server Hub
Target: Browser-Based Studio Studio (Sync with main.py)

This script provides a 100% functional Web version of the Studio.
It bridges Browser Fetch calls to the real Python ProBridgeAPI.
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

# --- GLOBAL LOGGING ---
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("beta_server.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("ASDK.FullStackHub")

# --- DYNAMIC IMPORTS FOR L3 ORCHESTRATION ---
# Ensure we can find the project modules
sys.path.append(os.getcwd())
try:
    from lim_chat_pro.engine.L3_Orchestration.pro_bridge_api import ProBridgeAPI
except ImportError as e:
    logger.error(f"[FATAL] Cannot import ProBridgeAPI: {e}")
    sys.exit(1)

# Instance of the REAL bridge used in main.py
BRIDGE = ProBridgeAPI()

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

class ASDKFunctionalBridge(http.server.SimpleHTTPRequestHandler):
    """
    Acts as both a static file server and an API proxy for ProBridgeAPI.
    """
    def do_POST(self):
        if self.path == '/api/call':
            try:
                content_length = int(self.headers['Content-Length'])
                post_data = self.rfile.read(content_length)
                data = json.loads(post_data.decode('utf-8'))
                
                method_name = data.get('method')
                args = data.get('args', [])
                
                logger.info(f"[API CLOUD] Call: {method_name}({args})")
                
                # Dynamic dispatch to ProBridgeAPI
                if hasattr(BRIDGE, method_name):
                    method = getattr(BRIDGE, method_name)
                    result = method(*args)
                    
                    self._send_json_response({"status": "success", "result": result})
                else:
                    self._send_json_response({"status": "error", "message": f"Method {method_name} not found"}, 404)
            except Exception as e:
                logger.error(f"[API ERROR] {e}")
                self._send_json_response({"status": "error", "message": str(e)}, 500)
        else:
            self.send_error(404)

    def _send_json_response(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        # Keep terminal clean from generic GET requests
        logger.debug("Server request: " + (format % args))

def start_hub_server(port=8080, directory="."):
    os.chdir(directory)
    socketserver.TCPServer.allow_reuse_address = True
    with socketserver.TCPServer(("", port), ASDKFunctionalBridge) as httpd:
        logger.info(f"[HUB] Studio Server active at http://localhost:{port}")
        httpd.serve_forever()

def check_structure():
    logger.info("--- Phase 1: Environment Integrity Check ---")
    root = Path(__file__).parent.absolute()
    required = ["user_data", "lim_chat_pro/engine/L5_Presentation/index_pro.html"]
    
    for item in required:
        if not (root / item).exists():
            logger.error(f"[FAIL] Missing: {item}")
            return False
        logger.info(f"[PASS] Essential Found: {item}")
    return True

def launch_web_studio():
    """Starts the Hub and opens the Functional Studio in Chrome."""
    logger.info("--- Launching Full-Stack Studio in Browser ---")
    
    app_root = Path(__file__).parent.absolute()
    
    server_thread = threading.Thread(
        target=start_hub_server, 
        args=(8080, str(app_root)),
        daemon=True
    )
    server_thread.start()
    
    time.sleep(1.5)
    
    try:
        url = "http://localhost:8080/lim_chat_pro/engine/L5_Presentation/index_pro.html"
        webbrowser.open(url)
        logger.info(f"[SUCCESS] Studio opened in Browser at {url}")
        print("\n" + "!"*50)
        print("  FULL-STACK HUB ACTIVE")
        print("  Mode: 100% Functional Sync (main.py <-> Browser)")
        print("!"*50)
        print("\n[!] Press Ctrl+C to terminate.")
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Hub terminated.")
        sys.exit(0)

def main():
    clear_screen()
    print("====================================================")
    print("   MCP ASDK STUDIO v0.9-4 | FULL-STACK HUB")
    print("   Status: Operational Sync with Browser")
    print("====================================================\n")
    
    if not check_structure():
        print("\n[!] CRITICAL ERROR: Structure corrupted.")
        sys.exit(1)

    print("\n[AUTO-LAUNCH SEQUENCE]")
    print("> Target: Browser-Based Studio Studio (100% Functional)")
    print("> Bridge: Dynamic REST Proxy to ProBridgeAPI")
    print("> Desktop mode (2) available during countdown...")

    # countdown
    import msvcrt
    cmd = None
    start_time = time.time()
    while time.time() - start_time < 3.0:
        if msvcrt.kbhit():
            cmd = msvcrt.getch().decode('utf-8')
            break
        time.sleep(0.1)

    if cmd == '2':
        logger.info("Launching Desktop version...")
        subprocess.Popen([sys.executable, "main.py"])
    else:
        launch_web_studio()

if __name__ == "__main__":
    main()
