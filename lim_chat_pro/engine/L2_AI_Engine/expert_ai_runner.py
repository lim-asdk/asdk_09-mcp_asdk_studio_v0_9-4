# Project: lim_chat_v2_0
# Developer: LIMHWACHAN
# Version: Expert Edition 1.0

"""
🎯 Expert AI Runner - Fault-Tolerant AI Execution Engine

This module provides robust AI execution with:
- Timeout mechanisms (prevent infinite loops)
- Retry logic (handle transient failures)
- Fallback strategies (continue on partial failures)
- Version-specific AI management (GPT-4 ≠ GPT-4o)
"""

import asyncio
import logging
import time
from typing import Dict, Any, Optional, Callable
from dataclasses import dataclass
from enum import Enum

logger = logging.getLogger("LimChat.Expert.AIRunner")


class AIStatus(Enum):
    """AI execution status"""
    SUCCESS = "success"
    TIMEOUT = "timeout"
    ERROR = "error"
    RETRY = "retry"


@dataclass
class AIResult:
    """AI execution result"""
    status: AIStatus
    data: Optional[Dict[str, Any]]
    execution_time: float
    error_message: Optional[str] = None
    retry_count: int = 0


class ExpertAIRunner:
    """
    Fault-tolerant AI execution engine for Expert Edition
    
    Features:
    - Timeout protection (prevent infinite loops)
    - Automatic retry on transient failures
    - Version-specific AI instance management
    - Detailed execution logging
    """
    
    def __init__(self, default_timeout: int = 120, max_retries: int = 2):
        """
        Initialize Expert AI Runner
        
        Args:
            default_timeout: Default timeout in seconds (default: 120s = 2 minutes)
            max_retries: Maximum retry attempts (default: 2)
        """
        self.default_timeout = default_timeout
        self.max_retries = max_retries
        self.ai_instances = {}  # Cache AI instances by identifier
        
        logger.info(f"ExpertAIRunner initialized (timeout={default_timeout}s, retries={max_retries})")
    
    def get_ai_identifier(self, model: str, version: str) -> str:
        """
        Generate unique identifier for AI model + version
        
        Args:
            model: AI model name (e.g., "gpt-4", "gemini-pro")
            version: Model version (e.g., "0613", "latest")
        
        Returns:
            Unique identifier (e.g., "gpt-4-0613")
        
        Example:
            >>> runner.get_ai_identifier("gpt-4", "0613")
            "gpt-4-0613"
            >>> runner.get_ai_identifier("gpt-4o", "2024-05-13")
            "gpt-4o-20240513"
        """
        # Remove dots and special characters from version
        clean_version = version.replace(".", "").replace("-", "")
        return f"{model}-{clean_version}"
    
    async def run_with_timeout(
        self,
        ai_func: Callable,
        timeout: Optional[int] = None,
        ai_name: str = "AI"
    ) -> AIResult:
        """
        Execute AI function with timeout protection
        
        Args:
            ai_func: Async function to execute
            timeout: Timeout in seconds (uses default if None)
            ai_name: AI name for logging
        
        Returns:
            AIResult with status and data
        
        Example:
            >>> async def my_ai_call():
            ...     return {"conclusion": "buy"}
            >>> result = await runner.run_with_timeout(my_ai_call, timeout=60)
        """
        timeout = timeout or self.default_timeout
        start_time = time.time()
        
        logger.info(f"{ai_name} execution started (timeout={timeout}s)")
        
        try:
            # Execute with timeout
            data = await asyncio.wait_for(ai_func(), timeout=timeout)
            execution_time = time.time() - start_time
            
            logger.info(f"{ai_name} completed successfully ({execution_time:.2f}s)")
            
            return AIResult(
                status=AIStatus.SUCCESS,
                data=data,
                execution_time=execution_time
            )
            
        except asyncio.TimeoutError:
            execution_time = time.time() - start_time
            logger.warning(f"{ai_name} TIMEOUT after {timeout}s - continuing without this AI")
            
            return AIResult(
                status=AIStatus.TIMEOUT,
                data=None,
                execution_time=execution_time,
                error_message=f"Timeout after {timeout}s"
            )
            
        except Exception as e:
            execution_time = time.time() - start_time
            logger.error(f"{ai_name} ERROR: {str(e)} - continuing")
            
            return AIResult(
                status=AIStatus.ERROR,
                data=None,
                execution_time=execution_time,
                error_message=str(e)
            )
    
    async def run_with_retry(
        self,
        ai_func: Callable,
        timeout: Optional[int] = None,
        max_retries: Optional[int] = None,
        ai_name: str = "AI"
    ) -> AIResult:
        """
        Execute AI function with retry logic
        
        Args:
            ai_func: Async function to execute
            timeout: Timeout in seconds
            max_retries: Maximum retry attempts (uses default if None)
            ai_name: AI name for logging
        
        Returns:
            AIResult with status and data
        
        Retry Strategy:
            - Retry on network errors, rate limits
            - Do NOT retry on timeout (already waited long enough)
            - 1 second delay between retries
        """
        max_retries = max_retries or self.max_retries
        retry_count = 0
        
        while retry_count <= max_retries:
            result = await self.run_with_timeout(ai_func, timeout, ai_name)
            
            # Success - return immediately
            if result.status == AIStatus.SUCCESS:
                result.retry_count = retry_count
                return result
            
            # Timeout - do NOT retry (already waited long enough)
            if result.status == AIStatus.TIMEOUT:
                logger.warning(f"{ai_name} timeout - no retry")
                result.retry_count = retry_count
                return result
            
            # Error - retry if attempts remaining
            if result.status == AIStatus.ERROR:
                retry_count += 1
                
                if retry_count <= max_retries:
                    logger.info(f"{ai_name} retrying ({retry_count}/{max_retries})...")
                    await asyncio.sleep(1)  # Wait 1 second before retry
                else:
                    logger.warning(f"{ai_name} failed after {max_retries} retries")
                    result.retry_count = retry_count - 1
                    return result
        
        # Should never reach here
        return result
    
    async def run_parallel(
        self,
        ai_funcs: Dict[str, Callable],
        timeout: Optional[int] = None
    ) -> Dict[str, AIResult]:
        """
        Execute multiple AI functions in parallel
        
        Args:
            ai_funcs: Dictionary of {ai_name: ai_function}
            timeout: Timeout for each AI
        
        Returns:
            Dictionary of {ai_name: AIResult}
        
        Example:
            >>> results = await runner.run_parallel({
            ...     "Bull AI": bull_func,
            ...     "Bear AI": bear_func
            ... })
            >>> print(results["Bull AI"].status)
            AIStatus.SUCCESS
        """
        logger.info(f"Starting parallel execution of {len(ai_funcs)} AIs")
        
        # Create tasks for all AIs
        tasks = {
            name: self.run_with_retry(func, timeout, ai_name=name)
            for name, func in ai_funcs.items()
        }
        
        # Execute all in parallel
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # Map results back to names
        result_dict = {}
        for (name, _), result in zip(tasks.items(), results):
            if isinstance(result, Exception):
                logger.error(f"{name} raised exception: {result}")
                result_dict[name] = AIResult(
                    status=AIStatus.ERROR,
                    data=None,
                    execution_time=0.0,
                    error_message=str(result)
                )
            else:
                result_dict[name] = result
        
        # Log summary
        success_count = sum(1 for r in result_dict.values() if r.status == AIStatus.SUCCESS)
        logger.info(f"Parallel execution completed: {success_count}/{len(ai_funcs)} successful")
        
        return result_dict
    
    def get_ai_instance(self, model: str, version: str, config: Dict[str, Any]):
        """
        Get or create AI instance for specific model + version
        
        Args:
            model: AI model name
            version: Model version
            config: AI configuration
        
        Returns:
            AI instance (cached for reuse)
        
        Note:
            Same model with different versions are treated as SEPARATE instances
            Example: GPT-4 (0613) ≠ GPT-4 (1106)
        """
        identifier = self.get_ai_identifier(model, version)
        
        if identifier not in self.ai_instances:
            logger.info(f"Creating new AI instance: {identifier}")
            # TODO: Implement actual AI instance creation
            # This will be integrated with existing AI engine
            self.ai_instances[identifier] = {
                "model": model,
                "version": version,
                "config": config,
                "identifier": identifier
            }
        
        return self.ai_instances[identifier]
    
    def clear_cache(self):
        """Clear AI instance cache"""
        logger.info(f"Clearing AI instance cache ({len(self.ai_instances)} instances)")
        self.ai_instances.clear()


# Example usage
if __name__ == "__main__":
    async def example():
        runner = ExpertAIRunner(default_timeout=10, max_retries=2)
        
        # Example 1: Simple execution with timeout
        async def fast_ai():
            await asyncio.sleep(1)
            return {"conclusion": "buy", "confidence": 85}
        
        result = await runner.run_with_timeout(fast_ai, ai_name="Fast AI")
        print(f"Fast AI result: {result.status}, time: {result.execution_time:.2f}s")
        
        # Example 2: Timeout scenario
        async def slow_ai():
            await asyncio.sleep(15)  # Exceeds 10s timeout
            return {"conclusion": "sell"}
        
        result = await runner.run_with_timeout(slow_ai, ai_name="Slow AI")
        print(f"Slow AI result: {result.status}, error: {result.error_message}")
        
        # Example 3: Parallel execution
        async def bull_ai():
            await asyncio.sleep(2)
            return {"conclusion": "buy"}
        
        async def bear_ai():
            await asyncio.sleep(3)
            return {"conclusion": "sell"}
        
        results = await runner.run_parallel({
            "Bull AI": bull_ai,
            "Bear AI": bear_ai
        })
        
        for name, result in results.items():
            print(f"{name}: {result.status}, time: {result.execution_time:.2f}s")
    
    # Run example
    asyncio.run(example())
