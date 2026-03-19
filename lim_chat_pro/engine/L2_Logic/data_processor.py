# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

import json
import logging

logger = logging.getLogger("LimChat.DataProcessor")

class LimChatDataProcessor:
    """
    [L2 Logic Layer]
    역할: 도구 결과(Raw Data)를 AI가 이해하기 쉬운 형태로 정제합니다. 
    특히 주식 데이터의 경우 불필요한 필드를 제거하고 핵심 지표만 골라내어 토큰 지출을 줄입니다.
    """
    def __init__(self):
        # [IQ-Pack Architecture]
        # Dynamic loading of priority keys from active pack settings.
        # Fallback to legacy hardcoded keys if no pack is active.
        self.priority_keys = self._load_priority_keys()

    def _load_priority_keys(self):
        """
        Loads priority keys from active IQ-Pack's settings.json.
        
        [IQ-Pack Strict Mode]
        No fallback to legacy keys. If no pack is active or settings.json
        is missing, raises an error to enforce proper pack configuration.
        """
        from L1_Infrastructure.path_manager import PathManager
        
        settings_path = PathManager.get_settings_file()
        
        # [V5-D-12] Graceful Fallback: If no pack is active, use default keys instead of crashing.
        default_keys = [
            'symbol', 'ticker', 'price', 'name', 'Description', 'description', 
            'longBusinessSummary', 'content', 'full_text', 'summary', 'text',
            'market_cap', 'volume', 'date', 'time', 'raw_data'
        ]
        
        if not settings_path or not settings_path.exists():
            logger.info(f"[DataProcessor] No settings.json found or active_pack is None. Using {len(default_keys)} default fallback keys.")
            return default_keys
        
        try:
            import json
            with open(settings_path, 'r', encoding='utf-8') as f:
                settings = json.load(f)
                keys = settings.get("priority_keys")
                
                if not keys:
                    raise ValueError(
                        f"[DataProcessor] settings.json must contain 'priority_keys' array.\n"
                        f"File: {settings_path}"
                    )
                
                logger.info(f"[DataProcessor] Loaded {len(keys)} priority keys from {settings_path.name}")
                return keys
                
        except json.JSONDecodeError as e:
            raise ValueError(f"[DataProcessor] Invalid JSON in {settings_path}: {e}")
        except Exception as e:
            raise RuntimeError(f"[DataProcessor] Failed to load settings: {e}")


    def process_tool_result(self, res_data, max_length=100000):
        """도구 응답 데이터를 분석하여 중요 정보만 남기고 요약합니다."""
        original_json = json.dumps(res_data, ensure_ascii=False)
        original_size = len(original_json)
        
        if original_size <= max_length:
            return original_json

        logger.warning(f"Large data detected ({original_size} chars). Truncating based on priority keys.")

        if isinstance(res_data, dict):
            summary_data = {}
            source = res_data
            
            # 1. raw_data가 중첩된 경우 처리
            if 'raw_data' in res_data and isinstance(res_data['raw_data'], dict):
                source = res_data['raw_data']
            
            # 2. 우선순위 키 기반 추출
            for key in self.priority_keys:
                if key in source:
                    value = source[key]
                    # 설명글이나 문서 본문은 적절히 절사 (토큰 폭발 방지)
                    if key in ['Description', 'description', 'longBusinessSummary', 'content', 'full_text', 'summary', 'text'] and isinstance(value, str):
                        limit = 5000 if key in ['content', 'full_text', 'summary', 'text'] else 1000
                        if len(value) > limit: 
                            value = value[:limit] + f"... (Truncated, original size: {len(value)} chars)"
                    summary_data[key] = value
            
            summary_data['_truncated'] = True
            summary_data['_original_size'] = original_size
            return json.dumps(summary_data, ensure_ascii=False)
        else:
            # 리스트거나 다른 형식인 경우 단순 절사
            return original_json[:max_length] + "... (Truncated)"
    
    def process(self, data, max_length=100000):
        """
        Alias for process_tool_result() to maintain test compatibility.
        
        Args:
            data: Raw data from tools
            max_length: Maximum length of processed data
            
        Returns:
            Processed data as JSON string
        """
        return self.process_tool_result(data, max_length)
