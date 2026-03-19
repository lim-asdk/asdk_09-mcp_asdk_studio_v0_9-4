import os, sys
from pathlib import Path

# Add project root to path
root = Path(r"C:\program_files\Lim Workspace\mcp_asdk_studio_v1")
sys.path.append(str(root))
sys.path.append(str(root / "lim_chat_pro" / "engine"))

try:
    print("Testing ProBridgeAPI import...")
    from lim_chat_pro.engine.L3_Orchestration.pro_bridge_api import ProBridgeAPI
    print("Initializing BRIDGE...")
    BRIDGE = ProBridgeAPI()
    print("SUCCESS: BRIDGE initialized.")
except Exception as e:
    import traceback
    traceback.print_exc()
