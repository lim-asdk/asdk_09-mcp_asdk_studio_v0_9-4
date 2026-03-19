# Project: lim_chat_v1_4
# Developer: LIMHWACHAN
# Version: 1.4

"""
[L2 Logic Layer - Profile Loader]
Role: Handles the discovery, loading, and validation of Persona Profiles.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("LimChat.Logic.Profile")

class ProfileLoader:
    def __init__(self):
        """Initialize ProfileLoader using PathManager."""
        self.profile_dir = PathManager.get_profile_dir()

    def list_profiles(self) -> List[str]:
        """
        Scans the profile directory and returns a list of available profile names.
        (e.g., ["stock_analyst", "risk_advisor"])
        """
        if not self.profile_dir.exists():
            return []
            
        profiles = []
        for file in self.profile_dir.glob("*.json"):
            # [Filter] Exclude API key files created by ConfigManager (start with p_)
            if file.stem.startswith("p_"):
                continue
            profiles.append(file.stem)  # filename without extension
        return sorted(profiles)

    def get_default_profile(self) -> Dict[str, Any]:
        """
        Returns a hardcoded fallback profile for base AI functionality.
        Used when no persona is available or requested profile is missing.
        """
        return {
            "name": "Emergency Assistant",
            "description": "A versatile emergency fallback AI for when primary packs or authentication fails.",
            "prompt_file": "default_assistant.md",
            "system_prompt": "You are a helpful, versatile AI assistant. Provide clear and accurate information to the user.",
            "allowed_tools": [],
            "id": "default_assistant"
        }

    def load_profile(self, profile_name: str) -> Dict[str, Any]:
        """
        Loads a specific profile by name.
        
        Args:
            profile_name: The name of the profile to load (e.g., "stock_analyst")
            
        Returns:
            Dict containing the profile configuration with absolute paths resolved.
            
        Raises:
            FileNotFoundError: If profile or prompt file does not exist.
            ValueError: If JSON is invalid or missing required fields.
        """
        profile_path = self.profile_dir / f"{profile_name}.json"
        
        if not profile_path.exists():
            # [Robustness] Return default profile instead of failing if requested
            logger.warning(f"Profile not found: {profile_name}. Using default assistant.")
            return self.get_default_profile()

        try:
            with open(profile_path, "r", encoding="utf-8-sig") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in profile {profile_name}: {e}")

        # Validate and Resolve Paths (IQ-Pack Aware)
        self._validate_profile(data)
        
        if "prompt_file" in data:
            prompt_filename = data["prompt_file"]
            
            # [IQ-Pack Strict Mode]
            # Only use prompts from the active pack directory (no fallback)
            # This ensures clarity: you always know which prompt is being used
            prompt_dir = PathManager.get_prompt_dir()
            absolute_path = prompt_dir / prompt_filename
            
            if not absolute_path.exists():
                raise FileNotFoundError(
                    f"Prompt file not found in active pack: {absolute_path}\n"
                    f"Expected location: {prompt_dir}\n"
                    f"Filename: {prompt_filename}\n"
                    f"Active pack: {PathManager.active_pack or 'Legacy Mode'}"
                )
                
            data["prompt_file_path"] = str(absolute_path)
            
            # Load the actual prompt content
            try:
                with open(absolute_path, "r", encoding="utf-8") as f:
                    data["system_prompt"] = f.read()
            except Exception as e:
                raise ValueError(f"Failed to read prompt file {absolute_path}: {e}")

        return data

    def _validate_profile(self, data: Dict[str, Any]):
        """Validates that necessary fields exist in the profile data."""
        # Required fields (always needed)
        required_fields = ["name", "description", "prompt_file"]
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            raise ValueError(f"Missing required fields: {', '.join(missing)}")
        
        # Tool specification (either allowed_tools OR capability_keywords)
        has_allowed_tools = "allowed_tools" in data
        has_capability_keywords = "capability_keywords" in data
        
        if not has_allowed_tools and not has_capability_keywords:
            raise ValueError("Profile must have either 'allowed_tools' or 'capability_keywords'")
        
        # Validate types
        if has_allowed_tools and not isinstance(data["allowed_tools"], list):
            raise ValueError("allowed_tools must be a list")
        
        if has_capability_keywords and not isinstance(data["capability_keywords"], list):
            raise ValueError("capability_keywords must be a list")
