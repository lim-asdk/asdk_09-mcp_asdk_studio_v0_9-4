"""
MCP ASDK Studio v0.9-5 | Ultra-Fast Beta Server Hub (V5 Async Edition)
Standardized via V5 Intelligence Matrix

FUNCTION: Unified Beta Server & Launcher (Asynchronous Boot)
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

# PORT CONFIGURATION
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

# Global Bridge Placeholder
BRIDGE = None

# --- DYNAMIC IMPORTS & RUNTIME SETUP ---
def setup_paths():
    """Matches main.py logic for consistent path resolution."""
    current_path = Path(__file__).resolve()
    found_root = None
    for i in range(5):
        parent = current_path.parents[i]
        if (parent / "lim_chat_pro").exists():
            found_root = parent
            break
    if not found_root:
        found_root = Path(__file__).resolve().parent

    project_root = found_root
    package_dir = project_root / "lim_chat_pro"
    
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    engine_dir = package_dir / "engine"          
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))
    return project_root

ROOT_PATH = setup_paths()
os.chdir(ROOT_PATH) # Ensure working directory is root

# Now import engine components
from lim_chat_pro import get_available_packs
from L1_Infrastructure.path_manager import PathManager

def kill_existing_port(port):
    """Ultra-fast port cleaning."""
    if os.name == 'nt':
        try:
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if output:
                for line in output.split('\n'):
                    parts = line.split()
                    if parts and len(parts) > 4:
                        pid = parts[-1]
                        if pid != '0':
                            logger.info(f"[PORT] Releasing port {port} (PID: {pid})...")
                            os.system(f"taskkill /F /PID {pid} >nul 2>&1")
                time.sleep(0.1)
        except Exception:
            pass

class ASDKFunctionalHub(http.server.SimpleHTTPRequestHandler):
    """Functional REST Proxy for Browser-to-Python interaction."""
    
    def do_POST(self):
        if self.path == '/api/call':
            if BRIDGE is None:
                self._send_json({"status": "error", "message": "Bridge is initializing... Please wait."}, 503)
                return
            try:
                content_length = int(self.headers['Content-Length'])
                raw_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(raw_data)
                
                method_name = data.get('method')
                args = data.get('args', [])
                
                if hasattr(BRIDGE, method_name):
                    method = getattr(BRIDGE, method_name)
                    result = method(*args) if isinstance(args, list) else method(args)
                    self._send_json({"status": "success", "result": result})
                else:
                    self._send_json({"status": "error", "message": f"Method {method_name} not found"}, 404)
            except Exception as e:
                logger.error(f"[HUB API] Crash: {str(e)}")
                self._send_json({"status": "error", "message": str(e)}, 500)
        else:
            self.send_error(404)

    def _send_json(self, data, code=200):
        try:
            self.send_response(code)
            self.send_header('Content-Type', 'application/json')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            self.wfile.write(json.dumps(data).encode('utf-8'))
        except Exception:
            pass

    def log_message(self, format, *args):
        pass # Silence HTTP logs

def start_hub():
    """Ultra-fast Launch Sequence (SLA < 2s for UI)"""
    os.chdir(ROOT_PATH)
    os.system('cls' if os.name == 'nt' else 'clear')
    
    print("==========================================================")
    print(f"   MCP ASDK STUDIO v0.9-5 | ULTRA-FAST ASYNC HUB")
    print(f"   Status: High-Speed Boot Sequence Initialized")
    print("==========================================================\n")
    
    # 1. Immediate Port Cleanup & Server Thread Start
    kill_existing_port(PORT)
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("", PORT), ASDKFunctionalHub)
        threading.Thread(target=httpd.serve_forever, daemon=True).start()
        logger.info(f"[BOOT] Web Server active on Port {PORT}")
    except Exception as e:
        logger.error(f"[FATAL] Server start failed: {e}")
        sys.exit(1)

    # 2. Immediate Browser Launch (Visual confirmation within seconds)
    url = f"http://localhost:{PORT}/lim_chat_pro/engine/L5_Presentation/index_pro.html"
    logger.info(f"[BOOT] Launching Browser immediately...")
    webbrowser.open(url)
    
    # 3. Background Bridge Activation (Heavy Lifting)
    def activate_bridge_async():
        global BRIDGE
        try:
            logger.info("[ASYNC] Loading L3 Orchestration Bridge...")
            
            # --- Pack Selection (Sync with main.py) ---
            packs = get_available_packs()
            active_pack = None
            if "stock_pro" in packs:
                active_pack = "stock_pro"
            elif packs:
                active_pack = packs[0]
                
            if active_pack:
                logger.info(f"[BOOT] Activating Intelligence Pack: {active_pack}")
                PathManager.set_active_pack(active_pack)
            else:
                logger.info("[BOOT] No IQ-Pack found. Using default mode.")
            # ------------------------------------------

            # Late-import to avoid boot delay
            from L3_Orchestration.pro_bridge_api import ProBridgeAPI
            BRIDGE = ProBridgeAPI()
            logger.info("[SUCCESS] Bridge Active. All MCP Servers Synced.")
        except Exception as e:
            logger.error(f"[FATAL] Bridge Activation Failed: {e}")

    threading.Thread(target=activate_bridge_async, daemon=True).start()
    
    print(f"\n> UI is opening at {url}")
    print("> The engine is warming up in the background...")
    print("> (Press Ctrl+C to shut down)\n")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Hub Shut Down.")

if __name__ == "__main__":
    start_hub()
