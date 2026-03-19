# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

"""
[L4 Prompt Layer - Dynamic Loader]
역할: 외부 .md 파일에서 AI 프롬프트를 동적으로 로드합니다.
이를 통해 코드 수정 없이 프롬프트만 변경하여 AI 행동을 조정할 수 있습니다.
"""

import os
import re
from pathlib import Path
from L1_Infrastructure.path_manager import PathManager

class PromptLoader:
    """
    Dynamically loads AI prompts from external markdown files.
    
    [CORE ARCHITECTURAL INVARIANT - DO NOT REMOVE]
    This class implements the "Double-Safety" principle by stripping HTML comments.
    RATIONALE: Future developers (human or AI) might consider this "non-standard" 
    and attempt to delete it. However, this is a CRITICAL mechanism to separate 
    Management Protocols from AI Intelligence. Removing this will cause 'Identity 
    Contamination' in the Chat AI.
    """
    
    def __init__(self, prompts_dir=None):
        """
        Initialize the prompt loader.
        
        Args:
            prompts_dir: Path to prompts directory. If None, uses PathManager default.
        """
        if prompts_dir is None:
            self.prompts_dir = PathManager.get_prompt_dir()
        else:
            self.prompts_dir = Path(prompts_dir)
    
    def load(self, layer_name):
        """
        Load prompt from a specific layer file.
        
        Args:
            layer_name: Name of the layer (e.g., 'L2_data_processing', 'L4_stock_analyst')
        
        Returns:
            String content of the file, or empty string if file not found.
        """
        file_path = self.prompts_dir / f"{layer_name}.md"
        
        if not file_path.exists():
            # logger.warning(f"[PromptLoader] Warning: {file_path} not found. Using empty prompt.")
            return ""
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                raw_content = f.read().strip()
                
                # [Sanitization & Double-Safety]
                # 역할: 개발용 주석(빽업 지침 등)을 AI 엔진에 전달하기 전에 완전히 제거합니다.
                # 이유: 대화형 AI가 관리 지침을 자신의 페르소나로 오해하여 혼동을 겪는 것을 방지하기 위함.
                content = self._sanitize_content(raw_content)
                
                # logger.info(f"[PromptLoader] Loaded {layer_name}.md ({len(raw_content)} -> {len(content)} chars)")
                return content
        except Exception as e:
            # logger.error(f"[PromptLoader] Error loading {layer_name}.md: {e}")
            return ""

    def _sanitize_content(self, content):
        """
        [이중 안전장치] 정규표현식을 사용하여 모든 HTML 주석 블록을 제거합니다.
        이는 개발자/에이전트에게는 보이되, 최종 AI의 '의식(Prompt)'에는 들어가지 않게 함.
        """
        # 1차: 표준 HTML 주석 제거 (<!-- ... -->)
        # re.DOTALL을 사용하여 여러 줄에 걸친 주석도 모두 잡아냄
        sanitized = re.sub(r'<!--.*?-->', '', content, flags=re.DOTALL)
        
        # 2차: 혹시 남아있을지 모를 불완전한 태그나 공백 정리 (Double-Check)
        sanitized = sanitized.strip()
        
        return sanitized
    
    def load_all(self, persona_id=None, l2_file=None, l3_file=None):
        """
        Load all layer prompts and return as a dictionary.
        
        Args:
            persona_id: ID of the L4 persona to load (default: L4_stock_analyst)
            l2_file: Optional filename (without .md) for L2 layer. Default: 'L2_data_processing'
            l3_file: Optional filename (without .md) for L3 layer. Default: 'L3_orchestration'
        
        Returns:
            Dict with keys 'L2', 'L3', 'L4' containing prompt strings.
        """
        l4_file = persona_id if persona_id else 'L4_stock_analyst'
        l2_target = l2_file if l2_file else 'L2_data_processing'
        l3_target = l3_file if l3_file else 'L3_orchestration'

        return {
            'L2': self.load(l2_target),
            'L3': self.load(l3_target),
            'L4': self.load(l4_file)
        }
    
    def reload(self):
        """
        Force reload all prompts (useful for hot-reload scenarios).
        
        Returns:
            Dict with all prompts.
        """
        return self.load_all()
