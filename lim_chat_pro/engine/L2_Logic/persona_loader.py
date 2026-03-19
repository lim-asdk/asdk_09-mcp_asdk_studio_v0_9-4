# -*- coding: utf-8 -*-
# Project: lim_chat_v2_0
# Developer: LIMHWACHAN
# Version: 2.0

"""
[L2 Logic Layer] PersonaLoader
역할: Persona (성격) 정보를 로드합니다.
Persona는 L2/L3/L4 프롬프트 경로와 capability_keywords를 포함합니다.
AI Profile (API 설정)과는 완전히 분리됩니다.
"""

import json
from pathlib import Path
from typing import Dict, Any, List
from L1_Infrastructure.path_manager import PathManager


class PersonaLoader:
    """
    Persona (성격) 로더
    
    Persona는 다음을 포함합니다:
    - name: 페르소나 이름
    - description: 설명
    - prompt_file: L4 프롬프트 파일 경로
    - l3_config: L3 오케스트레이션 프롬프트 경로 (선택)
    - l2_config: L2 데이터 처리 프롬프트 경로 (선택)
    - capability_keywords: 도구 바인딩용 키워드
    """
    
    def __init__(self, persona_dir: Path = None):
        """
        Initialize PersonaLoader.
        
        Args:
            persona_dir: Persona JSON 파일이 있는 디렉토리
                        None이면 PathManager에서 자동으로 가져옴
        """
        if persona_dir is None:
            # 기본값: data/prompts/{version}/ 디렉토리 사용
            # 각 버전의 BridgeAPI에서 오버라이드
            self.persona_dir = PathManager.get_prompt_dir()
        else:
            self.persona_dir = persona_dir
    
    def list_personas(self) -> List[str]:
        """
        사용 가능한 Persona 목록을 반환합니다.
        
        Returns:
            Persona ID 리스트 (예: ["stock_analyst", "economist"])
        """
        if not self.persona_dir.exists():
            return []
        
        personas = []
        for file in self.persona_dir.glob("persona_*.json"):
            # persona_stock_analyst.json -> stock_analyst
            persona_id = file.stem.replace("persona_", "")
            personas.append(persona_id)
        
        return sorted(personas)
    
    def load_persona(self, persona_id: str) -> Dict[str, Any]:
        """
        특정 Persona를 로드합니다.
        
        Args:
            persona_id: Persona ID (예: "stock_analyst")
        
        Returns:
            Persona 설정 딕셔너리
        
        Raises:
            FileNotFoundError: Persona 파일이 없을 때
            ValueError: JSON이 유효하지 않을 때
        """
        persona_path = self.persona_dir / f"persona_{persona_id}.json"
        
        if not persona_path.exists():
            raise FileNotFoundError(f"Persona not found: {persona_id} at {persona_path}")
        
        try:
            with open(persona_path, "r", encoding="utf-8") as f:
                data = json.load(f)
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in persona {persona_id}: {e}")
        
        self._validate_persona(data)
        
        # 프롬프트 파일 경로 해석
        if "prompt_file" in data:
            data["prompt_file_path"] = str(PathManager.PROJECT_ROOT / data["prompt_file"])
        
        if "l3_config" in data:
            data["l3_config_path"] = str(PathManager.PROJECT_ROOT / data["l3_config"])
        
        if "l2_config" in data:
            data["l2_config_path"] = str(PathManager.PROJECT_ROOT / data["l2_config"])
        
        return data
    
    def _validate_persona(self, data: Dict[str, Any]):
        """Persona 데이터 유효성 검사"""
        required_fields = ["name", "description", "prompt_file", "capability_keywords"]
        missing = [field for field in required_fields if field not in data]
        
        if missing:
            raise ValueError(f"Missing required fields in persona: {', '.join(missing)}")
        
        if not isinstance(data["capability_keywords"], list):
            raise ValueError("capability_keywords must be a list")
    
    def save_persona(self, persona_id: str, data: Dict[str, Any]):
        """
        Persona를 저장합니다.
        
        Args:
            persona_id: Persona ID
            data: Persona 데이터
        """
        self._validate_persona(data)
        
        persona_path = self.persona_dir / f"persona_{persona_id}.json"
        
        with open(persona_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)
