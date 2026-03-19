"""
MCP ASDK Studio v0.9-4 | Professional Global Hub
Standardized via V5 Intelligence Matrix

FUNCTION: Unified Beta Server & Launcher
TARGET: Desktop (Main) & Browser (Sub-system)
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

# PORT CONFIGURATION (Professional/Uncommon Port)
PORT = 2026

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [%(levelname)s] %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler("beta_server.log", mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger("ASDK.GlobalHub")

# Setup project path for module discovery
sys.path.append(os.getcwd())
try:
    from lim_chat_pro.engine.L3_Orchestration.pro_bridge_api import ProBridgeAPI
except ImportError as e:
    logger.error(f"[FATAL] ProBridgeAPI import failed: {e}")
    sys.exit(1)

BRIDGE = ProBridgeAPI()

def kill_existing_port(port):
    """
    Ensures the port is free for immediate restart by killing 
    the previous owner process (Windows optimized).
    """
    if os.name == 'nt':
        try:
            # Find PID using the port
            cmd = f'powershell -Command "Get-NetTCPConnection -LocalPort {port} -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess"'
            result = subprocess.check_output(cmd, shell=True).decode().strip()
            if result:
                pids = result.split()
                for pid in pids:
                    logger.info(f"[PORT] Killing previous hub process (PID: {pid})...")
                    os.system(f"taskkill /F /PID {pid} >nul 2>&1")
                time.sleep(0.5)
        except Exception as e:
            logger.debug(f"Port cleanup skipped: {e}")

class ASDKFunctionalHub(http.server.SimpleHTTPRequestHandler):
    """Functional REST Proxy for Browser-to-Python interaction."""
    def do_POST(self):
        if self.path == '/api/call':
            try:
                content_length = int(self.headers['Content-Length'])
                data = json.loads(self.rfile.read(content_length).decode())
                
                method_name = data.get('method')
                args = data.get('args', [])
                
                if hasattr(BRIDGE, method_name):
                    res = getattr(BRIDGE, method_name)(*args)
                    self._send_json({"status": "success", "result": res})
                else:
                    self._send_json({"status": "error", "message": "Method not found"}, 404)
            except Exception as e:
                self._send_json({"status": "error", "message": str(e)}, 500)

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        pass # Suppress noisy logs

def start_hub():
    """Diagnostic & Launch Sequence"""
    os.chdir(Path(__file__).parent.absolute())
    clear_screen()
    
    print("==========================================================")
    print(f"   MCP ASDK STUDIO v0.9-4 | ENHANCED GLOBAL HUB")
    print(f"   Target: Desktop & Browser Sync (Port: {PORT})")
    print("==========================================================\n")
    
    # 1. Port Cleanup
    kill_existing_port(PORT)
    
    # 2. Diagnostics
    required = ["user_data", "lim_chat_pro/engine/L5_Presentation/index_pro.html"]
    for item in required:
        if not Path(item).exists():
            logger.error(f"[FAIL] Missing {item}")
            sys.exit(1)
            
    # 3. Mode Choice & Auto-Launch
    print("[RUNNING DIAGNOSTICS... DONE]")
    print(f"\n> Auto-launching Browser Mode in 3s... (Default)")
    print("> (Press '1' for Desktop Mode instead)")
    
    import msvcrt
    cmd = None
    start_time = time.time()
    while time.time() - start_time < 3.0:
        if msvcrt.kbhit():
            cmd = msvcrt.getch().decode('utf-8')
            break
        time.sleep(0.1)

    if cmd == '1':
        logger.info("Executing Desktop Experience...")
        subprocess.Popen([sys.executable, "main.py"])
        return

    # Start Server for Browser Mode
    logger.info("Starting Hub Server for Browser Mode...")
    server_thread = threading.Thread(
        target=lambda: socketserver.TCPServer(("", PORT), ASDKFunctionalHub).serve_forever(),
        daemon=True
    )
    server_thread.start()
    
    time.sleep(1)
    url = f"http://localhost:{PORT}/lim_chat_pro/engine/L5_Presentation/index_pro.html"
    webbrowser.open(url)
    logger.info(f"[SUCCESS] Hub ready at {url}")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Hub Closed.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    start_hub()
