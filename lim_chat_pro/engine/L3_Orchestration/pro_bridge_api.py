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
    Fully synchronized with index_pro.html and reference UI screenshots.
    """
    
    def __init__(self, use_schema=False):
        """
        Initialize with config_pro.json for Professional Edition environment.
        """
        # [V5 Standard] Use config_pro.json as requested in original ui/main.py
        super().__init__(use_schema, config_filename="config_pro.json", auto_init=False)
        
        # PRO-specific data routing
        self._pro_profile_dir = PathManager.get_profile_dir()
        self._pro_prompt_dir = PathManager.get_prompt_dir()
        self._pro_server_dir = PathManager.get_server_dir()
        
        # Update loaders
        self._profile_loader.profile_dir = self._pro_profile_dir
        
        # Start servers once
        self._init_servers()
        
        # [V5 Sync] Pull key from .env to match screenshot's 'grok-4-1' profile
        self._sync_production_config()
        
        # Default persona from screenshot
        self._active_persona = "emergency_assistant"
        
        logger.info(f"ProBridgeAPI [V5 Production] Ready. (Persona: {self._active_persona})")

    def get_models(self):
        """[UI] 사용 가능한 AI 모델 목록을 반환합니다."""
        return {
            "models": [
                {"id": "grok-2-latest", "name": "Grok 2 (Latest)"},
                {"id": "grok-2-vision-latest", "name": "Grok 2 Vision"},
                {"id": "grok-beta", "name": "Grok Beta"},
                {"id": "gpt-4o", "name": "GPT-4o (OpenAI)"},
                {"id": "claude-3-5-sonnet-20241022", "name": "Claude 3.5 Sonnet (New)"}
            ]
        }

    def _sync_production_config(self):
        """
        Ensures the profiles match the user's screenshot exactly.
        Profile Name: grok-4-1-fast-non-reasoning
        """
        try:
            from dotenv import load_dotenv
            load_dotenv()
            grok_key = os.getenv("XAI_API_KEY")
            
            # Match screenshot profile name exactly
            target_profile_id = "grok-4-1-fast-non-reasoning"
            
            profiles = self._config_manager.config.get("profiles", [])
            # Always ensure the default one exists and is complete
            existing = next((p for p in profiles if p["id"] == target_profile_id), None)
            
            if not existing:
                logger.info(f"[Sync] Creating '{target_profile_id}' profile from .env key.")
                new_profile = {
                    "id": target_profile_id,
                    "name": target_profile_id,
                    "model": "grok-2-latest", # Updated to grok-2-latest for stability
                    "base_url": "https://api.x.ai/v1",
                    "system_prompt": "You are a fast, non-reasoning Grok-powered assistant."
                }
                profiles.append(new_profile)
                self._config_manager.config["profiles"] = profiles
            else:
                # Update model if it was grok-beta/grok-2 and failed
                if not existing.get("model") or existing.get("model") in ["grok-beta", "grok-2"]:
                    existing["model"] = "grok-2-latest"
            
            self._config_manager.config["active_profile_id"] = target_profile_id
            if grok_key:
                self._config_manager.save_api_key(target_profile_id, grok_key)
            self._config_manager.save()
        except Exception as e:
            logger.warning(f"Failed to sync production profile: {e}")

    # --- UI REQUIRED METHODS (index_pro.html Compatibility) ---
    
    def get_personas(self):
        """[UI] Load personas from L4_Prompt/personas/ directory"""
        try:
            # Current PathManager.get_profile_dir() routes to packs/... or user_data/profiles
            # But personas are usually in lim_chat_pro/engine/L4_Prompt/personas/
            persona_dir = PathManager.PROJECT_ROOT / "engine" / "L4_Prompt" / "personas"
            if not persona_dir.exists():
                persona_dir = PathManager.PROJECT_ROOT / "lim_chat_pro" / "engine" / "L4_Prompt" / "personas"

            personas = []
            for f in persona_dir.glob("*.txt"):
                personas.append({
                    "id": f.stem, 
                    "name": f.stem.replace("_", " ").title(), 
                    "model": "grok-beta"
                })
            
            if not personas:
                personas = [{"id": "emergency_assistant", "name": "Emergency Assistant", "model": "grok-beta"}]
            
            # Sort to keep Emergency Assistant at top if possible
            personas.sort(key=lambda x: 0 if x["id"] == "emergency_assistant" else 1)
            
            return {
                "status": "ok", 
                "personas": personas, 
                "active_id": self._active_persona
            }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- PACKS & SYSTEMS (PRO Tier) ---

    def get_available_packs(self):
        packs_dir = PathManager.IQ_PACKS_DIR
        return [item.name for item in packs_dir.iterdir() if item.is_dir()] if packs_dir.exists() else []

    def get_active_pack(self):
        return PathManager.active_pack or "asdk_studio_v1"

    def get_pack_manifests(self):
        manifests = []
        packs_dir = PathManager.IQ_PACKS_DIR
        if packs_dir.exists():
            for item in packs_dir.iterdir():
                if item.is_dir():
                    intro_path = item / "data" / "prompts" / "intro.json"
                    if intro_path.exists():
                        try:
                            with open(intro_path, 'r', encoding='utf-8') as f:
                                data = json.load(f).get("manifest", {})
                                manifests.append({
                                    "dir": item.name,
                                    "name": data.get("name", item.name),
                                    "description": data.get("description", ""),
                                    "version": data.get("version", "?")
                                })
                        except: pass
        return {"status": "ok", "packs": manifests}

    def get_engine_config(self):
        return self._config_manager.load_engine_config()

    def get_settings_template(self):
        # Match the System tab expectations
        return super().get_settings_template() if hasattr(super(), 'get_settings_template') else ""

    def test_profile(self, api_key, model, base_url, profile_id=None):
        """Test if API Key/Model work (Real Backend Test)"""
        logger.info(f"[ProBridge] Testing Profile: {model} / {base_url} (ID: {profile_id})")
        
        # [Fix] If input key is masked (******), get the actual key from ConfigManager
        target_key = api_key
        if api_key == "******" and profile_id and profile_id != "new":
            # Search both in config.json and separate key files
            actual_key = self._config_manager.get_api_key(profile_id)
            if actual_key:
                target_key = actual_key
                logger.debug("[ProBridge] Using actual key from storage for test (masked input detected)")

        # Call the real check logic in ai_engine
        is_ok, msg = self._ai_engine.check_api_connectivity(target_key, model, base_url)
        return {"ok": is_ok, "message": msg}

    # NOTE: chat(), get_profiles(), save_profile(), get_tools() are handled by LimChatBridgeAPI (Parent)
    # This ensures "Real" AI logic and secure key management are active.
