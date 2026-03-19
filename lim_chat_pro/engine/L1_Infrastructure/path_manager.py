# Project: lim_chat_v2_0
# Developer: lim_hwa_chan
# Version: 2.0 (Pro Interface Sync)

"""
[PATH_MANAGER.PY] - 프로그램 길라잡이 (내비게이션)
-----------------------------------------------------------
이 파일은 프로그램 내에서 파일들이 어디에 있는지 찾아주는 '내비게이션' 역할을 합니다.
V2.0 규격으로 업데이트되어 지능 팩(IQ-Packs)과 사용자의 데이터를 완벽히 구분합니다.

작성자: lim_hwa_chan (Updated for ASDK Studio v1)
-----------------------------------------------------------
"""

from pathlib import Path
import os
import sys

class PathManager:
    """
    중앙 집중식 경로 관리자 (V2.0 Production Standard)
    """
    
    # 1. 기준점 잡기 (Project Root Calculation)
    # 위치: lim_chat_pro/engine/L1_Infrastructure/path_manager.py
    _FILE_PATH = Path(__file__).resolve()
    SRC_ROOT = _FILE_PATH.parent.parent          # engine/
    PROJECT_ROOT = SRC_ROOT.parent.parent        # 프로젝트 루트 (mcp_asdk_studio_v1/)
    
    # 2. 주요 장소 정의
    IQ_PACKS_DIR = PROJECT_ROOT / "packs"       
    USER_DATA_ROOT = PROJECT_ROOT / "user_data" 
    
    CONFIG_DIR = USER_DATA_ROOT / "configs"
    HISTORY_DIR = USER_DATA_ROOT / "history"
    
    # 기본 경로 (Fallback)
    DATA_ROOT = USER_DATA_ROOT
    PROFILE_DIR = USER_DATA_ROOT / "profiles"
    SERVER_DIR = USER_DATA_ROOT / "servers"
    PROMPT_DIR = USER_DATA_ROOT / "prompts"
    
    # UI 경로
    L5_UI_DIR = SRC_ROOT / "L5_Presentation"
    
    active_pack = None

    @classmethod
    def set_active_pack(cls, pack_name: str):
        cls.active_pack = pack_name
        
    @classmethod
    def _resolve_path(cls, legacy_path: Path, pack_subdir: str):
        if cls.active_pack:
            pack_path = cls.IQ_PACKS_DIR / cls.active_pack / pack_subdir
            pack_path.mkdir(parents=True, exist_ok=True)
            return pack_path
        return legacy_path

    @classmethod
    def get_config_file(cls, filename="config_pro.json"):
        cls.CONFIG_DIR.mkdir(parents=True, exist_ok=True)
        return cls.CONFIG_DIR / filename
        
    @classmethod
    def get_history_dir(cls):
        cls.HISTORY_DIR.mkdir(parents=True, exist_ok=True)
        return cls.HISTORY_DIR
        
    @classmethod
    def get_profile_dir(cls):
        return cls._resolve_path(cls.PROFILE_DIR, "profiles")
        
    @classmethod
    def get_server_dir(cls):
        cls.SERVER_DIR.mkdir(parents=True, exist_ok=True)
        return cls.SERVER_DIR
        
    @classmethod
    def get_prompt_dir(cls):
        return cls._resolve_path(cls.PROMPT_DIR, "prompts")
    
    @classmethod
    def get_settings_file(cls):
        if cls.active_pack:
            return cls.IQ_PACKS_DIR / cls.active_pack / "settings.json"
        return None
    
    @classmethod
    def get_intent_map_file(cls):
        """의도 감지 지도(intent_map.json) 파일 위치를 알려줍니다."""
        if cls.active_pack:
            return cls.IQ_PACKS_DIR / cls.active_pack / "intent_map.json"
        return None 
    
    @classmethod
    def get_ui_path(cls, filename="index_pro.html"):
        # index_pro.html이 없으면 index.html로 폴백
        path = cls.L5_UI_DIR / filename
        if not path.exists() and filename == "index_pro.html":
            return cls.L5_UI_DIR / "index.html"
        return path

    @classmethod
    def add_engine_to_sys_path(cls):
        """런처에서 사용하는 호환성 메서드"""
        if str(cls.SRC_ROOT) not in sys.path:
            sys.path.insert(0, str(cls.SRC_ROOT))
        if str(cls.PROJECT_ROOT) not in sys.path:
            sys.path.insert(0, str(cls.PROJECT_ROOT))
