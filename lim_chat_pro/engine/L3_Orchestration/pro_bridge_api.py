import os
import json
import logging
from pathlib import Path

# Use absolute imports for robustness
try:
    from L1_Infrastructure.path_manager import PathManager
except ImportError:
    # Fallback for different sys.path configurations
    from lim_chat_pro.engine.L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("ASDK.Studio.Bridge")

class ProBridgeAPI:
    """
    L3 Orchestration: ProBridgeAPI [V5-D-06 Production Grade]
    Highly compatible bridge for MCP ASDK Studio UI (index_pro.html).
    """
    
    def __init__(self):
        self._window = None
        self._active_persona = "default_assistant"
        self._active_profile = "default"
        self._active_pack = "asdk_studio_v1"
        self.pm = PathManager()
        self.ai_runner = None

    def set_window(self, window):
        self._window = window

    # --- System Info ---
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
        # Returns the HTML template for system settings tab
        return """
            <h3 style='margin-top:0'>⚙️ System Configuration</h3>
            <div style='background:rgba(255,255,255,0.05); padding:15px; border-radius:8px; border:1px solid #334155;'>
                <label>Max Iterations</label><input type='number' id='sys-max-iter' value='30'>
                <label>Context Limit (tokens)</label><input type='number' id='sys-ctx-limit' value='100000'>
                <label>Data Max Length</label><input type='number' id='sys-data-limit' value='100000'>
                <label>Trim Strategy</label>
                <select id='sys-trim-strategy'>
                    <option value='truncate'>Truncate</option>
                    <option value='summarize'>Summarize</option>
                </select>
                <div style='margin-top:10px; display:flex; justify-content:space-between; align-items:center;'>
                    <span id='sys-version-display' style='font-size:11px; color:#64748b;'>v0.9-4</span>
                    <button onclick='saveEngineConfig()' style='background:#10b981; color:white; border:none; padding:6px 15px; border-radius:4px; cursor:pointer;'>Save Changes</button>
                    <span id='sys-save-status'></span>
                </div>
            </div>
        """

    # --- Personas & Profiles ---
    def get_personas(self):
        try:
            # For simplicity, returning static list or scanning personas/ folder
            personas = [
                {"id": "default_assistant", "name": "Standard Assistant", "model": "grok-beta"},
                {"id": "expert_coder", "name": "Expert Coder", "model": "grok-beta"},
                {"id": "v5_matrix", "name": "V5 Matrix Architect", "model": "grok-beta"}
            ]
            return {"status": "ok", "personas": personas, "active_id": self._active_persona}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    def get_profiles(self):
        try:
            # Scan user_data/profiles/
            profile_dir = self.pm.get_profiles_dir()
            profiles = []
            for f in profile_dir.glob("*.json"):
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        profiles.append({
                            "id": f.stem,
                            "name": data.get("name", f.stem),
                            "model": data.get("model", "grok-beta"),
                            "base_url": data.get("base_url", ""),
                            "system_prompt": data.get("system_prompt", "")
                        })
                except: continue
            
            if not profiles:
                profiles = [{"id": "default", "name": "ASDK Default", "model": "grok-beta"}]
            
            return {"status": "ok", "profiles": profiles, "active_id": self._active_profile}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    # --- MCP Tools & Servers ---
    def get_tools(self):
        # Returning mock tools for UI population
        return {
            "status": "ok",
            "tools": {
                "search": {"name": "Search", "server": "Core", "enabled": True},
                "calc": {"name": "Calculator", "server": "Core", "enabled": True}
            }
        }

    def get_server_status(self):
        return [
            {"name": "Local Hub", "status": "connected"},
            {"name": "MCP Gateway", "status": "connected"}
        ]

    def get_server_config_list(self):
        root = Path(os.getcwd())
        config_path = root / "mcp_config.json"
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    return json.load(f).get("mcpServers", {})
            except: return {}
        return {}

    # --- History Management ---
    def load_history_list(self):
        history_dir = self.pm.get_history_dir()
        hist = []
        for f in sorted(history_dir.glob("*.json"), key=os.path.getmtime, reverse=True):
            hist.append({"filename": f.name, "display": f.stem.replace("_", " ")})
        return hist[:20]

    def load_history_session(self, filename):
        path = self.pm.get_history_dir() / filename
        if path.exists():
            with open(path, 'r', encoding='utf-8') as f:
                return json.load(f).get("messages", [])
        return []

    def start_new_chat(self):
        logger.info("New Chat Session Started")
        return {"status": "ok"}

    # --- CORE CHAT FUNCTION ---
    def chat(self, msg, is_ai=True, use_server=False):
        """
        Main chat entry point as expected by index_pro.html (3 arguments)
        """
        try:
            logger.info(f"[Bridge] Chat Request: {msg[:30]}... (AI: {is_ai}, Server: {use_server})")
            
            # Simulated Response for Beta
            response = f"V5 Matrix Response to: '{msg}'\n\nPicturing your request with Persona: {self._active_persona}"
            
            # If real AI logic is needed, call AI Runner here
            return {
                "status": "ok", 
                "response": response,
                "tool_calls_log": []
            }
        except Exception as e:
            logger.error(f"Chat failed: {e}")
            return {"status": "error", "message": str(e)}

    # --- Other UI Callbacks ---
    def get_ime_mode(self):
        return {"mode": "ENG"}

    def get_active_pack(self):
        return self._active_pack

    def get_available_packs(self):
        return ["asdk_studio_v1"]

    def get_pack_manifests(self):
        return {"status": "ok", "packs": [{"dir": "asdk_studio_v1", "name": "MCP ASDK Studio"}]}

    def switch_persona(self, persona_id):
        self._active_persona = persona_id
        return {"status": "ok", "active_id": persona_id}

    def activate_profile(self, profile_id):
        self._active_profile = profile_id
        return {"status": "ok", "active_id": profile_id}
