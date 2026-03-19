import os
import sys
import json
import logging
from pathlib import Path

# Setup simple logger
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')
logger = logging.getLogger("HealthCheck")

def check_environment():
    logger.info("--- [L1] Infrastructure Check ---")
    from lim_chat_pro.engine.L1_Infrastructure.path_manager import PathManager
    pm = PathManager()
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
    if pm.get_profiles_dir().exists():
        logger.info(f"[OK] Profiles directory found: {pm.get_profiles_dir()}")
    else:
        logger.error("[ERROR] Profiles directory missing!")

def check_dependencies():
    logger.info("\n--- [L2] Dependency Check ---")
    try:
        import webview
        logger.info(f"[OK] pywebview is installed (Version: {webview.__version__})")
    except ImportError:
        logger.error("[ERROR] pywebview is NOT installed. Run 'pip install pywebview'")

def check_mcp_config():
    logger.info("\n--- [L3] MCP Connectivity Check ---")
    config_path = Path(__file__).parent / "user_data" / "mcp_config.json"
    if config_path.exists():
        try:
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
                logger.info(f"[OK] Found mcp_config.json with {len(config.get('mcpServers', {}))} servers.")
        except Exception as e:
            logger.error(f"[ERROR] Failed to parse mcp_config.json: {e}")
    else:
        logger.info("[INFO] No mcp_config.json found. System will run in standalone mode.")

if __name__ == "__main__":
    logger.info("=== MCP ASDK Studio v1 Health Diagnostics ===\n")
    check_environment()
    check_dependencies()
    check_mcp_config()
    logger.info("\n=== Diagnostics Complete ===")
