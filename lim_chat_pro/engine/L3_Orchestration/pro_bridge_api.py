import logging
import os
import json
from pathlib import Path

# Use the base class for "Real" functionality
from L3_Orchestration.bridge_api import LimChatBridgeAPI
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("ASDK.Studio.ProBridge")

class ProBridgeAPI(LimChatBridgeAPI):
    """
    [L3 Orchestration] ProBridgeAPI [V5-D-07 Production Mode]
    Inherits from LimChatBridgeAPI to provide full-scale AI & MCP capabilities.
    Focuses on 'PRO' folder structures and secure key management.
    """
    
    def __init__(self, use_schema=False):
        """
        Initialize with config_pro.json to separate Professional and Standard user data.
        """
        # Call parent with config_pro.json for distinct environment
        super().__init__(use_schema, config_filename="config_pro.json", auto_init=False)
        
        # PRO-specific directories via PathManager
        self._pro_profile_dir = PathManager.get_profile_dir()
        self._pro_prompt_dir = PathManager.get_prompt_dir()
        self._pro_server_dir = PathManager.get_server_dir()
        
        # [Sync] Update loaders to point to the correct PRO directories
        self._profile_loader.profile_dir = self._pro_profile_dir
        
        # Initialize servers (Safe to call once)
        self._init_servers()
        
        # Pull key from .env if first time setup
        self._sync_env_to_config()
        
        logger.info(f"ProBridgeAPI [V5 Production] Ready. (Profiles: {self._pro_profile_dir})")

    def _sync_env_to_config(self):
        """
        Pull keys from .env and inject into ConfigManager if not already set.
        Matches user request: '키도 끌고 와서 셋팅 해'
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
            grok_key = os.getenv("XAI_API_KEY")
            
            # Check if we have any profiles
            profiles = self._config_manager.config.get("profiles", [])
            if not profiles:
                logger.info("[Sync] No profiles found. Creating default Profile with .env key.")
                default_profile = {
                    "id": "asdk_default",
                    "name": "ASDK Studio Assistant (Grok Powered)",
                    "model": "grok-beta",
                    "base_url": "https://api.x.ai/v1",
                    "system_prompt": "You are a professional AI workspace assistant."
                }
                self._config_manager.config["profiles"] = [default_profile]
                self._config_manager.config["active_profile_id"] = "asdk_default"
                if grok_key:
                    self._config_manager.save_api_key("asdk_default", grok_key)
                self._config_manager.save()
        except Exception as e:
            logger.warning(f"Failed to sync .env: {e}")

    # --- UI REQUIRED METHODS (Ensure mapping for index_pro.html) ---
    
    def get_personas(self):
        """[UI] Load personas as per index_pro specifications"""
        try:
            # Look in lim_chat_pro/engine/L4_Prompt/personas/
            persona_dir = PathManager.get_profile_dir()
            personas = []
            for f in persona_dir.glob("*.txt"):
                personas.append({"id": f.stem, "name": f.stem.replace("_", " ").title(), "model": "grok-beta"})
            
            # Fallback if empty
            if not personas:
                personas = [{"id": "default_assistant", "name": "Standard Assistant", "model": "grok-beta"}]
            
            return {
                "status": "ok", 
                "personas": personas, 
                "active_id": self._active_persona
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # Handled by base class: get_profiles, save_profile, activate_profile
    # Handled by base class: chat(msg, is_ai, use_server)
    # Handled by base class: get_tools, get_server_status, get_server_config_list
    
    # --- PRO SPECIFIC: PACKS ---

    def get_available_packs(self):
        """Returns raw list of directories in packs/"""
        packs_dir = PathManager.IQ_PACKS_DIR
        if not packs_dir.exists(): return []
        return [item.name for item in packs_dir.iterdir() if item.is_dir()]

    def get_active_pack(self):
        return PathManager.active_pack or "asdk_studio_v1"

    def get_pack_manifests(self):
        """Reads intro.json for each pack for the dropdown list"""
        manifests = []
        packs_dir = PathManager.IQ_PACKS_DIR
        for item in packs_dir.iterdir():
            if item.is_dir():
                intro_path = item / "data" / "prompts" / "intro.json"
                if intro_path.exists():
                    try:
                        with open(intro_path, 'r', encoding='utf-8') as f:
                            data = json.load(f)
                            m = data.get("manifest", {})
                            manifests.append({
                                "dir": item.name,
                                "name": m.get("name", item.name),
                                "description": m.get("description", ""),
                                "version": m.get("version", "?")
                            })
                    except: pass
        return {"status": "ok", "packs": manifests}

    def get_engine_config(self):
        return self._config_manager.load_engine_config()

    def get_settings_template(self):
        # A simple template if UI needs a placeholder
        return "<div>System Configuration Panel</div>"
