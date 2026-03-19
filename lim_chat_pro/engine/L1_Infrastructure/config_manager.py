# -*- coding: utf-8 -*-
# Project: lim_chat_v1_1
# Developer: LIMHWACHAN
# Version: 1.1

import json
import os
import re
import logging
from pathlib import Path
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("LimChat.Config")

class ConfigManager:
    """
    [L1 Infrastructure Layer]
    역할: 프로그램의 기반이 되는 설정(Config), 프로필, API 키, 엔진 설정을 관리합니다.
    이 계층은 최하단에서 데이터의 저장소 위치와 환경 변수를 관리합니다.
    
    v1.3en 신규 기능:
    - load_engine_config(): AI 엔진의 물리적 한계(max_iterations, context_limit) 로드
    """
    def __init__(self, config_dir=None, config_filename=None):
        """
        Initialize ConfigManager with optional custom config directory or filename.
        
        Args:
            config_dir (Path|str, optional): Custom config directory for testing.
                                             If None, uses PathManager defaults.
            config_filename (str, optional): Custom filename for the configuration file.
                                             Example: "config_pro.json"
        """
        # [PathManager] 중앙 집중식 경로 관리
        if config_dir:
            # 테스트용: 커스텀 경로 사용
            self._custom_config_dir = True
            self.config_dir = Path(config_dir) if isinstance(config_dir, str) else config_dir
            self.config_file = self.config_dir / "configs" / (config_filename or "config_lim_chat_v1_4.json")
            self.profile_dir = self.config_dir / "profiles"
            self.server_dir = self.config_dir / "servers"
            
            # 디렉터리 생성 (구조 유지)
            (self.config_dir / "configs").mkdir(parents=True, exist_ok=True)
            self.profile_dir.mkdir(parents=True, exist_ok=True)
            self.server_dir.mkdir(parents=True, exist_ok=True)
        else:
            # 실제 사용: PathManager 사용
            self._custom_config_dir = False
            if config_filename:
                self.config_file = PathManager.get_config_file(config_filename)
            else:
                self.config_file = PathManager.get_config_file()
            self.profile_dir = PathManager.get_profile_dir()
            self.server_dir = PathManager.get_server_dir()
            self.config_dir = PathManager.CONFIG_DIR
        
        self.config = {
            "version": "1.4",
            "active_profile_id": None,
            "profiles": [],
            "window_settings": {"width": 1200, "height": 900, "x": 100, "y": 100},
            "mcpServers": {}, # 런타임에는 통합 객체로 유지하지만 저장은 개별 파일로 함
            "last_persona": None
        }
        self.load()


    def load(self):
        # 1. 기본 설정 로드
        if not self.config_file.exists():
            alt_v14 = self.config_file.parent / "config_lim_chat_v1_4.json"
            alt_v13 = self.config_file.parent / "config_lim_chat_v1_3.json"
            if alt_v14.exists():
                self.config_file = alt_v14
            elif alt_v13.exists():
                self.config_file = alt_v13
        if self.config_file.exists():
            try:
                data = json.loads(self.config_file.read_text(encoding="utf-8-sig"))
                # 레거시 데이터 마이그레이션 체크
                legacy_servers = data.get("mcpServers", {})
                if legacy_servers:
                    self._migrate_servers(legacy_servers)
                    # config 파일에서는 mcpServers 섹션 제거 (개별 파일이 소스)
                    if "mcpServers" in data: del data["mcpServers"]
                
                self.config.update(data)
            except Exception as e:
                logger.error(f"설정 로드 실패: {e}")

        # 2. 서버 설정 개별 파일 로드
        self.config["mcpServers"] = {}
        for s_file in self.server_dir.glob("*.json"):
            try:
                s_data = json.loads(s_file.read_text(encoding="utf-8-sig"))
                # 파일명이 기본 ID가 되지만, 내부에 name이 있으면 활용 가능
                s_id = s_file.stem
                self.config["mcpServers"][s_id] = s_data
            except Exception as e:
                logger.error(f"서버 설정 로드 실패 ({s_file.name}): {e}")

    def _migrate_servers(self, servers):
        """레거시 통합 설정을 개별 파일로 마이그레이션합니다."""
        logger.info(f"[Config] Migrating {len(servers)} servers to individual files...")
        for s_id, s_data in servers.items():
            self.save_server(s_id, s_data)

    def save(self):
        """공통 설정 저장 (서버 설정 제외)"""
        try:
            temp_config = self.config.copy()
            if "mcpServers" in temp_config:
                del temp_config["mcpServers"] # 개별 파일로 관리되므로 메인 설정에선 제외
            self.config_file.write_text(json.dumps(temp_config, indent=2, ensure_ascii=False), encoding="utf-8")
        except Exception as e:
            logger.error(f"설정 저장 실패: {e}")

    def save_server(self, server_id, server_data):
        """서버 설정을 개별 파일로 저장합니다."""
        try:
            s_file = self.server_dir / f"{server_id}.json"
            s_file.write_text(json.dumps(server_data, indent=2, ensure_ascii=False), encoding="utf-8")
            self.config["mcpServers"][server_id] = server_data
            logger.info(f"Server config saved: {s_file}")
            return True
        except Exception as e:
            logger.error(f"서버 저장 실패: {e}")
            return False

    def delete_server(self, server_id):
        """서버 설정 파일을 삭제합니다."""
        try:
            s_file = self.server_dir / f"{server_id}.json"
            if s_file.exists():
                s_file.unlink()
                if server_id in self.config["mcpServers"]:
                    del self.config["mcpServers"][server_id]
                logger.info(f"Server config deleted: {s_file}")
                return True
            return False
        except Exception as e:
            logger.error(f"서버 삭제 실패: {e}")
            return False

    def get_profile_meta(self, profile_id):
        for p in self.config["profiles"]:
            if p["id"] == profile_id: return p
        return None

    def get_api_key(self, profile_id):
        """
        프로필 JSON 파일에서 API 키를 로드합니다.
        (파일 기반 단일 소스 - 환경 변수 의존성 제거)
        """
        meta = self.get_profile_meta(profile_id)
        if not meta:
            logger.warning(f"Profile {profile_id} not found")
            return ""
        
        # 프로필 JSON 파일에서만 로드 (단일 진실 원천)
        if not meta.get("key_file"):
            logger.warning(f"No key_file specified for profile {profile_id}")
            return ""
        
        key_path = self.profile_dir / meta["key_file"]
        if not key_path.exists():
            logger.error(f"API key file not found: {key_path}")
            return ""
        
        try:
            data = json.loads(key_path.read_text(encoding="utf-8-sig"))
            return data.get("api_key", "")
        except Exception as e:
            logger.error(f"Failed to load API key: {e}")
            return ""

    def save_api_key(self, profile_id, api_key):
        """API 키를 프로필 JSON 파일에 저장합니다."""
        safe_id = re.sub(r"[^a-zA-Z0-9._-]", "_", profile_id)
        key_file = f"{safe_id}.json"
        key_path = self.profile_dir / key_file
        
        meta = self.get_profile_meta(profile_id)
        if meta:
            meta["key_file"] = key_file
            self.save()
        
        try:
            key_path.write_text(
                json.dumps({"api_key": api_key}, ensure_ascii=False), 
                encoding="utf-8"
            )
            logger.info(f"API key saved to: {key_path}")
        except Exception as e:
            logger.error(f"Failed to save API key: {e}")

    def delete_profile(self, profile_id):
        """프로필과 해당 API 키 파일을 삭제합니다."""
        meta = self.get_profile_meta(profile_id)
        if not meta:
            return False
        
        # 1. 키 파일 삭제
        if meta.get("key_file"):
            key_path = self.profile_dir / meta["key_file"]
            if key_path.exists():
                try:
                    key_path.unlink()
                    logger.info(f"Deleted key file: {key_path}")
                except Exception as e:
                    logger.error(f"Failed to delete key file: {e}")
        
        # 2. 프로필 리스트에서 삭제
        self.config["profiles"] = [p for p in self.config["profiles"] if p["id"] != profile_id]
        
        # 3. 만약 활성 프로필이었다면 해제
        if self.config.get("active_profile_id") == profile_id:
            self.config["active_profile_id"] = None
            
        self.save()
        return True
    
    def load_engine_config(self):
        """
        Load AI engine configuration from engine_config.json.
        Returns default values if file doesn't exist.
        """
        # Determine engine_config path based on initialization mode
        # If config_dir was set in __init__, we're in test mode
        if hasattr(self, '_custom_config_dir') and self._custom_config_dir:
            # Test mode: look in config_dir/configs/
            engine_config_file = self.config_dir / "configs" / "engine_config.json"
        elif "configs" in str(self.config_file):
            # Alternate test mode detection
            engine_config_file = self.config_file.parent / "engine_config.json"
        else:
            # Production mode: look in config_dir
            engine_config_file = self.config_dir / "engine_config.json"
        
        # Default values
        default_config = {
            "version": "1.4",
            "max_iterations": 30,
            "context_limit": 100000,
            "data_max_length": 100000,
            "trim_strategy": "keep_system_and_tools"
        }
        
        if not engine_config_file.exists():
            logger.info(f"[Config] Engine config not found, using defaults")
            return default_config
        
        try:
            data = json.loads(engine_config_file.read_text(encoding="utf-8-sig"))
            logger.info(f"[Config] Loaded engine config: max_iterations={data.get('max_iterations')}, context_limit={data.get('context_limit')}")
            return {**default_config, **data}  # Merge with defaults
        except Exception as e:
            logger.error(f"[Config] Failed to load engine config: {e}")
            return default_config

    def save_engine_config(self, config_data):
        """
        Save AI engine configuration to engine_config.json.
        """
        # Determine engine_config path based on initialization mode (Same logic as load)
        if hasattr(self, '_custom_config_dir') and self._custom_config_dir:
            engine_config_file = self.config_dir / "configs" / "engine_config.json"
        elif "configs" in str(self.config_file):
            engine_config_file = self.config_file.parent / "engine_config.json"
        else:
            engine_config_file = self.config_dir / "engine_config.json"
        try:
            # Ensure required fields are present if merging or just save what comes
            engine_config_file.write_text(json.dumps(config_data, indent=2, ensure_ascii=False), encoding="utf-8")
            logger.info(f"[Config] Saved engine config to {engine_config_file}")
            return True
        except Exception as e:
            logger.error(f"[Config] Failed to save engine config: {e}")
            return False

    def get_engine_config_version(self):
        """Returns the version from engine_config.json."""
        config = self.load_engine_config()
        return config.get("version", "1.4")
