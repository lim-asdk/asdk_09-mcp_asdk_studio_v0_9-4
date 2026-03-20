import os
import sys
import json
import logging
import socket
import urllib.request
import urllib.error
from pathlib import Path

# Setup simple logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("HealthCheck")

def check_environment():
    logger.info("--- [L1] Infrastructure Check ---")
    try:
        from lim_chat_pro.engine.L1_Infrastructure.path_manager import PathManager
        pm = PathManager
        logger.info(f"Project Root: {pm.PROJECT_ROOT}")
        logger.info(f"Data Root: {pm.DATA_ROOT}")
        
        # Check essential folders
        essential_dirs = ["user_data", "lim_chat_pro", "docs", "keys"]
        for d in essential_dirs:
            if (pm.PROJECT_ROOT / d).exists():
                logger.info(f"[OK] Found directory: {d}")
            else:
                logger.warning(f"[MISSING] Directory not found: {d}")

        # Check for profiles
        profile_dir = pm.get_profile_dir()
        if profile_dir.exists():
            logger.info(f"[OK] Profiles directory found: {profile_dir}")
        else:
            logger.error("[ERROR] Profiles directory missing!")
    except Exception as e:
        logger.error(f"[ERROR] Infrastructure check failed: {e}")

def check_dependencies():
    logger.info("\n--- [L2] Dependency Check ---")
    try:
        import webview
        logger.info("[OK] pywebview is installed.")
    except ImportError:
        logger.error("[ERROR] pywebview is NOT installed. Run 'pip install pywebview'")

def check_mcp_config():
    logger.info("\n--- [L3] MCP Connectivity Check ---")
    try:
        from lim_chat_pro.engine.L1_Infrastructure.path_manager import PathManager
        server_dir = PathManager.get_server_dir()
        if server_dir.exists():
            server_files = list(server_dir.glob("*.json"))
            logger.info(f"[OK] Found {len(server_files)} server configuration files in {server_dir}")
            for f in server_files:
                logger.info(f"  - {f.name}")
        else:
            logger.warning(f"[MISSING] Server directory not found: {server_dir}")
            
        # Also check root config as a fallback/reference
        config_path = PathManager.PROJECT_ROOT / "mcp_config.json"
        if config_path.exists():
            logger.info(f"[INFO] Reference mcp_config.json found in project root.")
    except Exception as e:
        logger.error(f"[ERROR] MCP config check failed: {e}")

def check_web_server():
    logger.info("\n--- [L4] Web Server Check ---")
    # Check if port 2026 is open
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(1)
        try:
            s.connect(("localhost", 2026))
            logger.info("[OK] Web Server (Port 2026) is active.")
            return True
        except (ConnectionRefusedError, socket.timeout):
            logger.warning("[OFFLINE] Web Server (Port 2026) is not running.")
            return False
        except Exception as e:
            logger.error(f"[ERROR] Port check failed: {e}")
            return False

def check_bridge_sync():
    logger.info("\n--- [L5] ProBridgeAPI Sync Check ---")
    url = "http://localhost:2026/api/call"
    payload = json.dumps({"method": "get_server_status", "args": []}).encode("utf-8")
    req = urllib.request.Request(url, data=payload, headers={'Content-Type': 'application/json'})
    
    try:
        with urllib.request.urlopen(req, timeout=2) as response:
            result = json.loads(response.read().decode())
            if result.get("status") == "success":
                bridge_status = result.get("result", [])
                logger.info(f"[OK] ProBridgeAPI is active via Web Hub.")
                logger.info(f"[INFO] Connected MCP Servers: {len(bridge_status)}")
                for s in bridge_status:
                    logger.info(f"  - {s['name']}: {s['status']} ({s['tools']} tools)")
            else:
                logger.error(f"[ERROR] Bridge API returned error: {result.get('message')}")
    except (urllib.error.URLError, socket.timeout) as e:
        logger.warning(f"[OFFLINE] Could not connect to Bridge API: {e}")
    except Exception as e:
        logger.error(f"[ERROR] Sync check failed: {e}")

if __name__ == "__main__":
    logger.info("=== MCP ASDK Studio v0.9-4 (Public Beta) Health Diagnostics ===\n")
    check_environment()
    check_dependencies()
    check_mcp_config()
    server_up = check_web_server()
    if server_up:
        check_bridge_sync()
    logger.info("\n=== Diagnostics Complete ===")
