import json
import logging
import os
import threading

from L1_Infrastructure.path_manager import PathManager
from L3_Orchestration.bridge_api import LimChatBridgeAPI

logger = logging.getLogger("ASDK.Studio.ProBridge")


class ProBridgeAPI(LimChatBridgeAPI):
    """Production bridge for the legacy Pro UI.

    The bridge keeps the interface responsive while AI profiles and MCP servers
    are loaded in the background. It mirrors the legacy V5 layout so the public
    beta UI stays compatible with the existing assets.
    """

    def __init__(self, use_schema=False):
        """Load the production config and start MCP servers without blocking boot."""
        super().__init__(use_schema, config_filename="config_pro.json", auto_init=False)

        self._pro_profile_dir = PathManager.get_profile_dir()
        self._pro_prompt_dir = PathManager.get_prompt_dir()
        self._pro_server_dir = PathManager.get_server_dir()

        # Keep the profile loader pointed at the active public/private data root.
        self._profile_loader.profile_dir = self._pro_profile_dir

        # Start MCP servers in the background so the UI can open immediately.
        threading.Thread(target=self._init_servers, daemon=True).start()

        # Sync the production profile from .env when the key is available.
        self._sync_production_config()

        self._active_persona = "emergency_assistant"
        logger.info(f"ProBridgeAPI ready. Active persona: {self._active_persona}")

    def get_models(self):
        """Return the model list expected by the UI, with a safe fallback."""
        config = self._config_manager.config
        models = config.get("available_models", [])

        if not models:
            return {
                "models": [
                    {"id": "grok-4-1-fast-non-reasoning", "name": "Grok 4.20 (Fast Non-Reasoning)"},
                    {"id": "gpt-4o", "name": "GPT-4o (OpenAI)"},
                ]
            }
        return {"models": models}

    def _sync_production_config(self):
        """Mirror the active profile and seed it from XAI_API_KEY when present."""
        try:
            from dotenv import load_dotenv

            load_dotenv()
            grok_key = os.getenv("XAI_API_KEY")
            target_profile_id = self._config_manager.config.get(
                "active_profile_id",
                "grok-4-1-fast-non-reasoning",
            )

            profiles = self._config_manager.config.get("profiles", [])
            existing = next((p for p in profiles if p["id"] == target_profile_id), None)

            if not existing and target_profile_id == "grok-4-1-fast-non-reasoning":
                logger.info(f"[Sync] Creating '{target_profile_id}' profile from .env.")
                new_profile = {
                    "id": target_profile_id,
                    "name": target_profile_id,
                    "model": target_profile_id,
                    "base_url": "https://api.x.ai/v1",
                    "system_prompt": "You are a fast, non-reasoning assistant.",
                }
                profiles.append(new_profile)
                self._config_manager.config["profiles"] = profiles

            self._config_manager.config["active_profile_id"] = target_profile_id
            if grok_key:
                self._config_manager.save_api_key(target_profile_id, grok_key)
            self._config_manager.save()
        except Exception as exc:
            logger.warning(f"Failed to sync production profile: {exc}")

    # --- UI-required methods (index_pro.html compatibility) ---

    def get_personas(self):
        """Load persona files from the prompt directory used by the legacy UI."""
        try:
            persona_dir = PathManager.PROJECT_ROOT / "engine" / "L4_Prompt" / "personas"
            if not persona_dir.exists():
                persona_dir = PathManager.PROJECT_ROOT / "lim_chat_pro" / "engine" / "L4_Prompt" / "personas"

            personas = []
            for file_path in persona_dir.glob("*.txt"):
                personas.append(
                    {
                        "id": file_path.stem,
                        "name": file_path.stem.replace("_", " ").title(),
                        "model": "grok-beta",
                    }
                )

            if not personas:
                personas = [{"id": "emergency_assistant", "name": "Emergency Assistant", "model": "grok-beta"}]

            personas.sort(key=lambda item: 0 if item["id"] == "emergency_assistant" else 1)
            return {"status": "ok", "personas": personas, "active_id": self._active_persona}
        except Exception as exc:
            return {"status": "error", "message": str(exc)}

    # --- packs and system helpers (Pro tier) ---

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
                            with open(intro_path, "r", encoding="utf-8") as handle:
                                data = json.load(handle).get("manifest", {})
                                manifests.append(
                                    {
                                        "dir": item.name,
                                        "name": data.get("name", item.name),
                                        "description": data.get("description", ""),
                                        "version": data.get("version", "?"),
                                    }
                                )
                        except Exception:
                            pass
        return {"status": "ok", "packs": manifests}

    def get_engine_config(self):
        return self._config_manager.load_engine_config()

    def get_settings_template(self):
        # Match the System tab expectations in the legacy UI.
        return super().get_settings_template() if hasattr(super(), "get_settings_template") else ""

    def get_profile_key(self, profile_id):
        """Return the saved API key for the requested profile."""
        if not profile_id or profile_id == "new":
            return {"key": ""}

        actual_key = self._config_manager.get_api_key(profile_id)
        return {"key": actual_key if actual_key else ""}

    def _init_servers(self):
        """Start each MCP server in its own thread so slow servers do not block boot."""
        from L1_Infrastructure.mcp_handler import McpClientHandler

        project_root = PathManager.PROJECT_ROOT
        servers_conf = self._config_manager.config.get("mcpServers", {})

        def start_single_server(name, conf):
            try:
                client = McpClientHandler(name, conf, project_root)
                client.start()
                self._clients[name] = client
                logger.info(f"[BOOT] Server '{name}' connected successfully.")
            except Exception as exc:
                logger.error(f"Failed to initialize server '{name}': {exc}")

        for name, conf in servers_conf.items():
            threading.Thread(target=start_single_server, args=(name, conf), daemon=True).start()

    # chat(), get_profiles(), save_profile(), get_tools(), and test_profile()
    # are handled by LimChatBridgeAPI. That keeps the core AI logic and key
    # management centralized in the parent class.
