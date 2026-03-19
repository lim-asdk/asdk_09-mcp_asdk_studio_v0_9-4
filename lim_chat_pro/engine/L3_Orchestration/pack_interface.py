# -*- coding: utf-8 -*-
# Project: LimChat Pro
# Component: Pack Data Interface (Read-Only)
# Role: The "Librarian" - Reads pack data but never executes logic.

import logging
import json
import pathlib
from typing import Dict, List, Any, Optional

logger = logging.getLogger("LimChat.PackInterface")

class PackInterface:
    """
    [Data Layer]
    Responsible for PHYSICALLY accessing the 'packs/' directory.
    - Scans for valid packs.
    - Reads intro.json and mainfest.
    - Provides raw data to Bridge or Orchestrator.
    
    CRITICAL: This class MUST NOT import 'ai_engine' or execute any tools.
    """
    
    def __init__(self, packs_root_name="packs"):
        self.packs_root = pathlib.Path(packs_root_name)
        
    def scan_available_packs(self) -> List[Dict[str, Any]]:
        """
        Scans the 'packs/' directory and returns a list of valid packs.
        A valid pack must be a directory. intro.json is optional but recommended.
        """
        results = []
        try:
            if not self.packs_root.exists():
                logger.warning(f"Packs root '{self.packs_root}' does not exist.")
                return []
                
            for item in self.packs_root.iterdir():
                if item.is_dir() and not item.name.startswith("_") and not item.name.startswith("."):
                    # Basic metadata
                    pack_info = {
                        "dir_name": item.name,
                        "path": str(item),
                        "has_intro": (item / "data" / "prompts" / "intro.json").exists()
                    }
                    
                    # Try to read name from intro.json (Lightweight)
                    if pack_info["has_intro"]:
                        try:
                            intro_data = self._read_json(item / "data" / "prompts" / "intro.json")
                            manifest = intro_data.get("manifest", {})
                            pack_info["name"] = manifest.get("name", item.name)
                            pack_info["description"] = manifest.get("description", "")
                        except Exception:
                            pack_info["name"] = item.name # Fallback
                    else:
                        pack_info["name"] = item.name
                        
                    results.append(pack_info)
                    
            return sorted(results, key=lambda x: x["name"])
            
        except Exception as e:
            logger.error(f"Error scanning packs: {e}")
            return []

    def get_pack_intro(self, pack_dir_name: str) -> Optional[Dict[str, Any]]:
        """Reads the full intro.json for a specific pack."""
        try:
            target_file = self.packs_root / pack_dir_name / "data" / "prompts" / "intro.json"
            if target_file.exists():
                return self._read_json(target_file)
            return None
        except Exception as e:
            logger.error(f"Failed to read intro for {pack_dir_name}: {e}")
            return None

    def _read_json(self, path: pathlib.Path) -> Dict[str, Any]:
        """Helper for safe JSON reading."""
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
