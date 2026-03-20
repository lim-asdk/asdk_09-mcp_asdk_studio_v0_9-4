# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3
# Developer: LIMHWACHAN
# Version: 1.3

import time
import logging
import threading
import sys
from pathlib import Path
from typing import Dict
import ctypes
from ctypes import wintypes

# 상위 계층 임포트 (L1, L2, L3)
from L1_Infrastructure.config_manager import ConfigManager
from L1_Infrastructure.mcp_handler import McpClientHandler
from L1_Infrastructure.path_manager import PathManager
from L2_Logic.history_manager import HistoryManager
from L2_Logic.profile_loader import ProfileLoader
from L3_Orchestration.ai_engine import LimChatAIEngine

logger = logging.getLogger("LimChat.Bridge")

class LimChatBridgeAPI:
    """
    [L3 Orchestration Layer]
    역할: 웹뷰(L5 Presentation)와 내부 로직을 잇는 통로입니다.
    사용자의 요청을 받아 적절한 모듈(L1, L2, L3)을 호출하고 결과를 반환합니다.
    
    CRITICAL PRINCIPLE:
    - Code (Hardware): Shared across all versions
    - Prompts/Configs (Software): Standard-specific directories
    """
    def __init__(self, use_schema=False, config_filename="config_standard.json", auto_init=True):
        self._window = None
        self.use_schema = use_schema
        
        # [CRITICAL] ConfigManager initialization (Parameter-based)
        self._config_manager = ConfigManager(config_filename=config_filename)
        self._history_manager = HistoryManager()
        
        # 서버 및 도구 관리
        self._clients: Dict[str, McpClientHandler] = {}
        self._tool_map: Dict[str, str] = {} # tool_name -> server_name
        
        # 캐시 설정
        self._history_cache = []
        self._history_dirty = 0
        self._history_flush_every = 5
        
        self._profile_loader = ProfileLoader()
        # Use actual directories from PathManager
        self._profile_loader.profile_dir = PathManager.get_profile_dir()
        
        # 페르소나 관리 (Persistence)
        self._active_persona = self._config_manager.config.get("last_persona") or "stock_analyst"

        # [Prompt Management] BackupManager 초기화
        from L2_Logic.backup_manager import BackupManager
        # Use Dynamic prompt directory
        self._PROMPTS_DIR = PathManager.get_prompt_dir()
        self._BACKUPS_DIR = self._PROMPTS_DIR / "backups"
        self._HISTORY_FILE = PathManager.PROJECT_ROOT / "data" / "prompt_history.json"
        
        self._backup_manager = BackupManager(
            prompts_dir=str(self._PROMPTS_DIR),
            backups_dir=str(self._BACKUPS_DIR),
            history_file=str(self._HISTORY_FILE)
        )
        
        # 초기화: 설정된 서버 시작 (Pro에서 오버라이드 가능하도록 auto_init 옵션 지원)
        if auto_init:
            self._init_servers()
        
        logger.info(f"BridgeAPI initialized (Config: {config_filename})")

    # --- Prompt Management Methods (Moved from prompt_api.py) ---

    def get_prompt_files(self):
        """[UI] 사용 가능한 프롬프트 파일 목록을 반환합니다."""
        try:
            logger.info(f"[Debug] Searching for prompts in: {self._PROMPTS_DIR}")
            if not self._PROMPTS_DIR.exists():
                 logger.error(f"[Debug] Prompt directory does not exist: {self._PROMPTS_DIR}")
            
            files = []
            for f in self._PROMPTS_DIR.glob("*.md"):
                 # Extract layer info from filename (e.g., L4_stock_analyst -> L4)
                 layer = f.stem.split("_")[0] if "_" in f.stem else "Unknown"
                 files.append({
                     "name": f.stem,
                     "path": str(f),
                     "layer": layer,
                     # "content": ... (List implementation usually omits content for performance)
                 })
            
            logger.info(f"[Debug] Found {len(files)} prompt files")
            # 정렬 (L1 -> L2 -> ...)
            files.sort(key=lambda x: x['name'])
            
            # [Debug] 반환 데이터 확인 로그
            logger.info(f"[Debug] Returning files to UI: {files}")
            return files
        except Exception as e:
            logger.error(f"Failed to list prompt files: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return []  # Return empty list on error instead of dict

    def get_prompt_file(self, layer):
        """[UI] 특정 계층의 프롬프트 내용을 가져옵니다."""
        try:
            logger.info(f"[Debug] get_prompt_file called with layer='{layer}'")
            logger.info(f"[Debug] PROMPTS_DIR: {self._PROMPTS_DIR}")
            
            file_path = self._PROMPTS_DIR / f"{layer}.md"
            logger.info(f"[Debug] Looking for file: {file_path}")
            logger.info(f"[Debug] File exists: {file_path.exists()}")
            
            if not file_path.exists():
                logger.error(f"[Debug] File not found: {file_path}")
                return {"error": "Prompt file not found"}
            
            content = file_path.read_text(encoding='utf-8')
            logger.info(f"[Debug] Successfully loaded {len(content)} characters from {layer}")
            return {
                "layer": layer,
                "content": content
            }
        except Exception as e:
            logger.error(f"Failed to get prompt '{layer}': {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}

    def update_prompt_file(self, layer, content, reason="Manual edit via UI"):
        """[UI] 프롬프트 내용을 수정합니다 (저장 전 자동 백업)."""
        try:
            if content is None:
                return {"error": "Content is required"}
            
            file_path = self._PROMPTS_DIR / f"{layer}.md"
            
            # 1. 기존 파일이 있으면 백업 생성
            if file_path.exists():
                self._backup_manager.create_backup(layer, reason)
            
            # 2. 파일 저장
            file_path.write_text(content, encoding='utf-8')
            
            return {
                "status": "success",
                "message": f"Prompt '{layer}' updated and backed up."
            }
        except Exception as e:
            logger.error(f"Failed to update prompt '{layer}': {e}")
            return {"error": str(e)}

    def get_backups(self, layer=None, limit=None):
        """[UI] 백업 목록을 가져옵니다."""
        try:
            # pywebview에서 int로 넘어오지 않을 수 있으므로 형변환 시도
            if limit is not None:
                limit = int(limit)
            return self._backup_manager.list_backups(layer_name=layer, limit=limit)
        except Exception as e:
            logger.error(f"Failed to list backups: {e}")
            return {"error": str(e)}

    def restore_backup(self, backup_filename):
        """[UI] 백업 파일로부터 프롬프트를 복원합니다."""
        try:
            if not backup_filename:
                return {"error": "backup_filename is required"}
            
            self._backup_manager.restore_backup(backup_filename)
            return {
                "status": "success",
                "message": f"Restored from {backup_filename}"
            }
        except Exception as e:
            logger.error(f"Failed to restore prompt: {e}")
            return {"error": str(e)}

    def get_prompt_diff(self, layer, backup_filename):
        """[UI] 현재 파일과 백업 파일의 차이점을 가져옵니다."""
        try:
            if not layer or not backup_filename:
                return {"error": "layer and backup_filename are required"}
            
            diff = self._backup_manager.get_diff(layer, backup_filename)
            return {"diff": diff}
        except Exception as e:
            logger.error(f"Failed to get diff: {e}")
            return {"error": str(e)}

    def get_prompt_history(self):
        """[UI] 전체 변경 이력을 가져옵니다."""
        try:
            if not self._HISTORY_FILE.exists():
                return []
            
            import json
            with open(self._HISTORY_FILE, 'r', encoding='utf-8-sig') as f:
                history = json.load(f)
            return history
        except Exception as e:
            logger.error(f"Failed to get history: {e}")
            return {"error": str(e)}

    def create_backup_snapshot(self, reason="Manual Backup"):
         """[UI] 현재 상태의 모든 프롬프트 파일을 백업합니다. (Snapshot)"""
         try:
             # L1~L5 등 모든 파일에 대해 백업 수행
             # 현재 BackupManager.create_backup은 단일 layer에 대해 동작함.
             # API 요구사항: "Create Backup" 버튼은 전체 스냅샷인가?
             # BackupPanel.tsx를 안봐서 모르겠지만, 보통 개별 파일 백업일수도.
             # 하지만 api.ts에서는 createBackup() 인자가 없음.
             # 따라서 전체 백업 또는 '현재 선택된 것' 백업일 것.
             # 안전하게 존재하는 모든 .md 파일에 대해 백업 생성.
             
             results = []
             for f in self._PROMPTS_DIR.glob("*.md"):
                 layer_name = f.stem
                 self._backup_manager.create_backup(layer_name, reason)
                 results.append(layer_name)
                 
             return {
                 "status": "success",
                 "message": f"Created snapshots for: {', '.join(results)}",
                 "backup_file": "multiple" # api.ts expects backup_file string
             }
         except Exception as e:
             logger.error(f"Failed to create snapshot: {e}")
             return {"error": str(e)}

    def generate_prompt_snapshot(self):
        """[UI] 현재 모든 프롬프트 파일을 하나의 MD 파일로 생성합니다."""
        try:
            from datetime import datetime
            import os
            
            # 스냅샷 파일 경로
            snapshot_dir = PathManager.PROJECT_ROOT / "프롬프트_관리_시스템" / "snapshots"
            snapshot_dir.mkdir(parents=True, exist_ok=True)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            snapshot_file = snapshot_dir / f"prompt_snapshot_{timestamp}.md"
            
            # 모든 프롬프트 파일 수집
            prompt_files = sorted(self._PROMPTS_DIR.glob("*.md"))
            
            if not prompt_files:
                return {"error": "No prompt files found"}
            
            # MD 파일 생성
            content = []
            content.append("# 프롬프트 시스템 스냅샷\n")
            content.append(f"**생성 시간**: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            content.append(f"**프롬프트 개수**: {len(prompt_files)}\n")
            content.append("\n---\n\n")
            
            # 목차 생성
            content.append("## 📑 목차\n\n")
            for i, file_path in enumerate(prompt_files, 1):
                layer_name = file_path.stem
                content.append(f"{i}. [{layer_name}](#{layer_name.lower().replace('_', '-')})\n")
            content.append("\n---\n\n")
            
            # 각 프롬프트 파일 내용 추가
            for file_path in prompt_files:
                layer_name = file_path.stem
                
                content.append(f"## {layer_name}\n\n")
                content.append(f"**파일**: `{file_path.name}`\n")
                content.append(f"**크기**: {file_path.stat().st_size} bytes\n")
                content.append(f"**수정 시간**: {datetime.fromtimestamp(file_path.stat().st_mtime).strftime('%Y-%m-%d %H:%M:%S')}\n\n")
                
                # 프롬프트 내용
                with open(file_path, 'r', encoding='utf-8') as f:
                    prompt_content = f.read()
                
                content.append("```markdown\n")
                content.append(prompt_content)
                content.append("\n```\n\n")
                content.append("---\n\n")
            
            # 파일 저장
            with open(snapshot_file, 'w', encoding='utf-8') as f:
                f.write(''.join(content))
            
            logger.info(f"Prompt snapshot created: {snapshot_file}")
            
            return {
                "status": "success",
                "file_path": str(snapshot_file),
                "file_name": snapshot_file.name,
                "prompt_count": len(prompt_files)
            }
            
        except Exception as e:
            logger.error(f"Failed to generate prompt snapshot: {e}")
            return {"error": str(e)}


    def _init_servers(self):
        # [PathManager] 프로젝트 루트 동적 참조
        project_root = PathManager.PROJECT_ROOT
        servers_conf = self._config_manager.config.get("mcpServers", {})
        for name, conf in servers_conf.items():
            try:
                client = McpClientHandler(name, conf, project_root)
                client.start()
                self._clients[name] = client
            except Exception as e:
                logger.error(f"Failed to initialize server '{name}': {e}")

    def _bind_tools_dynamic(self, persona_name):
        """
        [Semantic Binding] 페르소나의 capability_keywords를 기반으로
        현재 연결된 MCP 도구들의 화이트리스트를 동적 생성
        
        Args:
            persona_name: 페르소나 이름 (예: "stock_analyst")
        
        Returns:
            허용된 도구 이름 리스트
        """
        try:
            # 1. 페르소나 프로필 로드
            profile = self._profile_loader.load_profile(persona_name)
            keywords = profile.get("capability_keywords", [])
            
            if not keywords:
                logger.warning(f"[Binding] No capability_keywords in {persona_name}, allowing all tools")
                # Fallback: allowed_tools가 있으면 사용 (하위 호환성)
                return profile.get("allowed_tools", [])
            
            # 2. 현재 연결된 모든 MCP 도구 수집
            allowed_tools = []
            for server_name, client in self._clients.items():
                if client.status != "connected":
                    continue
                
                # disabled_tools 체크
                disabled_list = self._config_manager.config.get("mcpServers", {}).get(server_name, {}).get("disabled_tools", [])
                
                for tool in client.tools:
                    # UI에서 비활성화된 도구는 제외
                    if tool.name in disabled_list:
                        continue
                    
                    # 3. Semantic Matching: 도구 설명에 키워드 포함 여부 확인
                    tool_text = f"{tool.name} {tool.description}".lower()
                    
                    for keyword in keywords:
                        if keyword.lower() in tool_text:
                            allowed_tools.append(tool.name)
                            logger.info(f"[Binding] ✅ {tool.name} matched by keyword '{keyword}'")
                            break  # 하나라도 매칭되면 추가
            
            logger.info(f"[Binding] Persona '{persona_name}' granted {len(allowed_tools)} tools")
            return allowed_tools
            
        except Exception as e:
            logger.error(f"[Binding] Failed to bind tools for {persona_name}: {e}")
            return []  # 실패 시 빈 리스트 (모든 도구 차단)

    def set_window(self, window):
        self._window = window

    # --- UI Callable Methods ---

    def chat(self, message, use_ai_mode, use_server=False):
        """[UI] 사용자의 채팅 메시지를 처리합니다."""
        try:
            # 1. 프로필 정보 획득
            active_id = self._config_manager.config.get("active_profile_id")
            meta = self._config_manager.get_profile_meta(active_id)
            if not meta: return {"response": "Please select a profile first."}
            
            # 2. AI 엔진 초기화 (L3)
            api_key = self._config_manager.get_api_key(active_id)
            
            # [Configuration] 엔진 설정 로드
            engine_config = self._config_manager.load_engine_config()
            
            # AI Engine 초기화
            engine = LimChatAIEngine(api_key, meta["model"], meta["base_url"], use_schema=self.use_schema, engine_config=engine_config)
            
            # [CRITICAL] 페르소나 로더 경로 동기화 (Standard/Pro/Expert 버전별 독립성 보장)
            engine.profile_loader.profile_dir = self._profile_loader.profile_dir
            
            # [Semantic Binding] 동적 화이트리스트 생성
            dynamic_whitelist = self._bind_tools_dynamic(self._active_persona)
            
            # [Multi-Persona] 현재 페르소나 적용 (RouterLock & System Prompt)
            # set_persona() 메서드가 동적 화이트리스트로 RouterLock을 설정하고 시스템 프롬프트를 반환함
            system_prompt = engine.set_persona(self._active_persona, allowed_tools_override=dynamic_whitelist)
            
            # 3. 히스토리 준비 (L2)
            if not self._history_manager.current_session_file:
                self._history_manager.start_new_session()
            
            # 사용자 메시지 기록
            user_msg = {"role": "user", "content": message, "timestamp": self._ts()}
            self._append_history(user_msg)
            
            # 히스토리 로드 (최근 10개)
            recent_hist = self._history_manager.load_history(self._history_manager.current_session_file.name)[-10:]
            recent_hist = [{k: v for k, v in m.items() if k != "tool_calls"} for m in recent_hist]

            # 4. 도구 목록 준비 (L1)
            all_openai_tools = []
            self._refresh_tool_map()
            if use_server:
                for name, c in self._clients.items():
                    if c.status == "connected":
                        disabled_list = self._config_manager.config.get("mcpServers", {}).get(name, {}).get("disabled_tools", [])
                        for t in c.tools:
                            if t.name in disabled_list:
                                continue
                            all_openai_tools.append({
                                "type": "function",
                                "function": {"name": t.name, "description": t.description, "parameters": t.inputSchema}
                            })

            # 5. 엔진 실행 (자율 루프 수행)
            res = engine.process_chat(
                message, recent_hist, all_openai_tools, 
                use_server, self._tool_map, self._clients,
                system_prompt_override=system_prompt  # 오버라이드 전달
            )

            # 6. 응답 기록 및 반환
            response_msg = {
                "role": "assistant", 
                "content": res.get("response", ""), 
                "timestamp": self._ts()
            }
            self._append_history(response_msg)
            
            # [Persistence] 현재 세션의 마지막 페르소나 저장
            self._config_manager.config["last_persona"] = self._active_persona
            self._config_manager.save()
            
            return res

        except Exception as e:
            logger.error(f"Chat failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            
            # [CRITICAL FALLBACK] If any error occurs (Auth fail, Profile missing, etc.), 
            # try one more time with default assistant fallback.
            try:
                logger.info("Retrying chat with default assistant fallback...")
                
                # [Robustness] Use safe defaults
                active_id = self._config_manager.config.get("active_profile_id")
                api_key = self._config_manager.get_api_key(active_id)
                
                # Use environment variable as last resort
                if not api_key:
                     import os
                     api_key = os.environ.get("OPENAI_API_KEY", "")
                
                # Default meta (Emergency Fallback)
                model = "gpt-4o" 
                base_url = None
                
                # Try to get meta from active profile if possible
                if api_key:
                    meta = self._config_manager.get_profile_meta(active_id)
                    if meta:
                        model = meta.get("model") or model
                        base_url = meta.get("base_url") or base_url

                if not api_key:
                    return {"response": f"❌ **Error**: {str(e)}\n\n⚠️ **System Info**: No valid API key found. Please check your profile settings. [Emergency Mode]"}

                # [Emergency Intelligence] Inject system state so AI can answer status questions
                active_pack = getattr(self, "get_active_pack", lambda: "Unknown")()
                
                engine_config = self._config_manager.load_engine_config()
                engine = LimChatAIEngine(api_key, model, base_url, use_schema=self.use_schema, engine_config=engine_config)
                
                # Use default profile directly
                system_prompt = engine.set_persona("default_assistant", allowed_tools_override=[])
                
                # Add a system note about the fallback and system state (Section Split!)
                injection_content = self._get_system_state_injection()
                fallback_msg = (
                    f"[SYSTEM: Original request failed with {str(e)}. Falling back to Emergency Assistant.]\n"
                    f"{injection_content}\n"
                    f"User Message: {message}"
                )
                
                res = engine.process_chat(fallback_msg, [], [], False, {}, {}, system_prompt_override=system_prompt)
                
                # Add a visual indicator to the response
                if "response" in res:
                    res["response"] = f"⚠️ **Emergency Fallback Active**: (Original Error: {str(e)})\n\n" + res["response"]
                
                return res
            except Exception as fallback_e:
                logger.error(f"Double fallback failed: {fallback_e}")

            return {"response": f"❌ An error occurred: {str(e)}"}

    def _refresh_tool_map(self):
        self._tool_map = {}
        for s_name, client in self._clients.items():
            if client.status == "connected":
                for t in client.tools:
                    self._tool_map[t.name] = s_name

    def _ts(self):
        return int(time.time() * 1000)

    def _append_history(self, msg_obj):
        # 성능을 위한 캐싱 및 지연 저장 로직
        if not self._history_cache:
            self._history_cache = self._history_manager.load_history(self._history_manager.current_session_file.name)
        
        self._history_cache.append(msg_obj)
        self._history_dirty += 1
        
        if self._history_dirty >= self._history_flush_every:
            self._history_manager.save_history(self._history_cache)
            self._history_dirty = 0

    # --- 공통 설정 및 프로필 메서드 (ConfigManager L1 활용) ---
    def get_profiles(self): 
        return {
            "profiles": self._config_manager.config.get("profiles", []),
            "active_id": self._config_manager.config.get("active_profile_id")
        }
    def activate_profile(self, pid): 
        self._config_manager.config["active_profile_id"] = pid
        self._config_manager.save()
        return {"status": "ok"}
    
    def save_profile(self, profile_data):
        """[UI] 프로필 정보를 저장합니다."""
        pid = profile_data.get("id") or f"p_{int(time.time()*1000)}"
        profile_data["id"] = pid
        
        # 프로필 리스트 업데이트
        profiles = self._config_manager.config.get("profiles", [])
        found = False
        for i, p in enumerate(profiles):
            if p["id"] == pid:
                # [보안 개선] 기존 프로필 수정 시, 키 값이 ******면 기존 메타데이터의 key_file을 유지함
                if profile_data.get("api_key") == "******":
                    profile_data["key_file"] = p.get("key_file")
                profiles[i] = profile_data
                found = True; break
        if not found: profiles.append(profile_data)
        
        self._config_manager.config["profiles"] = profiles
        
        # [중요] 키 값이 ******가 아닐 때만 실제 파일 저장 수행
        new_key = profile_data.get("api_key")
        if new_key and new_key != "******":
            self._config_manager.save_api_key(pid, new_key)
            
        self._config_manager.save()
        return {"status": "saved"}

    def get_server_status(self):
        return [{"name": n, "status": c.status, "tools": len(c.tools)} for n, c in self._clients.items()]
    
    def get_tools(self):
        """[UI] 모든 서버의 도구 목록을 통합하여 반환합니다."""
        all_tools = {}
        for s_name, client in self._clients.items():
            disabled_list = self._config_manager.config.get("mcpServers", {}).get(s_name, {}).get("disabled_tools", [])
            for t in client.tools:
                all_tools[t.name] = {
                    "name": t.name,
                    "description": t.description,
                    "server": s_name,
                    "enabled": t.name not in disabled_list
                }
        return {"tools": all_tools}

    def get_server_tools(self, name):
        """[UI] 특정 서버의 도구 목록을 반환합니다."""
        if name not in self._clients:
            return {"ok": False, "message": "Server is not connected.", "tools": []}
        
        tools = []
        disabled_list = self._config_manager.config.get("mcpServers", {}).get(name, {}).get("disabled_tools", [])
        for t in self._clients[name].tools:
            tools.append({
                "name": t.name,
                "description": t.description,
                "parameters": t.inputSchema,
                "enabled": t.name not in disabled_list
            })
        return {"ok": True, "tools": tools, "status": self._clients[name].status, "error": self._clients[name].error_msg}

    def get_server_config_list(self):
        """[UI] 설정된 서버 목록을 반환합니다."""
        return self._config_manager.config.get("mcpServers", {})

    def save_server_config(self, name, command, args_str, transport="stdio", url=None, headers_str=None, display_name=None):
        """[UI] 서버 설정을 저장하고 재시작합니다 (Transport 지원 추가)."""
        # Test Connection should mirror the saved server definition closely so
        # local SSE/HTTP entries exercise the same launch path as real startup.
        args = [a.strip() for a in args_str.split('\n') if a.strip()]
        
        # 헤더 파싱 (Key=Value 형태)
        headers = {}
        if headers_str:
            for line in headers_str.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    headers[k.strip()] = v.strip()

        # Preserve existing env from JSON if available
        existing_conf = self._config_manager.config.get("mcpServers", {}).get(name, {})
        env = existing_conf.get("env", {}).copy()
        
        # Enforce essential flags
        env["PYTHONUNBUFFERED"] = "1"
        env["GR_BOOT_SILENT"] = "1"

        server_data = {
            "name": display_name or name, # 표시 이름 (없으면 ID 사용)
            "transport": transport,  # stdio, sse, http
            "command": command,
            "args": args,
            "env": env,
            "url": url,
            "headers": headers
        }
        
        # 개별 파일로 저장
        success = self._config_manager.save_server(name, server_data)
        if not success:
            return {"status": "failed", "message": "File save failed"}

        # 서버 재시작
        if name in self._clients:
            try:
                self._clients[name].stop()
            except:
                pass
        
        project_root = PathManager.PROJECT_ROOT
        new_client = McpClientHandler(name, server_data, project_root)
        new_client.start()
        self._clients[name] = new_client
        
        return {"status": "saved"}

    def toggle_tool(self, server_name, tool_name, enabled):
        """[UI] 특정 도구의 활성화 여부를 전환합니다."""
        server_conf = self._config_manager.config.get("mcpServers", {}).get(server_name)
        if not server_conf:
            return {"status": "error", "message": "Server configuration not found."}
        
        disabled_list = server_conf.get("disabled_tools", [])
        if enabled:
            if tool_name in disabled_list:
                disabled_list.remove(tool_name)
        else:
            if tool_name not in disabled_list:
                disabled_list.append(tool_name)
        
        server_conf["disabled_tools"] = disabled_list
        self._config_manager.save_server(server_name, server_conf)
        return {"status": "ok", "enabled": enabled}

    def toggle_server_tools(self, server_name, enabled):
        """[UI] 특정 서버의 모든 도구를 일괄 활성화/비활성화합니다."""
        server_conf = self._config_manager.config.get("mcpServers", {}).get(server_name)
        if not server_conf:
            return {"status": "error", "message": "Server configuration not found."}
        
        # 클라이언트에서 도구 목록을 가져와야 함
        client = self._clients.get(server_name)
        if not client:
            return {"status": "error", "message": "Server is not connected."}
            
        all_tool_names = [t.name for t in client.tools]
        
        if enabled:
            # 모두 활성화 -> disabled_list 비우기
            server_conf["disabled_tools"] = []
        else:
            # 모두 비활성화 -> 모든 도구를 disabled_list에 추가
            server_conf["disabled_tools"] = all_tool_names
            
        self._config_manager.save_server(server_name, server_conf)
        return {"status": "ok", "enabled": enabled}

    def test_connection(self, command, args_str, transport="stdio", url=None, headers_str=None, display_name=None):
        """[UI] 입력된 설정으로 서버 연결을 테스트합니다 (Transport 지원)."""
        args = [a.strip() for a in args_str.split('\n') if a.strip()]
        
        headers = {}
        if headers_str:
            for line in headers_str.split('\n'):
                if '=' in line:
                    k, v = line.split('=', 1)
                    headers[k.strip()] = v.strip()

        # Preserve existing env from JSON if available (for test_temp)
        # For temporary tests, we might not have a saved config yet, 
        # but if we do, we should use its env.
        # HTTP/SSE entries keep command/args so the handler can auto-launch a
        # local backing server before connecting to the /sse endpoint.
        existing_conf = self._config_manager.config.get("mcpServers", {}).get(display_name or "Test Server", {})
        env = existing_conf.get("env", {}).copy()
        
        # Enforce essential flags
        env["PYTHONUNBUFFERED"] = "1"
        env["GR_BOOT_SILENT"] = "1"

        temp_config = {
            "name": display_name or "Test Server",
            "transport": transport,
            "command": command,
            "args": args,
            "env": env,
            "url": url,
            "headers": headers
        }
        
        # 임시 클라이언트 생성
        temp_name = "test_temp"
        project_root = PathManager.PROJECT_ROOT
        client = McpClientHandler(temp_name, temp_config, project_root)
        last_error = None
        # A localhost SSE/HTTP target can emit transient connection failures
        # while its backing process is still binding the port.
        remote_transport = transport.lower() in ("sse", "http")
        
        try:
            client.start()
            # 최대 10초 대기
            for _ in range(20):
                time.sleep(0.5)
                if client.status == "connected":
                    tools = []
                    for t in client.tools:
                        tools.append({
                            "name": t.name,
                            "description": t.description,
                            "parameters": t.inputSchema
                        })
                    return {"ok": True, "status": "connected", "tools": tools}
                if client.status == "error":
                    # SSE/HTTP entries may still be starting their backing local
                    # process, so we keep waiting until the timeout instead of
                    # failing on the first transient connection error.
                    if remote_transport:
                        last_error = client.error_msg or "Unknown Error"
                        continue
                    return {"ok": False, "message": client.error_msg or "Unknown Error"}
            
            if last_error:
                return {"ok": False, "message": f"Connection Timeout: Server did not respond in 10s ({last_error})"}
            return {"ok": False, "message": "Connection Timeout: Server did not respond in 10s"}
        except Exception as e:
            return {"ok": False, "message": str(e)}
        finally:
            try:
                client.stop()
            except:
                pass

    def delete_server(self, name):
        """[UI] 서버 설정을 삭제하고 가동 중인 클라이언트를 중지합니다."""
        if name in self._clients:
            try:
                self._clients[name].stop()
                del self._clients[name]
            except:
                pass
        
        success = self._config_manager.delete_server(name)
        return {"status": "deleted" if success else "failed"}

    def test_profile(self, api_key, model, base_url, profile_id=None):
        """[UI] API 키 유효성을 테스트합니다."""
        try:
            # [보안 개선] 키가 마스킹된 경우 저장된 키 로드
            if api_key == "******" and profile_id and profile_id != "new":
                real_key = self._config_manager.get_api_key(profile_id)
                if not real_key:
                    return {"ok": False, "message": "Saved key not found."}
                api_key = real_key

            from openai import OpenAI
            test_client = OpenAI(api_key=api_key, base_url=base_url)
            test_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            return {"ok": True}
        except Exception as e:
            return {"ok": False, "message": str(e)}

    def load_history_list(self): return self._history_manager.get_history_list()
    def load_history_session(self, fname): return self._history_manager.load_history(fname)
    def clear_history(self):
        """[UI] 모든 히스토리를 삭제합니다."""
        self._history_manager.clear_all_history()
        return {"status": "cleared"}

    def start_new_chat(self):
        """[UI] 새로운 대화 세션을 시작합니다."""
        filename = self._history_manager.start_new_session()
        return {"status": "ok", "filename": filename}

    def delete_history_session(self, filename):
        """[UI] 특정 히스토리 세션을 삭제합니다."""
        success = self._history_manager.delete_history(filename)
        return {"status": "deleted" if success else "failed"}

    def delete_profile(self, pid):
        """[UI] 프로필을 삭제합니다."""
        success = self._config_manager.delete_profile(pid)
        return {"status": "deleted" if success else "failed"}

    def get_ime_mode(self):
        """[UI] 현재 윈도우의 IME 상태(한글/영문)를 반환합니다. (WebView2 호환성 개선)"""
        try:
            class GUITHREADINFO(ctypes.Structure):
                _fields_ = [
                    ("cbSize", ctypes.c_ulong),
                    ("flags", ctypes.c_ulong),
                    ("hwndActive", ctypes.c_void_p),
                    ("hwndFocus", ctypes.c_void_p),
                    ("hwndCapture", ctypes.c_void_p),
                    ("hwndMenuOwner", ctypes.c_void_p),
                    ("hwndMoveSize", ctypes.c_void_p),
                    ("hwndCaret", ctypes.c_void_p),
                    ("rcCaret", wintypes.RECT)
                ]
            
            hwnd = ctypes.windll.user32.GetForegroundWindow()
            if not hwnd: return {"mode": "Unknown"}

            thread_id = ctypes.windll.user32.GetWindowThreadProcessId(hwnd, None)
            
            gui_info = GUITHREADINFO(cbSize=ctypes.sizeof(GUITHREADINFO))
            success = ctypes.windll.user32.GetGUIThreadInfo(thread_id, ctypes.byref(gui_info))
            
            # 포커스된 실제 입력 창(WebView Render Window)을 타겟팅
            target_hwnd = gui_info.hwndFocus if (success and gui_info.hwndFocus) else hwnd
            
            hime = ctypes.windll.imm32.ImmGetContext(target_hwnd)
            if not hime:
                return {"mode": "Unknown"}
            
            # 0: Alphanumeric (ENG), 1: Hangul (KOR)
            status = ctypes.windll.imm32.ImmGetOpenStatus(hime)
            ctypes.windll.imm32.ImmReleaseContext(target_hwnd, hime)
            
            return {"mode": "KOR" if status else "ENG"}
        except Exception as e:
            return {"mode": "Unknown", "error": str(e)}

    def get_engine_config(self):
        """[UI] 엔진 설정을 반환합니다."""
        return self._config_manager.load_engine_config()

    def save_engine_config(self, config_data):
        """[UI] 엔진 설정을 저장합니다."""
        success = self._config_manager.save_engine_config(config_data)
        return {"status": "saved" if success else "failed"}

    def get_settings_template(self):
        """[UI] 설정 페이지의 HTML 템플릿을 반환합니다."""
        template_path = PathManager.get_ui_path("settings.html")
        if template_path.exists():
            return template_path.read_text(encoding="utf-8")
        return ""

    def get_personas(self):
        """[UI] 사용 가능한 페르소나 리스트를 반환합니다."""
        try:
            profile_names = self._profile_loader.list_profiles()
            personas = []
            for name in profile_names:
                # Format name: "stock_analyst" -> "Stock Analyst"
                display_name = name.replace("_", " ").title()
                personas.append({
                    "id": name,
                    "name": display_name
                })
            
            # [Robustness] If no profiles found, add the emergency assistant
            if not personas:
                personas.append({"id": "default_assistant", "name": "Emergency Assistant"})
                
            return {"personas": personas, "active_id": self._active_persona}
        except Exception as e:
            logger.error(f"Failed to get personas: {e}")
            # Fallback to at least show the current/default persona
            return {
                "personas": [{"id": "default_assistant", "name": "Emergency Assistant"}], 
                "active_id": self._active_persona, 
                "error": str(e)
            }

    def switch_persona(self, persona_id):
        """[UI] 활성 페르소나를 전환합니다."""
        # [Robustness] 존재 확인 후 없으면 기본값으로
        available = self._profile_loader.list_profiles()
        if persona_id not in available and persona_id != "default_assistant":
            logger.warning(f"Requested persona {persona_id} not found. Falling back to default.")
            persona_id = available[0] if available else "default_assistant"

        self._active_persona = persona_id
        
        # [Persistence] 즉시 저장
        self._config_manager.config["last_persona"] = persona_id
        self._config_manager.save()
        
        return {"status": "ok", "active_id": persona_id}

    def _get_system_state_injection(self):
        """
        [Safety] Construct the System State Injection string.
        This scans both MCP Tools (Hardware) and Packs (Intelligence) to prevent AI confusion.
        
        ################################################################################
        # [MAINTENANCE GUIDE] Emergency AI Recognition Method (Context Injection)
        # created_at: 2026-01-26
        # reason: To ensure Emergency AI distinguishes between 'Tools(MCP)' and 'Brains(Packs)'.
        #
        # 1. MCP Scan: Iterates self.get_server_status() -> List of tools.
        # 2. Pack Scan: Physically scans 'packs/' dir -> List of packs.
        #    - Token Optimization: Reads 'intro.json' but ONLY extracts 'manifest.name'.
        #    - Safety: Wrapped in try-except to never crash the emergency fallback.
        #
        # If you need to change how AI perceives the system state, MODIFY THIS METHOD.
        ################################################################################
        """
        try:
            active_pack = getattr(self, "get_active_pack", lambda: "Unknown")()
            
            # 1. MCP Tools Scan (Hardware)
            mcp_lines = []
            for s in self.get_server_status():
                 status_icon = "🟢" if s['status'] == 'connected' else "🔴"
                 mcp_lines.append(f"- {status_icon} {s['name']} ({s['status']})")
            mcp_section = "\n".join(mcp_lines) or "No servers connected."

            # 2. Pack Scan (Intelligence)
            pack_section = "Scanning failed."
            try:
                import pathlib
                import json
                packs_dir = pathlib.Path("packs") 
                if packs_dir.exists():
                    pack_list = []
                    for p in packs_dir.iterdir():
                        if p.is_dir() and not p.name.startswith("_") and not p.name.startswith("."):
                            intro_file = p / "data" / "prompts" / "intro.json"
                            display_name = ""
                            
                            # [Token Optimization] Only read 'name' to save tokens
                            if intro_file.exists():
                                try:
                                    # Read file but only parse name/description
                                    content = intro_file.read_text(encoding='utf-8')
                                    data = json.loads(content)
                                    manifest = data.get("manifest", {})
                                    real_name = manifest.get("name", "")
                                    # Only append name if it exists, no description to save tokens
                                    if real_name:
                                        display_name = f": {real_name}"
                                    else:
                                         display_name = " (Valid)"
                                except:
                                    display_name = " (Read Error)"
                                    
                            pack_list.append(f"- 📦 {p.name}{display_name}")
                    pack_section = "\n".join(pack_list) or "No packs found."
            except Exception as scan_e:
                pack_section = f"Error scanning packs: {str(scan_e)}"

            return (
                f"\n\n== 🛡️ SYSTEM STATE INJECTION 🛡️ ==\n"
                f"The following information is mechanically injected by the Body (Engine).\n"
                f"You are receiving this because the System Admin (User) needs diagnosis.\n\n"
                
                f"[GLOBAL HARDWARE: MCP TOOLS] 🛠️\n"
                f"(These are external tools you can USE. They are shared across all packs.)\n"
                f"{mcp_section}\n\n"
                
                f"[BRAIN CARTRIDGES: INTELLIGENCE PACKS] 🧠\n"
                f"(These are brain modules you can SWITCH to. They contain personas/prompts.)\n"
                f"current_active_pack: {active_pack}\n"
                f"available_packs:\n{pack_section}\n\n"
                
                f"== END OF INJECTION ==\n"
            )
        except Exception as e:
            logger.error(f"Error building system state injection: {e}")
            return "\n[SYSTEM STATE INJECTION FAILED]\n"
