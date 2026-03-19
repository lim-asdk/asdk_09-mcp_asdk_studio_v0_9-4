from pathlib import Path
import os
import sys

class PathManager:
    """
    Centralized Path Manager for MCP ASDK Studio v1.
    Standardized according to [V5-D-01] Directive.
    """
    
    def __init__(self, project_root=None):
        # 1. Determine Project Root
        if project_root:
            self.PROJECT_ROOT = Path(project_root).absolute()
        else:
            # Default: 4 levels up from this file
            self.PROJECT_ROOT = Path(__file__).parent.parent.parent.parent.absolute()
        
        # 2. Load .env
        self.env = self._load_env()
        
        # 3. Core Directory Pointers (Generalization)
        # Allows overriding via .env for different environments
        self.DATA_ROOT = Path(self.env.get("DATA_ROOT", self.PROJECT_ROOT / "user_data"))
        self.KEYS_ROOT = Path(self.env.get("KEYS_ROOT", self.PROJECT_ROOT / "keys"))
        self.LOG_ROOT = Path(self.env.get("LOG_ROOT", self.DATA_ROOT / "logs"))
        
        # 4. Engine & UI Paths (L1..L5 Alignment)
        self.ENGINE_ROOT = self.PROJECT_ROOT / "lim_chat_pro" / "engine"
        self.UI_ROOT = self.ENGINE_ROOT / "L5_Presentation"
        
        # 5. Logical Sub-dirs
        self.CONFIG_DIR = self.DATA_ROOT / "configs"
        self.HISTORY_DIR = self.DATA_ROOT / "history"
        self.PROFILE_DIR = self.DATA_ROOT / "profiles"
        self.PROMPT_DIR = self.DATA_ROOT / "prompts"
        self.MCP_DATA_DIR = self.DATA_ROOT / "mcp"
        
        self.SERVER_BUNDLE_DIR = self.PROJECT_ROOT / "servers"

        # Initialize folders
        self._ensure_essential_dirs()

    def _load_env(self):
        env = {}
        env_path = self.PROJECT_ROOT / ".env"
        if env_path.exists():
            try:
                with open(env_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            name, value = line.split('=', 1)
                            env[name.strip()] = value.strip()
            except Exception:
                pass
        return env

    def _ensure_essential_dirs(self):
        dirs = [
            self.DATA_ROOT, self.KEYS_ROOT, self.LOG_ROOT,
            self.CONFIG_DIR, self.HISTORY_DIR, self.PROFILE_DIR, self.MCP_DATA_DIR
        ]
        for d in dirs:
            d.mkdir(parents=True, exist_ok=True)

    # --- Directory Getters ---
    def get_profiles_dir(self): return self.PROFILE_DIR
    def get_history_dir(self): return self.HISTORY_DIR
    def get_configs_dir(self): return self.CONFIG_DIR
    def get_keys_dir(self): return self.KEYS_ROOT
    def get_logs_dir(self): return self.LOG_ROOT
    def get_mcp_data_dir(self): return self.MCP_DATA_DIR

    def get_mcp_config_path(self, filename="mcp_config.json"):
        return self.MCP_DATA_DIR / filename

    def get_ui_path(self, filename="index_pro.html"):
        return self.UI_ROOT / filename

    def add_engine_to_sys_path(self):
        if str(self.ENGINE_ROOT) not in sys.path:
            sys.path.insert(0, str(self.ENGINE_ROOT))
        if str(self.PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(self.PROJECT_ROOT))
