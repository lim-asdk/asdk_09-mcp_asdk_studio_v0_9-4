# -*- coding: utf-8 -*-
# Project: lim_chat_v1_4
# Developer: Antigravity (Coding AI)
# Version: 1.4

from datetime import datetime
from pathlib import Path
import shutil
import json
import difflib
import logging

logger = logging.getLogger("LimChat.BackupManager")

class BackupManager:
    """
    [L2 Logic Layer]
    프롬프트 백업 및 복원을 관리하는 클래스입니다.
    데이터 무결성을 위해 복원 전 자동 백업 기능을 제공합니다.
    """
    
    def __init__(self, prompts_dir: str, backups_dir: str, history_file: str):
        self.prompts_dir = Path(prompts_dir)
        self.backups_dir = Path(backups_dir)
        self.history_file = Path(history_file)
        
        # 필요한 디렉토리 생성
        self.backups_dir.mkdir(parents=True, exist_ok=True)
        self.prompts_dir.mkdir(parents=True, exist_ok=True)
    
    def create_backup(self, layer_name: str, change_reason: str = "") -> str:
        """
        현재 프롬프트 파일의 백업을 생성합니다.
        
        Args:
            layer_name: 백업할 프롬프트 계층 이름 (예: 'L3_orchestration', 'L4_stock_analyst')
            change_reason: 변경 사유 (optional)
            
        Returns:
            str: 생성된 백업 파일 이름
        """
        source_file = self.prompts_dir / f"{layer_name}.md"
        
        if not source_file.exists():
            logger.error(f"Source file not found: {source_file}")
            raise FileNotFoundError(f"{source_file} not found")
        
        # 타임스탬프 생성 (초 단위까지 포함하여 충돌 방지)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_filename = f"{layer_name}_{timestamp}.md"
        backup_path = self.backups_dir / backup_filename
        
        # 파일 복사
        shutil.copy2(source_file, backup_path)
        logger.info(f"Backup created: {backup_filename}")
        
        # 이력 기록
        self._record_history({
            "timestamp": datetime.now().isoformat(),
            "layer": layer_name,
            "action": "backup",
            "backup_filename": backup_filename,
            "change_reason": change_reason
        })
        
        return backup_filename
    
    def restore_backup(self, backup_filename: str, create_backup_before: bool = True) -> bool:
        """
        백업 파일로부터 프롬프트를 복원합니다.
        
        Args:
            backup_filename: 복원할 백업 파일 이름
            create_backup_before: 복원 전 현재 상태를 백업할지 여부 (기본값 True)
            
        Returns:
            bool: 복원 성공 여부
        """
        backup_path = self.backups_dir / backup_filename
        
        if not backup_path.exists():
            logger.error(f"Backup file not found: {backup_path}")
            raise FileNotFoundError(f"Backup {backup_filename} not found")
        
        # 파일명에서 계층 이름 추출
        layer_name = self._extract_layer_name(backup_filename)
        target_file = self.prompts_dir / f"{layer_name}.md"
        
        # 복원 전 현재 상태 백업 (안전 장치)
        if create_backup_before and target_file.exists():
            self.create_backup(layer_name, f"Automatic backup before restoring {backup_filename}")
        
        # 복원 작업
        shutil.copy2(backup_path, target_file)
        logger.info(f"Restored {layer_name} from {backup_filename}")
        
        # 이력 기록
        self._record_history({
            "timestamp": datetime.now().isoformat(),
            "layer": layer_name,
            "action": "restore",
            "backup_filename": backup_filename
        })
        
        return True
    
    def get_diff(self, layer_name: str, backup_filename: str) -> str:
        """
        현재 프롬프트 파일과 특정 백업 파일 간의 차이점을 계산합니다.
        
        Args:
            layer_name: 비교할 프롬프트 계층 이름
            backup_filename: 비교할 백업 파일 이름
            
        Returns:
            str: Unified diff 형식의 문자열
        """
        current_file = self.prompts_dir / f"{layer_name}.md"
        backup_file = self.backups_dir / backup_filename
        
        if not current_file.exists():
            raise FileNotFoundError(f"Current file {current_file} not found")
        if not backup_file.exists():
            raise FileNotFoundError(f"Backup file {backup_file} not found")

        with open(current_file, 'r', encoding='utf-8') as f:
            current_lines = f.readlines()
        
        with open(backup_file, 'r', encoding='utf-8') as f:
            backup_lines = f.readlines()
        
        diff = difflib.unified_diff(
            backup_lines, 
            current_lines,
            lineterm='',
            fromfile=f"BACKUP: {backup_filename}",
            tofile=f"CURRENT: {layer_name}.md"
        )
        
        return '\n'.join(diff)

    def list_backups(self, layer_name: str = None, limit: int = None) -> list:
        """
        백업 파일 목록을 반환합니다.
        
        Args:
            layer_name: 특정 계층의 백업만 필터링 (optional)
            limit: 반환할 최대 개수 (optional)
            
        Returns:
            list: 백업 정보 딕셔너리 리스트
        """
        backups = []
        # 최신순 정렬
        files = sorted(self.backups_dir.glob("*.md"), key=lambda x: x.stat().st_mtime, reverse=True)
        
        for backup_file in files:
            extracted_layer = self._extract_layer_name(backup_file.name)
            if layer_name and extracted_layer != layer_name:
                continue
            
            backups.append({
                "filename": backup_file.name,
                "timestamp": datetime.fromtimestamp(backup_file.stat().st_mtime).isoformat(),
                "size": backup_file.stat().st_size,
                "layer": extracted_layer
            })
            if limit and len(backups) >= limit:
                break
        return backups

    def _extract_layer_name(self, filename: str) -> str:
        """파일명에서 계층 이름(L4_stock_analyst 등)을 추출합니다."""
        # 포맷: {layer_name}_{timestamp}.md (timestamp: %Y%m%d_%H%M%S)
        # '_'를 기준으로 뒤에서 두 부분을 제외한 나머지가 layer_name
        parts = filename.replace('.md', '').split('_')
        if len(parts) < 3:
            return parts[0] # Fallback
        return '_'.join(parts[:-2])

    def _record_history(self, entry: dict):
        """작업 이력을 JSON 파일에 기록합니다."""
        history = []
        if self.history_file.exists():
            try:
                with open(self.history_file, 'r', encoding='utf-8') as f:
                    history = json.load(f)
            except (json.JSONDecodeError, IOError):
                history = []
        
        history.append(entry)
        
        # 이력 파일 저장 (UTF-8, Indent 적용)
        try:
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(history, f, indent=2, ensure_ascii=False)
        except IOError as e:
            logger.error(f"Failed to record history: {e}")
