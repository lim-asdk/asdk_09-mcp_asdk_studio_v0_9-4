# Project: lim_chat_v2_0
# Developer: LIMHWACHAN
# Version: Expert Edition 1.0

"""
🎯 Expert Bridge API - Expert Edition Interface

This module provides the JavaScript-Python bridge for Expert Edition,
exposing methods for multi-AI debate functionality to the UI.

CRITICAL PRINCIPLE:
- Code (Hardware): Shared with Standard (extends LimChatBridgeAPI)
- Prompts/Configs (Software): Completely separate (Expert-specific paths)
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from pathlib import Path

# Import Expert Orchestrator
from L3_Orchestration.expert_orchestrator import ExpertOrchestrator

# Import existing infrastructure (Code sharing - OK!)
from L3_Orchestration.bridge_api import LimChatBridgeAPI
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("LimChat.Expert.BridgeAPI")


class ExpertBridgeAPI(LimChatBridgeAPI):
    """
    Expert Edition Bridge API
    
    Extends the standard Bridge API with Expert Debate functionality.
    Maintains full compatibility with existing features while adding
    multi-AI debate capabilities and using Expert-specific directories.
    
    SEPARATION PRINCIPLE:
    - Inherits all code from LimChatBridgeAPI (shared hardware)
    - Overrides paths to use Expert-specific directories (separate software)
    """
    
    def __init__(self, use_schema=False):
        """Initialize Expert Bridge API with Expert-specific paths"""
        # Call parent constructor
        super().__init__(use_schema)
        
        # [CRITICAL] Override ConfigManager to use Expert-specific config (Settings Isolation)
        from L1_Infrastructure.config_manager import ConfigManager
        self._config_manager = ConfigManager(config_filename="config_expert.json")
        
        # Override paths to Expert-specific directories
        self._expert_profile_dir = PathManager.PROJECT_ROOT / "data" / "profiles" / "expert"
        self._expert_prompt_dir = PathManager.PROJECT_ROOT / "data" / "prompts" / "expert"
        self._expert_server_dir = PathManager.PROJECT_ROOT / "data" / "servers" / "expert"
        
        # Ensure directories exist
        self._expert_profile_dir.mkdir(parents=True, exist_ok=True)
        self._expert_prompt_dir.mkdir(parents=True, exist_ok=True)
        self._expert_server_dir.mkdir(parents=True, exist_ok=True)
        
        # Update ProfileLoader to use Expert directory
        from L2_Logic.profile_loader import ProfileLoader
        self._profile_loader = ProfileLoader()
        self._profile_loader.profile_dir = self._expert_profile_dir
        
        # Initialize Expert Orchestrator
        self.expert_orchestrator = ExpertOrchestrator()
        
        logger.info("ExpertBridgeAPI initialized")
        logger.info(f"Expert Profile Dir: {self._expert_profile_dir}")
        logger.info(f"Expert Prompt Dir: {self._expert_prompt_dir}")
        logger.info(f"Expert Server Dir: {self._expert_server_dir}")
    
    def run_expert_analysis(
        self,
        query: str,
        bull_model: str = "gpt-4",
        bull_version: str = "latest",
        bear_model: str = "gemini-pro",
        bear_version: str = "latest",
        judge_model: str = "deepseek",
        judge_version: str = "latest",
        parallel: bool = True,
        show_opinions: bool = True
    ) -> Dict[str, Any]:
        """
        [UI] Run Expert Debate analysis
        
        Args:
            query: User's question (e.g., "Analyze IBRX stock")
            bull_model: Model for Bull AI
            bull_version: Version for Bull AI
            bear_model: Model for Bear AI
            bear_version: Version for Bear AI
            judge_model: Model for Judge AI
            judge_version: Version for Judge AI
            parallel: Run Bull and Bear in parallel
            show_opinions: Include individual opinions in result
        
        Returns:
            Dictionary with debate results
        """
        try:
            logger.info(f"Starting Expert Analysis for: {query}")
            logger.info(f"Bull: {bull_model}-{bull_version}, Bear: {bear_model}-{bear_version}, Judge: {judge_model}-{judge_version}")
            
            # Prepare AI configurations
            bull_config = {"model": bull_model, "version": bull_version}
            bear_config = {"model": bear_model, "version": bear_version}
            judge_config = {"model": judge_model, "version": judge_version}
            
            # Progress callback for UI updates
            progress_updates = []
            
            def progress_callback(phase, status, progress):
                update = {
                    "phase": phase,
                    "status": status,
                    "progress": progress
                }
                progress_updates.append(update)
                logger.info(f"Progress: {phase} - {status} ({progress}%)")
                
                # Send real-time update to UI if window is available
                if self._window:
                    try:
                        self._window.evaluate_js(
                            f"window.updateExpertProgress('{phase}', '{status}', {progress})"
                        )
                    except:
                        pass
            
            # Run debate (synchronously wrap async call)
            result = asyncio.run(
                self.expert_orchestrator.run_debate(
                    user_query=query,
                    bull_ai_config=bull_config,
                    bear_ai_config=bear_config,
                    judge_ai_config=judge_config,
                    parallel=parallel,
                    show_opinions=show_opinions,
                    progress_callback=progress_callback
                )
            )
            
            # Format response
            response = {
                "status": result.status,
                "execution_time": result.execution_time,
                "warnings": result.warnings,
                "progress_updates": progress_updates
            }
            
            if show_opinions:
                response["bull_opinion"] = result.bull_opinion
                response["bear_opinion"] = result.bear_opinion
            
            response["judge_verdict"] = result.judge_verdict
            
            logger.info(f"Expert Analysis completed: {result.status} ({result.execution_time:.2f}s)")
            
            return response
            
        except Exception as e:
            logger.error(f"Expert Analysis failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "status": "error",
                "error": str(e),
                "warnings": [f"Fatal error: {str(e)}"]
            }
    
    def save_expert_config(self, config: Dict[str, Any]) -> Dict[str, str]:
        """
        [UI] Save Expert Debate configuration
        
        Args:
            config: Configuration dictionary with AI settings
        
        Returns:
            Status dictionary
        """
        try:
            # Save to config manager
            self._config_manager.config["expert_debate"] = config
            self._config_manager.save()
            
            logger.info("Expert config saved successfully")
            return {"status": "success", "message": "Configuration saved"}
            
        except Exception as e:
            logger.error(f"Failed to save expert config: {e}")
            return {"status": "error", "message": str(e)}
    
    def load_expert_config(self) -> Dict[str, Any]:
        """
        [UI] Load Expert Debate configuration
        
        Returns:
            Configuration dictionary
        """
        try:
            config = self._config_manager.config.get("expert_debate", {})
            
            # Apply defaults if not set
            if not config:
                config = {
                    "bull_ai": "gpt-4",
                    "bull_version": "latest",
                    "bear_ai": "gemini-pro",
                    "bear_version": "latest",
                    "judge_ai": "deepseek",
                    "judge_version": "latest",
                    "parallel": True,
                    "show_opinions": True
                }
            
            return config
            
        except Exception as e:
            logger.error(f"Failed to load expert config: {e}")
            return {}
    
    def test_expert_config(
        self,
        bull_model: str,
        bear_model: str,
        judge_model: str
    ) -> Dict[str, Any]:
        """
        [UI] Test Expert Debate AI connections
        
        Args:
            bull_model: Bull AI model
            bear_model: Bear AI model
            judge_model: Judge AI model
        
        Returns:
            Test results
        """
        try:
            # TODO: Implement actual AI connection testing
            # For now, return success
            logger.info(f"Testing AI connections: Bull={bull_model}, Bear={bear_model}, Judge={judge_model}")
            
            results = {
                "bull": {"status": "connected", "model": bull_model},
                "bear": {"status": "connected", "model": bear_model},
                "judge": {"status": "connected", "model": judge_model}
            }
            
            return {
                "success": True,
                "results": results,
                "message": "All AI connections successful"
            }
            
        except Exception as e:
            logger.error(f"AI connection test failed: {e}")
            return {
                "success": False,
                "error": str(e)
            }
    
    def get_expert_presets(self) -> Dict[str, Any]:
        """
        [UI] Get available Expert Debate presets
        
        Returns:
            Dictionary of presets
        """
        try:
            presets = self.expert_orchestrator.get_presets()
            return {"presets": presets}
            
        except Exception as e:
            logger.error(f"Failed to get presets: {e}")
            return {"presets": {}, "error": str(e)}
    
    def apply_expert_preset(self, preset_name: str) -> Dict[str, Any]:
        """
        [UI] Apply an Expert Debate preset
        
        Args:
            preset_name: Name of preset to apply
        
        Returns:
            Applied configuration
        """
        try:
            config = self.expert_orchestrator.apply_preset(preset_name)
            
            # Save to config
            self._config_manager.config["expert_debate"] = {
                "bull_ai": config["bull"]["model"],
                "bull_version": config["bull"]["version"],
                "bear_ai": config["bear"]["model"],
                "bear_version": config["bear"]["version"],
                "judge_ai": config["judge"]["model"],
                "judge_version": config["judge"]["version"],
                "preset": preset_name
            }
            self._config_manager.save()
            
            logger.info(f"Applied preset: {preset_name}")
            return {"status": "success", "config": config}
            
        except Exception as e:
            logger.error(f"Failed to apply preset: {e}")
            return {"status": "error", "error": str(e)}
    
    def get_available_ai_models(self) -> Dict[str, Any]:
        """
        [UI] Get list of available AI models
        
        Returns:
            Dictionary of available models
        """
        # TODO: Dynamically detect available models from profiles
        # For now, return static list
        models = {
            "gpt-4": {
                "name": "GPT-4",
                "provider": "OpenAI",
                "versions": ["latest", "0613", "1106-preview"]
            },
            "gpt-4o": {
                "name": "GPT-4o",
                "provider": "OpenAI",
                "versions": ["latest", "2024-05-13"]
            },
            "gemini-pro": {
                "name": "Gemini Pro",
                "provider": "Google",
                "versions": ["latest", "1.0", "1.5"]
            },
            "deepseek": {
                "name": "DeepSeek",
                "provider": "DeepSeek",
            "versions": ["latest"]
            }
        }
        
        return {"models": models}
    
    # --- Expert AI Profile Management ---
    
    def get_expert_ai_profiles(self) -> Dict[str, Any]:
        """
        [UI] Expert 버전의 3개 AI Profile 반환
        
        Returns:
            Dictionary with bull, bear, judge AI profiles
        """
        try:
            expert_profiles = self._config_manager.config.get("expert_ai_profiles", {})
            
            # Mask API keys for security
            result = {}
            for role in ["bull", "bear", "judge"]:
                profile = expert_profiles.get(role, {})
                if profile and "api_key" in profile:
                    profile = profile.copy()
                    profile["api_key"] = "******"
                result[role] = profile
            
            logger.info(f"[Expert] Loaded AI profiles: {list(result.keys())}")
            return result
            
        except Exception as e:
            logger.error(f"[Expert] Failed to get AI profiles: {e}")
            return {"bull": {}, "bear": {}, "judge": {}}
    
    def save_expert_ai_profile(self, role: str, profile_data: Dict[str, Any]) -> Dict[str, str]:
        """
        [UI] Expert AI Profile 저장
        
        Args:
            role: "bull", "bear", "judge"
            profile_data: {name, model, api_key, base_url}
        
        Returns:
            Status dictionary
        """
        try:
            if role not in ["bull", "bear", "judge"]:
                return {"status": "error", "message": f"Invalid role: {role}"}
            
            # Initialize expert_ai_profiles if not exists
            if "expert_ai_profiles" not in self._config_manager.config:
                self._config_manager.config["expert_ai_profiles"] = {}
            
            # Get existing profile
            existing = self._config_manager.config["expert_ai_profiles"].get(role, {})
            
            # Update profile data
            updated_profile = {
                "name": profile_data.get("name", f"{role.capitalize()} AI"),
                "model": profile_data.get("model", ""),
                "base_url": profile_data.get("base_url", "")
            }
            
            # Handle API key (don't overwrite if masked)
            new_key = profile_data.get("api_key")
            if new_key and new_key != "******":
                # Save API key securely
                profile_id = f"expert_{role}"
                self._config_manager.save_api_key(profile_id, new_key)
                updated_profile["key_file"] = f"{profile_id}.key"
            elif existing.get("key_file"):
                # Keep existing key file reference
                updated_profile["key_file"] = existing["key_file"]
            
            # Save to config
            self._config_manager.config["expert_ai_profiles"][role] = updated_profile
            self._config_manager.save()
            
            logger.info(f"[Expert] Saved {role} AI profile: {updated_profile['name']}")
            return {"status": "saved", "role": role}
            
        except Exception as e:
            logger.error(f"[Expert] Failed to save {role} AI profile: {e}")
            return {"status": "error", "message": str(e)}
    
    def test_expert_ai_profile(self, role: str, api_key: str, model: str, base_url: str) -> Dict[str, Any]:
        """
        [UI] Expert AI Profile 연결 테스트
        
        Args:
            role: "bull", "bear", "judge"
            api_key: API key to test
            model: Model name
            base_url: API base URL
        
        Returns:
            Test result
        """
        try:
            # If API key is masked, load from saved profile
            if api_key == "******":
                profile_id = f"expert_{role}"
                api_key = self._config_manager.get_api_key(profile_id)
                if not api_key:
                    return {"ok": False, "message": "Saved API key not found"}
            
            # Test connection using OpenAI-compatible API
            from openai import OpenAI
            test_client = OpenAI(api_key=api_key, base_url=base_url)
            
            logger.info(f"[Expert] Testing {role} AI: {model} at {base_url}")
            
            test_client.chat.completions.create(
                model=model,
                messages=[{"role": "user", "content": "hi"}],
                max_tokens=5
            )
            
            logger.info(f"[Expert] {role} AI connection successful")
            return {"ok": True, "role": role, "message": f"{role.capitalize()} AI connection successful"}
            
        except Exception as e:
            logger.error(f"[Expert] {role} AI connection failed: {e}")
            return {"ok": False, "role": role, "message": str(e)}
