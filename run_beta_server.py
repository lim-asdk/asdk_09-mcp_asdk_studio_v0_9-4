"""
MCP ASDK Studio v0.9-4 | Ultra-Fast Beta Server Hub
Standardized via V5 Intelligence Matrix

FUNCTION: Unified Beta Server & Launcher (Speed Optimized)
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

# Setup project path for module discovery
sys.path.append(os.getcwd())
try:
    from lim_chat_pro.engine.L3_Orchestration.pro_bridge_api import ProBridgeAPI
except ImportError as e:
    logger.error(f"[FATAL] ProBridgeAPI import failed: {e}")
    sys.exit(1)

# Initialize the bridge
BRIDGE = ProBridgeAPI()

def kill_existing_port(port):
    """
    Ultra-fast port cleaning using native netstat.
    Solves 'address already in use' instantly.
    """
    if os.name == 'nt':
        try:
            # High-speed PID lookup
            cmd = f'netstat -ano | findstr :{port}'
            output = subprocess.check_output(cmd, shell=True).decode().strip()
            if output:
                # Get the last column (PID) from the first line matching the port
                lines = output.split('\n')
                for line in lines:
                    parts = line.split()
                    if parts and len(parts) > 4:
                        pid = parts[-1]
                        if pid != '0':
                            logger.info(f"[PORT] Releasing port {port} (PID: {pid})...")
                            os.system(f"taskkill /F /PID {pid} >nul 2>&1")
                time.sleep(0.1) # Minimum stabilization
        except Exception as e:
            logger.debug(f"Fast-kill skipped: {e}")

class ASDKFunctionalHub(http.server.SimpleHTTPRequestHandler):
    """Functional REST Proxy for Browser-to-Python interaction."""
    def do_POST(self):
        if self.path == '/api/call':
            try:
                content_length = int(self.headers['Content-Length'])
                raw_data = self.rfile.read(content_length).decode('utf-8')
                data = json.loads(raw_data)
                
                method_name = data.get('method')
                args = data.get('args', [])
                
                logger.debug(f"[HUB API] Calling: {method_name}")
                
                if hasattr(BRIDGE, method_name):
                    method = getattr(BRIDGE, method_name)
                    # Handle both sync and async-style calls if needed 
                    # (ProBridgeAPI is generally sync for JS calls)
                    result = method(*args) if isinstance(args, list) else method(args)
                    self._send_json({"status": "success", "result": result})
                else:
                    logger.warning(f"[HUB API] Method not found: {method_name}")
                    self._send_json({"status": "error", "message": f"Method {method_name} not found"}, 404)
            except Exception as e:
                logger.error(f"[HUB API] Crash: {str(e)}")
                self._send_json({"status": "error", "message": f"Server Crash: {str(e)}"}, 500)
        else:
            self.send_error(404)

    def _send_json(self, data, code=200):
        self.send_response(code)
        self.send_header('Content-Type', 'application/json')
        self.send_header('Access-Control-Allow-Origin', '*')
        self.end_headers()
        self.wfile.write(json.dumps(data).encode('utf-8'))

    def log_message(self, format, *args):
        pass # Suppress noisy logs

def start_hub():
    """Ultra-fast Launch Sequence"""
    os.chdir(Path(__file__).parent.absolute())
    clear_screen()
    
    print("==========================================================")
    print(f"   MCP ASDK STUDIO v0.9-4 | ULTRA-FAST HUB")
    print(f"   Target: Professional Browser Experience (Port: {PORT})")
    print("==========================================================\n")
    
    # 1. Fast Port Cleanup
    kill_existing_port(PORT)
    
    # 2. Structure Verification (Cached-like Speed)
    required = ["user_data", "lim_chat_pro/engine/L5_Presentation/index_pro.html"]
    for item in required:
        if not Path(item).exists():
            logger.error(f"[FAIL] Missing {item}")
            sys.exit(1)
            
    # 3. Mode Choice & High-Speed Auto-Launch
    print("[DIAGNOSTICS... OK]")
    print(f"\n> Auto-launching Web Studio in 0.7s...")
    print("> (Press '1' for Desktop Mode, '3' for Docs)")
    
    import msvcrt
    cmd = None
    start_time = time.time()
    # Reduced delay for snappier feel
    while time.time() - start_time < 0.7:
        if msvcrt.kbhit():
            cmd = msvcrt.getch().decode('utf-8')
            break
        time.sleep(0.02)

    if cmd == '1':
        logger.info("Starting Desktop...")
        subprocess.Popen([sys.executable, "main.py"])
        return
    elif cmd == '3':
        logger.info("Opening Documentation...")
        webbrowser.open("http://localhost:2026/docs/index.html")
        # Need to start server anyway
    
    # Start Functional Server
    logger.info("Activating L3 Hub Bridge...")
    socketserver.TCPServer.allow_reuse_address = True
    try:
        httpd = socketserver.TCPServer(("", PORT), ASDKFunctionalHub)
        server_thread = threading.Thread(target=httpd.serve_forever, daemon=True)
        server_thread.start()
    except Exception as e:
        logger.error(f"[FATAL] Server start failed: {e}")
        sys.exit(1)
    
    # Smallest possible stabilization
    time.sleep(0.2)
    url = f"http://localhost:{PORT}/lim_chat_pro/engine/L5_Presentation/index_pro.html"
    webbrowser.open(url)
    logger.info(f"[SUCCESS] Web Studio Hub is Live at {url}")
    
    try:
        while True: time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Hub Shut Down.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear')

if __name__ == "__main__":
    start_hub()
