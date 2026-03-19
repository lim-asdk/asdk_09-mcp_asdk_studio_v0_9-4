# Project: lim_chat_v2_0
# Developer: LIMHWACHAN
# Version: Expert Edition 1.0

"""
🎯 Expert Orchestrator - Multi-AI Debate Coordinator

This module coordinates the Expert Debate system:
- Bull AI (Optimistic perspective)
- Bear AI (Pessimistic perspective)  
- Judge AI (Final verdict)

Features:
- Parallel or sequential execution
- Fault-tolerant (continues even if one AI fails)
- Detailed progress tracking
- Flexible AI assignment (one AI can handle multiple roles)
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, List
from dataclasses import dataclass
from pathlib import Path

# Import Expert AI Runner
from L2_AI_Engine.expert_ai_runner import ExpertAIRunner, AIResult, AIStatus

# Import existing infrastructure
from L1_Infrastructure.path_manager import PathManager
from L2_Logic.profile_loader import ProfileLoader

logger = logging.getLogger("LimChat.Expert.Orchestrator")


@dataclass
class DebateResult:
    """Expert debate result"""
    bull_opinion: Optional[Dict[str, Any]]
    bear_opinion: Optional[Dict[str, Any]]
    judge_verdict: Optional[Dict[str, Any]]
    execution_time: float
    warnings: List[str]
    status: str  # "success", "partial_success", "failed"


class ExpertOrchestrator:
    """
    Multi-AI Debate Coordinator for Expert Edition
    
    Orchestrates Bull AI, Bear AI, and Judge AI to provide
    comprehensive stock analysis from multiple perspectives.
    """
    
    def __init__(self, ai_engine=None):
        """
        Initialize Expert Orchestrator
        
        Args:
            ai_engine: Optional LimChatAIEngine instance (for testing or custom config)
        """
        self.ai_runner = ExpertAIRunner(default_timeout=120, max_retries=2)
        self.profile_loader = ProfileLoader()
        
        # AI Engine (will be set by ExpertBridgeAPI)
        self.ai_engine = ai_engine
        
        # Load expert debate profile
        self.expert_profile = self._load_expert_profile()
        
        logger.info("ExpertOrchestrator initialized")
    
    def _load_expert_profile(self) -> Dict[str, Any]:
        """Load expert debate configuration from profile"""
        try:
            profile_path = PathManager.PROJECT_ROOT / "data" / "profiles" / "expert_debate.json"
            
            if not profile_path.exists():
                logger.warning(f"Expert profile not found at {profile_path}, using defaults")
                return self._get_default_profile()
            
            import json
            with open(profile_path, 'r', encoding='utf-8') as f:
                profile = json.load(f)
            
            logger.info("Expert profile loaded successfully")
            return profile
            
        except Exception as e:
            logger.error(f"Failed to load expert profile: {e}, using defaults")
            return self._get_default_profile()
    
    def _get_default_profile(self) -> Dict[str, Any]:
        """Get default expert debate configuration"""
        return {
            "name": "Expert Debate",
            "version": "1.0.0",
            "ai_roles": {
                "bull": {
                    "prompt_file": "L4_expert_bull.md",
                    "default_model": "gpt-4",
                    "timeout": 120
                },
                "bear": {
                    "prompt_file": "L4_expert_bear.md",
                    "default_model": "gemini-pro",
                    "timeout": 120
                },
                "judge": {
                    "prompt_file": "L4_expert_judge.md",
                    "default_model": "deepseek",
                    "timeout": 90
                }
            },
            "presets": {
                "balanced": {
                    "bull": {"model": "gpt-4", "version": "latest"},
                    "bear": {"model": "gemini-pro", "version": "latest"},
                    "judge": {"model": "deepseek", "version": "latest"}
                }
            }
        }
    
    async def _prepare_shared_context(self, user_query: str) -> Dict[str, Any]:
        """
        Prepare shared context for Bull and Bear AIs
        
        CRITICAL: Bull과 Bear가 동일한 데이터를 보고 분석하도록
        데이터를 먼저 수집하여 공유 컨텍스트 생성
        
        Args:
            user_query: User's question (e.g., "IBRX 종목 분석해줘")
        
        Returns:
            Shared context dictionary with market data
        
        Example:
            {
                "timestamp": "2026-01-19 23:00:00",
                "data": {
                    "current_price": "$6.50",
                    "price_change": "+2.5%",
                    "volume": "1.2M",
                    "market_cap": "$450M",
                    "cash_position": "$45M",
                    "quarterly_revenue": "$8.2M"
                }
            }
        """
        try:
            from datetime import datetime
            import re
            
            logger.info(f"Fetching shared context for: {user_query}")
            
            # Extract ticker from query (simple regex)
            ticker_match = re.search(r'\b([A-Z]{2,5})\b', user_query)
            ticker = ticker_match.group(1) if ticker_match else "UNKNOWN"
            
            # Initialize shared context
            shared_context = {
                "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "ticker": ticker,
                "query": user_query,
                "data": {},
                "note": "All AIs will analyze this EXACT same data snapshot"
            }
            
            # TODO: Integrate with MCP Tools
            # For now, use placeholder data
            # In Step 2, this will be replaced with actual MCP tool calls
            
            # Placeholder data (will be replaced with MCP tool results)
            shared_context["data"] = {
                "current_price": "$6.50",
                "price_change_pct": "+2.5%",
                "volume": "1.2M",
                "market_cap": "$450M",
                "cash_position": "$45M",
                "quarterly_revenue": "$8.2M",
                "short_interest": "36.8%",
                "analyst_target": "$10.40",
                "_source": "placeholder (Step 1 - MCP integration pending)"
            }
            
            logger.info(f"Shared context prepared for {ticker} at {shared_context['timestamp']}")
            logger.info(f"Data points collected: {len(shared_context['data'])}")
            
            return shared_context
            
        except Exception as e:
            logger.error(f"Failed to prepare shared context: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {"error": str(e)}
    
    def _load_prompt(self, prompt_file: str) -> str:
        """Load prompt content from file"""
        try:
            prompt_path = PathManager.get_prompt_dir() / prompt_file
            
            if not prompt_path.exists():
                logger.error(f"Prompt file not found: {prompt_path}")
                return f"You are an AI assistant analyzing stocks."
            
            content = prompt_path.read_text(encoding='utf-8')
            logger.info(f"Loaded prompt: {prompt_file}")
            return content
            
        except Exception as e:
            logger.error(f"Failed to load prompt {prompt_file}: {e}")
            return f"You are an AI assistant analyzing stocks."
    
    async def run_debate(
        self,
        user_query: str,
        bull_ai_config: Dict[str, Any],
        bear_ai_config: Dict[str, Any],
        judge_ai_config: Dict[str, Any],
        parallel: bool = True,
        show_opinions: bool = True,
        progress_callback: Optional[callable] = None
    ) -> DebateResult:
        """
        Run Expert Debate with Bull, Bear, and Judge AIs
        
        Args:
            user_query: User's question (e.g., "Analyze IBRX stock")
            bull_ai_config: {"model": "gpt-4", "version": "latest"}
            bear_ai_config: {"model": "gemini-pro", "version": "latest"}
            judge_ai_config: {"model": "deepseek", "version": "latest"}
            parallel: If True, run Bull and Bear in parallel
            show_opinions: If True, include individual opinions in result
            progress_callback: Callback function for progress updates
        
        Returns:
            DebateResult with opinions and verdict
        
        Example:
            >>> result = await orchestrator.run_debate(
            ...     "Analyze IBRX stock",
            ...     {"model": "gpt-4", "version": "latest"},
            ...     {"model": "gemini-pro", "version": "latest"},
            ...     {"model": "deepseek", "version": "latest"}
            ... )
            >>> print(result.judge_verdict)
        """
        start_time = time.time()
        warnings = []
        
        logger.info(f"Starting Expert Debate for query: {user_query}")
        logger.info(f"Parallel mode: {parallel}")
        
        # ========================================
        # CRITICAL: Shared Context Preparation
        # ========================================
        # Bull과 Bear가 동일한 데이터를 보고 분석하도록
        # 데이터를 먼저 수집하여 Shared Context 생성
        logger.info("Preparing shared context for consistent analysis...")
        
        shared_context = await self._prepare_shared_context(user_query)
        
        if shared_context.get("error"):
            warnings.append(f"Failed to prepare shared context: {shared_context['error']}")
            logger.warning(f"Shared context preparation failed, proceeding with query only")
        else:
            logger.info(f"Shared context prepared: {len(shared_context.get('data', {}))} data points")
        
        # Load prompts
        bull_prompt = self._load_prompt(
            self.expert_profile["ai_roles"]["bull"]["prompt_file"]
        )
        bear_prompt = self._load_prompt(
            self.expert_profile["ai_roles"]["bear"]["prompt_file"]
        )
        judge_prompt = self._load_prompt(
            self.expert_profile["ai_roles"]["judge"]["prompt_file"]
        )
        
        # Step 1: Run Bull and Bear AIs
        if parallel:
            logger.info("Running Bull and Bear AIs in parallel")
            bull_result, bear_result = await self._run_bull_bear_parallel(
                user_query, bull_ai_config, bear_ai_config,
                bull_prompt, bear_prompt, progress_callback
            )
        else:
            logger.info("Running Bull and Bear AIs sequentially")
            bull_result, bear_result = await self._run_bull_bear_sequential(
                user_query, bull_ai_config, bear_ai_config,
                bull_prompt, bear_prompt, progress_callback
            )
        
        # Collect warnings from Bull and Bear
        if bull_result.status != AIStatus.SUCCESS:
            warning_msg = f"Bull AI {bull_result.status.value}: {bull_result.error_message}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        if bear_result.status != AIStatus.SUCCESS:
            warning_msg = f"Bear AI {bear_result.status.value}: {bear_result.error_message}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        # Step 2: Run Judge AI with Bull and Bear opinions
        if progress_callback:
            progress_callback("judge", "running", 0)
        
        judge_result = await self._run_judge(
            user_query, judge_ai_config, judge_prompt,
            bull_result, bear_result, progress_callback
        )
        
        if judge_result.status != AIStatus.SUCCESS:
            warning_msg = f"Judge AI {judge_result.status.value}: {judge_result.error_message}"
            warnings.append(warning_msg)
            logger.warning(warning_msg)
        
        # Calculate total execution time
        execution_time = time.time() - start_time
        
        # Determine overall status
        status = self._determine_status(bull_result, bear_result, judge_result)
        
        logger.info(f"Expert Debate completed in {execution_time:.2f}s with status: {status}")
        
        return DebateResult(
            bull_opinion=bull_result.data if show_opinions else None,
            bear_opinion=bear_result.data if show_opinions else None,
            judge_verdict=judge_result.data,
            execution_time=execution_time,
            warnings=warnings,
            status=status
        )
    
    async def _run_bull_bear_parallel(
        self,
        user_query: str,
        bull_config: Dict[str, Any],
        bear_config: Dict[str, Any],
        bull_prompt: str,
        bear_prompt: str,
        progress_callback: Optional[callable],
        shared_context: Optional[Dict[str, Any]] = None
    ) -> tuple[AIResult, AIResult]:
        """Run Bull and Bear AIs in parallel"""
        
        # Create AI functions
        async def bull_func():
            if progress_callback:
                progress_callback("bull", "running", 0)
            result = await self._call_ai(user_query, bull_config, bull_prompt, "Bull AI", shared_context)
            if progress_callback:
                progress_callback("bull", "done" if result.status == AIStatus.SUCCESS else "error", 100)
            return result
        
        async def bear_func():
            if progress_callback:
                progress_callback("bear", "running", 0)
            result = await self._call_ai(user_query, bear_config, bear_prompt, "Bear AI", shared_context)
            if progress_callback:
                progress_callback("bear", "done" if result.status == AIStatus.SUCCESS else "error", 100)
            return result
        
        # Run in parallel
        results = await self.ai_runner.run_parallel({
            "Bull AI": bull_func,
            "Bear AI": bear_func
        })
        
        return results["Bull AI"], results["Bear AI"]
    
    async def _run_bull_bear_sequential(
        self,
        user_query: str,
        bull_config: Dict[str, Any],
        bear_config: Dict[str, Any],
        bull_prompt: str,
        bear_prompt: str,
        progress_callback: Optional[callable],
        shared_context: Optional[Dict[str, Any]] = None
    ) -> tuple[AIResult, AIResult]:
        """Run Bull and Bear AIs sequentially"""
        
        # Run Bull AI first
        if progress_callback:
            progress_callback("bull", "running", 0)
        
        bull_result = await self._call_ai(user_query, bull_config, bull_prompt, "Bull AI", shared_context)
        
        if progress_callback:
            progress_callback("bull", "done" if bull_result.status == AIStatus.SUCCESS else "error", 100)
        
        # Then run Bear AI
        if progress_callback:
            progress_callback("bear", "running", 0)
        
        bear_result = await self._call_ai(user_query, bear_config, bear_prompt, "Bear AI", shared_context)
        
        if progress_callback:
            progress_callback("bear", "done" if bear_result.status == AIStatus.SUCCESS else "error", 100)
        
        return bull_result, bear_result
    
    async def _run_judge(
        self,
        user_query: str,
        judge_config: Dict[str, Any],
        judge_prompt: str,
        bull_result: AIResult,
        bear_result: AIResult,
        progress_callback: Optional[callable]
    ) -> AIResult:
        """Run Judge AI with Bull and Bear opinions"""
        
        # Prepare Judge prompt with Bull and Bear opinions
        judge_query = self._prepare_judge_query(
            user_query, bull_result, bear_result, judge_prompt
        )
        
        # Run Judge AI
        judge_result = await self._call_ai(
            judge_query, judge_config, judge_prompt, "Judge AI"
        )
        
        if progress_callback:
            progress_callback("judge", "done" if judge_result.status == AIStatus.SUCCESS else "error", 100)
        
        return judge_result
    
    def _prepare_judge_query(
        self,
        user_query: str,
        bull_result: AIResult,
        bear_result: AIResult,
        judge_prompt: str
    ) -> str:
        """Prepare query for Judge AI with Bull and Bear opinions"""
        
        query_parts = [f"Original Query: {user_query}\n"]
        
        # Add Bull opinion
        if bull_result.status == AIStatus.SUCCESS and bull_result.data:
            query_parts.append(f"\nBull AI Opinion:\n{bull_result.data}\n")
        else:
            query_parts.append(f"\nBull AI: Analysis failed ({bull_result.status.value})\n")
        
        # Add Bear opinion
        if bear_result.status == AIStatus.SUCCESS and bear_result.data:
            query_parts.append(f"\nBear AI Opinion:\n{bear_result.data}\n")
        else:
            query_parts.append(f"\nBear AI: Analysis failed ({bear_result.status.value})\n")
        
        query_parts.append("\nPlease provide your final verdict based on the above opinions.")
        
        return "".join(query_parts)
    
    async def _call_ai(
        self,
        query: str,
        ai_config: Dict[str, Any],
        prompt: str,
        ai_name: str,
        shared_context: Optional[Dict[str, Any]] = None
    ) -> AIResult:
        """
        Call AI with given configuration
        
        Args:
            query: User's question
            ai_config: AI configuration (model, version, timeout)
            prompt: System prompt for this AI role
            ai_name: Name of AI (for logging)
            shared_context: Shared data snapshot for consistent analysis
        
        Returns:
            AIResult with parsed JSON response
        """
        
        async def ai_func():
            """Actual AI call function"""
            if not self.ai_engine:
                raise RuntimeError("AI Engine not initialized. Set ai_engine in ExpertOrchestrator.")
            
            # Prepare full prompt with shared context
            full_prompt = self._inject_shared_context(prompt, shared_context)
            
            logger.info(f"[{ai_name}] Calling AI with model: {ai_config.get('model', 'unknown')}")
            
            # Call AI engine (synchronous, so we need to run in executor)
            import concurrent.futures
            loop = asyncio.get_event_loop()
            
            def sync_ai_call():
                """Synchronous AI call wrapper"""
                # Use process_chat with empty history for single-shot analysis
                response = self.ai_engine.process_chat(
                    message=query,
                    history_msgs=[],
                    all_openai_tools=[],  # No tools for Expert Edition
                    use_server=False,
                    tool_map={},
                    clients={},
                    system_prompt_override=full_prompt
                )
                return response.get("response", "")
            
            # Run in executor to avoid blocking
            ai_response = await loop.run_in_executor(None, sync_ai_call)
            
            logger.info(f"[{ai_name}] Received response ({len(ai_response)} chars)")
            
            # Parse JSON response
            parsed_data = self._parse_ai_response(ai_response, ai_name)
            
            # Add metadata
            parsed_data["model"] = ai_config.get("model", "unknown")
            parsed_data["version"] = ai_config.get("version", "unknown")
            parsed_data["raw_response"] = ai_response[:500]  # First 500 chars for debugging
            
            return parsed_data
        
        # Get timeout from config or use default
        timeout = ai_config.get("timeout", 120)
        
        # Run with timeout and retry
        result = await self.ai_runner.run_with_retry(
            ai_func, timeout=timeout, ai_name=ai_name
        )
        
        return result
    
    def _inject_shared_context(
        self,
        base_prompt: str,
        shared_context: Optional[Dict[str, Any]]
    ) -> str:
        """
        Inject shared context into prompt
        
        Args:
            base_prompt: Base system prompt
            shared_context: Shared data snapshot
        
        Returns:
            Full prompt with injected context
        """
        if not shared_context or shared_context.get("error"):
            return base_prompt
        
        # Format shared context as readable text
        context_text = "\n\n## SHARED DATA SNAPSHOT\n\n"
        context_text += f"**Timestamp**: {shared_context.get('timestamp', 'N/A')}\n"
        context_text += f"**Ticker**: {shared_context.get('ticker', 'N/A')}\n"
        context_text += f"**Note**: {shared_context.get('note', '')}\n\n"
        
        context_text += "### Market Data:\n"
        data = shared_context.get("data", {})
        for key, value in data.items():
            if not key.startswith("_"):  # Skip internal fields
                context_text += f"- **{key}**: {value}\n"
        
        context_text += "\n---\n\n"
        
        return context_text + base_prompt
    
    def _parse_ai_response(
        self,
        response: str,
        ai_name: str
    ) -> Dict[str, Any]:
        """
        Parse AI response into structured format
        
        Expected JSON format:
        {
            "conclusion": "buy" | "sell" | "hold",
            "reasoning": ["reason1", "reason2", ...],
            "confidence": 0-100,
            "key_points": ["point1", "point2", ...]
        }
        
        Args:
            response: Raw AI response
            ai_name: Name of AI (for logging)
        
        Returns:
            Parsed data dictionary
        """
        import json
        import re
        
        # Try to extract JSON from response
        # Look for JSON block (```json ... ```)
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # Look for raw JSON object
            json_match = re.search(r'\{[^{}]*"conclusion"[^{}]*\}', response, re.DOTALL)
            if json_match:
                json_str = json_match.group(0)
            else:
                # Fallback: treat entire response as reasoning
                logger.warning(f"[{ai_name}] No JSON found, using fallback parsing")
                return {
                    "conclusion": "unknown",
                    "reasoning": [response[:500]],  # First 500 chars
                    "confidence": 50,
                    "key_points": [],
                    "parse_error": "No JSON structure found"
                }
        
        try:
            data = json.loads(json_str)
            
            # Validate required fields
            if "conclusion" not in data:
                data["conclusion"] = "unknown"
            if "reasoning" not in data:
                data["reasoning"] = []
            if "confidence" not in data:
                data["confidence"] = 50
            
            logger.info(f"[{ai_name}] Parsed: {data.get('conclusion')} (confidence: {data.get('confidence')})")
            return data
            
        except json.JSONDecodeError as e:
            logger.error(f"[{ai_name}] JSON parse error: {e}")
            return {
                "conclusion": "unknown",
                "reasoning": [response[:500]],
                "confidence": 0,
                "key_points": [],
                "parse_error": str(e)
            }
    
    def _determine_status(
        self,
        bull_result: AIResult,
        bear_result: AIResult,
        judge_result: AIResult
    ) -> str:
        """Determine overall debate status"""
        
        success_count = sum([
            bull_result.status == AIStatus.SUCCESS,
            bear_result.status == AIStatus.SUCCESS,
            judge_result.status == AIStatus.SUCCESS
        ])
        
        if success_count == 3:
            return "success"
        elif success_count >= 1:
            return "partial_success"
        else:
            return "failed"
    
    def get_presets(self) -> Dict[str, Any]:
        """Get available AI configuration presets"""
        return self.expert_profile.get("presets", {})
    
    def apply_preset(self, preset_name: str) -> Dict[str, Dict[str, Any]]:
        """
        Apply a preset configuration
        
        Args:
            preset_name: Name of preset ("balanced", "premium", "fast", etc.)
        
        Returns:
            Dictionary with bull, bear, judge configurations
        """
        presets = self.get_presets()
        
        if preset_name not in presets:
            logger.warning(f"Preset '{preset_name}' not found, using 'balanced'")
            preset_name = "balanced"
        
        preset = presets[preset_name]
        logger.info(f"Applied preset: {preset_name}")
        
        return {
            "bull": preset["bull"],
            "bear": preset["bear"],
            "judge": preset["judge"]
        }


# Example usage
if __name__ == "__main__":
    async def example():
        orchestrator = ExpertOrchestrator()
        
        # Example 1: Run debate with balanced preset
        preset_config = orchestrator.apply_preset("balanced")
        
        result = await orchestrator.run_debate(
            user_query="Analyze IBRX stock",
            bull_ai_config=preset_config["bull"],
            bear_ai_config=preset_config["bear"],
            judge_ai_config=preset_config["judge"],
            parallel=True
        )
        
        print(f"Status: {result.status}")
        print(f"Execution time: {result.execution_time:.2f}s")
        print(f"Warnings: {result.warnings}")
        print(f"Judge verdict: {result.judge_verdict}")
    
    # Run example
    asyncio.run(example())
