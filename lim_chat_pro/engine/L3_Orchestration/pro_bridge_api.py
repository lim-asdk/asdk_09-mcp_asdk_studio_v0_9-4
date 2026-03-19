import os
import json
import logging
from pathlib import Path

logger = logging.getLogger("ASDK.Studio.Bridge")

class ProBridgeAPI:
    """
    L3 Orchestration: ProBridgeAPI [V5-D-06 Enhanced]
    Bridges Python logic to the Studio JS UI (index_pro.html).
    """
    
    def __init__(self):
        self._window = None
        self._active_persona = "default_assistant"
        self._active_pack = "asdk_studio_v1"
        self.ai_runner = None

    def set_window(self, window):
        self._window = window

    # --- System Info & Identity ---
    def get_version_info(self):
        return {"status": "ok", "version": "0.9.4", "name": "ASDK Studio Hub"}

    def get_active_pack_info(self):
        return {
            "id": "asdk_studio_v1",
            "name": "MCP ASDK Studio",
            "description": "Professional AI Workspace with V5 Matrix",
            "version": "0.9-4"
        }

    # --- Configuration & Settings ---
    def get_engine_config(self):
        return {
            "version": "0.9.4",
            "max_iterations": 30,
            "context_limit": 100000,
            "data_max_length": 100000,
            "trim_strategy": "truncate"
        }

    def get_settings_template(self):
        return """
            <div class='section-title'>Engine Limits</div>
            <label>Max Iterations</label><input type='number' id='sys-max-iter' value='30'>
            <label>Context Limit</label><input type='number' id='sys-ctx-limit' value='100000'>
            <label>Data Max Length</label><input type='number' id='sys-data-limit' value='100000'>
            <label>Trim Strategy</label>
            <select id='sys-trim-strategy'>
                <option value='truncate'>Truncate</option>
                <option value='summarize'>Summarize</option>
            </select>
            <div id='sys-version-display' style='font-size:10px; color:gray;'>v0.9-4</div>
            <button onclick='saveEngineConfig()'>Save Settings</button>
            <span id='sys-save-status'></span>
        """

    # --- Personas & Profiles ---
    def get_personas(self):
        # UI expects {personas: [{id, name, model}], active_id}
        try:
            personas = [
                {"id": "default_assistant", "name": "Standard Assistant", "model": "grok-beta"},
                {"id": "expert_coder", "name": "Expert Coder", "model": "grok-beta"},
                {"id": "v5_matrix", "name": "V5 Matrix Architect", "model": "grok-beta"}
            ]
            return {"status": "ok", "personas": personas, "active_id": self._active_persona}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_profiles(self):
        return {"status": "ok", "profiles": [{"id": "default", "name": "Default Profile"}]}

    # --- MCP Server Management ---
    def get_server_config_list(self):
        """Loads from mcp_config.json in the project root."""
        root = Path(os.getcwd())
        config_path = root / "mcp_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("mcpServers", {})
            except:
                return {}
        return {}

    # --- Utility & Integration ---
    def get_ime_mode(self):
        return {"mode": "ENG"} # Placeholder for browser mode

    def get_active_pack(self):
        return self._active_pack

    # --- Chat Core ---
    def process_chat(self, message):
        logger.info(f"[Bridge] Chat: {message[:20]}...")
        # Placeholder logic
        return {"status": "ok", "response": f"Hub Echo: {message}"}

    def switch_persona(self, persona_id):
        self._active_persona = persona_id
        return {"status": "ok", "active_id": persona_id}

    def save_engine_config(self, config):
        logger.info(f"Saving engine config: {config}")
        return {"status": "saved"}
