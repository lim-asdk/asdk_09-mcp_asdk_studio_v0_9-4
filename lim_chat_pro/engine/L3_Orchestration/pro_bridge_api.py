import os
import json
import logging
from pathlib import Path

# Use a delayed import or string comparison in PathManager to avoid recursion if any
# We already fixed PathManager to be simple.

logger = logging.getLogger("ASDK.Studio.Bridge")

class ProBridgeAPI:
    """
    L3 Orchestration: ProBridgeAPI
    
    This class serves as the primary bridge between the Python backend and the 
    JavaScript frontend (pywebview) for MCP ASDK Studio v0.9-4.
    It handles data serialization, message routing, and exposes system 
    capabilities (MCP, Personas, Profiles) to the UI.
    
    Note for AI Agents:
    - Use this class to register new features that require Python interaction.
    - All paths requested by the UI must go through the PathManager (L1).
    """
    
    def __init__(self):
        # Note: We don't store the window object here directly if it causes recursion in pywebview
        # We can use window.evaluate_js or similar directly from the main loop if needed,
        # or just avoid exposing the window object to the JS side.
        self._window = None
        self._active_persona = "default_assistant"
        
        # Delayed import to avoid circular dependency
        self.ai_runner = None

    def set_window(self, window):
        self._window = window

    # --- System Info ---
    def get_version_info(self):
        return {
            "version": "1.0.0",
            "name": "MCP ASDK Studio v1",
            "mode": "General Studio"
        }

    def get_active_pack_info(self):
        return {
            "id": "asdk_studio_v1",
            "name": "MCP ASDK Studio",
            "description": "General purpose AI Council Chamber & MCP Development Studio",
            "version": "1.0",
            "is_studio": True
        }

    # --- Personas (Profiles) ---
    def get_personas(self):
        from L1_Infrastructure.path_manager import PathManager
        try:
            pm = PathManager()
            profile_dir = pm.get_profiles_dir()
            personas = []
            
            for f in profile_dir.glob("*.json"):
                try:
                    with open(f, 'r', encoding='utf-8') as file:
                        data = json.load(file)
                        personas.append({
                            "id": f.stem,
                            "name": data.get("name", f.stem),
                            "model": data.get("model", "grok-beta")
                        })
                except Exception as e:
                    logger.warning(f"Failed to load persona {f.name}: {e}")
            
            if not personas:
                personas = [{"id": "default", "name": "Standard AI Assistant", "model": "grok-beta"}]
                
            return {"status": "ok", "personas": personas}
        except Exception as e:
            logger.error(f"Error listing personas: {e}")
            return {"status": "error", "message": str(e)}

    def switch_persona(self, persona_id):
        self._active_persona = persona_id
        return {"status": "ok", "persona_id": persona_id}

    # --- Chat Logic ---
    def process_chat(self, message):
        try:
            logger.info(f"[Bridge] User Message: {message[:50]}...")
            response = f"Studio Response: Received '{message}' (Persona: {self._active_persona})"
            return {"status": "ok", "response": response}
        except Exception as e:
            logger.error(f"Chat processing failed: {e}")
            return {"status": "error", "message": str(e)}

    def close_window(self):
        # We use a separate flag or call to avoid recursion in serialization
        if self._window:
            import webview
            # Instead of calling self._window.destroy(), 
            # we can just emit a sign or hide it if needed.
            pass
