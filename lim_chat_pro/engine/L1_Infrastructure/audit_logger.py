# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

"""
[L1 Infrastructure Layer - Audit Logger]
역할: 시스템 실행 이벤트를 JSONL 형식으로 기록합니다.
모든 도구 호출, 데이터 처리, 에러 등을 추적 가능하게 합니다.
"""

import json
import time
from pathlib import Path
import logging
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("LimChat.AuditLogger")

class AuditLogger:
    """JSONL 형식의 감사 로그 기록기"""
    
    def __init__(self, log_dir=None):
        """
        Args:
            log_dir: 로그 디렉토리 경로 (기본값: PathManager.get_history_dir())
        """
        if log_dir is None:
            self.log_dir = PathManager.get_history_dir()
        else:
            self.log_dir = Path(log_dir)
        
        self.log_dir.mkdir(exist_ok=True)
        self.log_file = self.log_dir / "audit.jsonl"
    
    def log(self, layer, event, **kwargs):
        """
        이벤트를 JSONL 형식으로 기록합니다.
        
        Args:
            layer: 발생 계층 (L1, L2, L3, L4, L5)
            event: 이벤트 타입 (tool_call, data_truncated, error, etc.)
            **kwargs: 추가 메타데이터
        """
        entry = {
            "ts": int(time.time() * 1000),
            "layer": layer,
            "event": event,
            **kwargs
        }
        
        try:
            with open(self.log_file, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        except Exception as e:
            logger.error(f"Failed to write audit log: {e}")
    
    def log_tool_call(self, tool_name, args, result=None, error=None):
        """도구 호출 이벤트 기록"""
        self.log(
            "L3",
            "tool_call",
            tool=tool_name,
            args=args,
            success=error is None,
            error=str(error) if error else None
        )
    
    def log_data_processing(self, original_size, processed_size, truncated=False):
        """데이터 처리 이벤트 기록"""
        self.log(
            "L2",
            "data_processing",
            original_size=original_size,
            processed_size=processed_size,
            truncated=truncated
        )
    
    def log_prompt_load(self, layer_name, char_count):
        """프롬프트 로딩 이벤트 기록"""
        self.log(
            "L4",
            "prompt_load",
            layer=layer_name,
            char_count=char_count
        )
    
    def log_error(self, layer, error_type, message, **kwargs):
        """에러 이벤트 기록"""
        self.log(
            layer,
            "error",
            error_type=error_type,
            message=message,
            **kwargs
        )

    def log_router_event(self, event_type: str, tool_name: str, reason: str = None, **kwargs):
        """
        RouterLock 이벤트 기록
        
        Args:
            event_type: "allowed" 또는 "blocked"
            tool_name: 도구 이름
            reason: 차단 이유 (blocked인 경우)
        """
        self.log(
            "L3",
            "router_event",
            event_type=event_type,
            tool=tool_name,
            reason=reason,
            **kwargs
        )
