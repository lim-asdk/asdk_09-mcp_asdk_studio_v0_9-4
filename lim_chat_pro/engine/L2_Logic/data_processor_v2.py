# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

"""
[L2 Logic Layer - Pydantic Wrapper]
역할: 기존 data_processor.py를 감싸는 래퍼
기존 코드는 전혀 수정하지 않음
"""

from L2_Logic.data_processor import LimChatDataProcessor as LegacyProcessor
import logging

logger = logging.getLogger("LimChat.DataProcessorV2")

# Pydantic는 선택적 import (없어도 동작)
try:
    from docs.standards.protocol_schema import MessageEnvelope, UpPayload
    PYDANTIC_AVAILABLE = True
except ImportError:
    PYDANTIC_AVAILABLE = False
    logger.warning("Pydantic not available. Using legacy mode.")


class LimChatDataProcessorV2(LegacyProcessor):
    """
    Pydantic 지원 래퍼
    use_schema=False면 기존 방식 그대로 사용
    """
    
    def __init__(self, use_schema=False):
        super().__init__()
        self.use_schema = use_schema and PYDANTIC_AVAILABLE
        
        if use_schema and not PYDANTIC_AVAILABLE:
            logger.warning("Pydantic not installed. Falling back to legacy mode.")
            self.use_schema = False
    
    def process_tool_result(self, raw_data):
        """
        기존 메서드를 오버라이드하되, 플래그로 동작 선택
        """
        if not self.use_schema:
            # 기존 방식 그대로 (부모 클래스 호출)
            return super().process_tool_result(raw_data)
        
        # Pydantic 방식 (새로운 기능)
        try:
            return self._process_with_schema(raw_data)
        except Exception as e:
            # Pydantic 실패 시 기존 방식으로 폴백
            logger.error(f"Pydantic processing failed: {e}. Falling back to legacy.")
            return super().process_tool_result(raw_data)
    
    def _process_with_schema(self, raw_data):
        """Pydantic 스키마 사용 (신규)"""
        # 신뢰도 계산
        confidence = self._calculate_confidence(raw_data)
        
        # 요약 생성 (기존 로직 재사용)
        summary = self._summarize_data(raw_data)
        
        # Pydantic 검증
        payload = UpPayload(
            status="SUCCESS" if raw_data else "FAIL",
            raw_data_snapshot=raw_data,
            insight_summary=summary,
            confidence_score=confidence
        )
        
        envelope = MessageEnvelope(
            sender="L2_Logic",
            receiver="L3_Engine",
            message_type="UP_REPORT",
            payload=payload.dict()
        )
        
        logger.info(f"[Pydantic] Processed with confidence: {confidence}")
        return envelope.dict()
    
    def _calculate_confidence(self, data):
        """신뢰도 계산 (신규 기능)"""
        if not data:
            return 0
        if isinstance(data, dict):
            field_count = len(data)
            if field_count > 10:
                return 95
            elif field_count > 5:
                return 80
            else:
                return 60
        return 50
    
    def _summarize_data(self, data):
        """기존 요약 로직 재사용"""
        result = super().process_tool_result(data)
        if isinstance(result, str):
            return result[:200]
        return str(result)[:200]
