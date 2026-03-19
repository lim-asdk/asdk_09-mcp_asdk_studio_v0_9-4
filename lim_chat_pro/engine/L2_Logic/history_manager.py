# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

import json
import os
import time
from pathlib import Path
from L1_Infrastructure.path_manager import PathManager

class HistoryManager:
    """
    [L2 Logic Layer]
    역할: 대화 기록(Chat History)의 영속성(Persistence)을 관리합니다.
    JSON 파일 형태로 세션을 저장하고, 이전 대화 목록을 불러오는 기능을 제공합니다.
    """
    def __init__(self, history_dir=None):
        # [PathManager] 중앙 집중식 경로 관리
        if history_dir:
            self.history_dir = Path(history_dir)
        else:
            self.history_dir = PathManager.get_history_dir()
            
        # PathManager 내부에서 mkdir을 수행하지만, 안전을 위해 확인
        if not self.history_dir.exists():
            self.history_dir.mkdir(parents=True, exist_ok=True)
            
        self.current_session_file = None

    def start_new_session(self):
        """새 세션 파일을 생성합니다."""
        timestamp = int(time.time() * 1000)
        filename = f"chat_{timestamp}.json"
        self.current_session_file = self.history_dir / filename
        self.save_history([]) # 초기 빈 리스트 저장
        return filename

    def save_history(self, messages):
        """메시지 리스트를 현재 세션 파일에 저장합니다."""
        if not self.current_session_file:
            self.start_new_session()
        
        try:
            with open(self.current_session_file, 'w', encoding='utf-8') as f:
                json.dump(messages, f, ensure_ascii=False, indent=2)
        except Exception as e:
            pass

    def load_history(self, filename):
        """특정 파일로부터 히스토리를 불러옵니다."""
        try:
            path = self.history_dir / filename
            if path.exists():
                with open(path, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            pass
        return []

    def get_history_list(self):
        """사용 가능한 히스토리 세션 목록을 반환합니다."""
        files = []
        for f in self.history_dir.glob("chat_*.json"):
            try:
                ts = int(f.stem.split('_')[1])
                files.append({
                    "filename": f.name,
                    "timestamp": ts,
                    "display": time.strftime('%Y-%m-%d %H:%M', time.localtime(ts / 1000))
                })
            except:
                pass
        # 최신순 정렬
        # 최신순 정렬
        files.sort(key=lambda x: x['timestamp'], reverse=True)
        return files

    def clear_all_history(self):
        """모든 히스토리 파일을 삭제합니다."""
        for f in self.history_dir.glob("chat_*.json"):
            try:
                os.remove(f)
            except Exception as e:
                pass
        self.current_session_file = None
        return True

    def delete_history(self, filename):
        """특정 히스토리 파일을 삭제합니다."""
        try:
            target = self.history_dir / filename
            if target.exists():
                os.remove(target)
                if self.current_session_file and self.current_session_file.name == filename:
                    self.current_session_file = None
                return True
        except Exception as e:
            pass
        return False
