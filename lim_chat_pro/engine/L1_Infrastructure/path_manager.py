from pathlib import Path
import os
import sys

class PathManager:
    """
    중앙 집중식 경로 관리자 (Centralized Path Manager) - MCP ASDK Studio v1 전용
    """
    
    # ----------------------------------------------------------------
    # 1. 기준점 잡기 (Project Root Calculation)
    # ----------------------------------------------------------------
    _FILE_PATH = Path(__file__).resolve()
    SRC_ROOT = _FILE_PATH.parent.parent # engine/
    PACKAGE_ROOT = SRC_ROOT.parent      # lim_chat_pro/
    PROJECT_ROOT = PACKAGE_ROOT.parent  # mcp_asdk_studio_v1/ (전체 저장소 루트)
    
    # ----------------------------------------------------------------
    # 2. 주요 장소 정의 (Key Directory Definitions)
    # ----------------------------------------------------------------
    USER_DATA_ROOT = PROJECT_ROOT / "user_data" 
    
    CONFIG_DIR = USER_DATA_ROOT / "configs"
    HISTORY_DIR = USER_DATA_ROOT / "history"
    PROFILE_DIR = USER_DATA_ROOT / "profiles"
    PROMPT_DIR = USER_DATA_ROOT / "prompts"
    
    SERVER_BUNDLE_DIR = PROJECT_ROOT / "servers"
    MCP_CONFIG_DIR = USER_DATA_ROOT / "mcp"
    
    L5_UI_DIR = SRC_ROOT / "L5_Presentation"

    @classmethod
    def get_config_file(cls, filename="config_asdk_studio_v1.json"):
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CONFIG_DIR / filename
        
    @classmethod
    def get_history_dir(cls):
        cls.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        return cls.HISTORY_DIR
        
    @classmethod
    def get_profile_dir(cls):
        cls.PROFILE_DIR.mkdir(parents=True, exist_ok=True)
        return cls.PROFILE_DIR
        
    @classmethod
    def get_server_dir(cls):
        cls.MCP_CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.MCP_CONFIG_DIR
        
    @classmethod
    def get_prompt_dir(cls):
        cls.PROMPT_DIR.mkdir(parents=True, exist_ok=True)
        return cls.PROMPT_DIR
    
    @classmethod
    def get_ui_path(cls, filename="index_pro.html"):
        return cls.L5_UI_DIR / filename

    @classmethod
    def add_src_to_sys_path(cls):
        if str(cls.SRC_ROOT) not in sys.path:
            sys.path.append(str(cls.SRC_ROOT))
