# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

"""
[L3 Orchestration Layer - Tool Router]
역할: 의도별 도구 사용 제한 (화이트리스트 기반)
AI가 호출하려는 도구를 필터링하여 통제된 범위 내에서만 실행되도록 합니다.
"""

import logging

logger = logging.getLogger("LimChat.ToolRouter")

# 의도별 허용 도구 화이트리스트
TOOL_WHITELIST = {
    "stock_analysis": [], # Deprecated: Whitelist disabled for general purpose
    "general_chat": [],
    "test_mode": []
}

class ToolRouter:
    """
    [도구 라우터 (Universal Mode)]
    역할: 모든 도구의 실행을 허용합니다 (범용성 확보).
    기존의 화이트리스트 차단 로직은 제거되었으며, 의도 감지는 로깅 목적으로만 사용됩니다.
    [Updated for IQ-Pack]: Loads intent keywords dynamically from active pack.
    """
    
    def __init__(self, whitelist=None, strict_mode=False):
        self.whitelist = whitelist or TOOL_WHITELIST
        self.strict_mode = strict_mode
        self.disabled_tools = []

    def filter_tool_calls(self, intent, tool_calls):
        if not tool_calls:
            return []
        if self.strict_mode:
            allowed_names = self.whitelist.get(intent, [])
            filtered = [tc for tc in tool_calls if tc.function.name in allowed_names]
            logger.info(f"[ToolRouter] Strict Mode: intent={intent}, filtered={len(tool_calls)}->{len(filtered)}")
            tool_calls = filtered
        if self.disabled_tools:
            tool_calls = [tc for tc in tool_calls if tc.function.name not in self.disabled_tools]
        logger.info(f"[ToolRouter] Intent '{intent}': pass {len(tool_calls)} tools")
        return tool_calls
    
    def detect_intent(self, message):
        """
        Detects user intent from message using IQ-Pack's intent_map.json.
        
        [IQ-Pack Strict Mode]
        No fallback to legacy keywords. If no pack is active or intent_map.json
        is missing, raises an error to enforce proper pack configuration.
        """
        message_lower = message.lower()
        
        # Load dynamic intent map from active pack
        intent_map = self._load_intent_map()
        
        # [V5-D-14] Graceful Fallback: If no pack is active, use general_chat instead of crashing.
        if not intent_map:
            logger.info("[ToolRouter] No intent_map.json found or active_pack is None. Using 'general_chat' as fallback.")
            return "general_chat"
        
        # Dynamic Detection Logic
        for intent_id, intent_info in intent_map.get("intents", {}).items():
            keywords = intent_info.get("keywords", [])
            for keyword in keywords:
                if keyword in message_lower:
                    logger.info(f"[ToolRouter] Detected intent: {intent_info.get('name')} (keyword: {keyword})")
                    return intent_info.get("name", "general_chat")
        
        # Default: general conversation
        logger.info("[ToolRouter] No specific intent detected, using general_chat")
        return "general_chat"

    def _load_intent_map(self):
        """Loads intent map from active pack or returns None."""
        from L1_Infrastructure.path_manager import PathManager
        map_path = PathManager.get_intent_map_file()
        
        if map_path and map_path.exists():
            try:
                import json
                with open(map_path, 'r', encoding='utf-8-sig') as f:
                    return json.load(f)
            except Exception as e:
                logger.error(f"[ToolRouter] Failed to load intent map: {e}")
        return None
    
    def get_available_tools(self, intent="general_chat"):
        """
        Get list of available tools for given intent.
        
        Args:
            intent: User intent (e.g., "stock_analysis", "general_chat")
            
        Returns:
            List of tool names available for this intent.
            In universal mode, returns empty list (all tools allowed).
        """
        # Universal mode: 모든 도구 허용이므로 화이트리스트 반환
        return self.whitelist.get(intent, [])


# ============================================================================
# RouterLock: Hot-Swappable Intelligence Security Layer
# ============================================================================

import json
from datetime import datetime
from typing import List, Dict, Any, Set

from L1_Infrastructure.audit_logger import AuditLogger

logger_lock = logging.getLogger("LimChat.RouterLock")


class RouterLock:
    """
    [Hot-Swappable Intelligence - Security Layer]
    역할: AI 환각으로 인한 허용되지 않은 도구 호출을 물리적으로 차단하고 기록합니다.
    
    Features:
    - JSON 로그 출력 (ELK/Splunk 연동 가능)
    - 차단된 호출 상세 추적 (blocked_calls 리스트)
    - Malformed call 감지 및 별도 처리
    - 보안 보고서 생성 (get_security_report)
    """
    
    def __init__(self, allowed_tools: List[str]):
        """
        RouterLock 초기화
        
        Args:
            allowed_tools: 허용된 도구 이름 리스트 (예: ["get_stock_quote", "search_news"])
        """
        self.allowed_tools: Set[str] = set(allowed_tools or [])
        self.allow_all: bool = (len(self.allowed_tools) == 0) or ("*" in self.allowed_tools) or ("any" in self.allowed_tools)
        self.violation_count: int = 0
        self.blocked_calls: List[Dict[str, Any]] = []
        self.audit_logger = AuditLogger()
    
    def _log(self, level: str, payload: dict):
        """JSON 로그를 한 줄에 출력 및 감사 로그 기록"""
        logger_lock.log(getattr(logging, level.upper()), json.dumps(payload, ensure_ascii=False))
        
        # 감사 로그 연동
        event_type = "allowed" if "Allowed" in payload.get("msg", "") else "blocked"
        self.audit_logger.log_router_event(
            event_type=event_type,
            tool_name=payload.get("tool_name"),
            reason=payload.get("reason"),
            request_id=payload.get("request_id")
        )
    
    def check_and_filter(self, tool_calls) -> List:
        """
        도구 호출 목록을 검사하고, 허용되지 않은 것은 차단 및 기록합니다.
        
        Args:
            tool_calls: LLM이 생성한 도구 호출 리스트
        
        Returns:
            검증된(Safe) 도구 호출 리스트
        """
        if not tool_calls:
            return []
        
        safe_calls = []
        
        for call in tool_calls:
            # 안전한 tool_name 추출
            tool_name = None
            if hasattr(call, 'function') and call.function is not None:
                tool_name = call.function.name if hasattr(call.function, 'name') else None
            elif hasattr(call, 'get'):
                tool_name = call.get("function", {}).get("name")
            
            call_id = call.id if hasattr(call, 'id') else call.get("id", "unknown") if hasattr(call, 'get') else "unknown"
            
            meta = {
                "request_id": call_id,
                "tool_name": tool_name,
                "timestamp": datetime.utcnow().isoformat() + "Z",
            }
            
            if tool_name is None:
                # 구조적 오류 (Malformed Call)
                self.violation_count += 1
                meta["reason"] = "malformed_call_missing_name"
                self.blocked_calls.append(meta)
                self._log("ERROR", {"msg": "🚫 [Blocked] Malformed tool call", **meta})
                continue
            
            if self.allow_all or tool_name in self.allowed_tools:
                safe_calls.append(call)
                self._log("INFO", {"msg": f"✅ [Allowed] {tool_name}", **meta})
            else:
                self.violation_count += 1
                meta["reason"] = "not_in_whitelist"
                self.blocked_calls.append(meta)
                self._log("WARNING", {"msg": f"🚫 [Blocked] Un-allowed tool: {tool_name}", **meta})
        
        return safe_calls
    
    def get_security_report(self) -> str:
        """차단된 호출 요약 및 상세 리스트 반환"""
        report = {
            "violations": self.violation_count,
            "blocked_calls": self.blocked_calls
        }
        return json.dumps(report, ensure_ascii=False, indent=2)
