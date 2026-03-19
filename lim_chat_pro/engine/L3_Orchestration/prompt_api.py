# -*- coding: utf-8 -*-
# Project: lim_chat_v1_4
# Developer: Antigravity (Coding AI)
# Version: 1.4

from flask import Blueprint, request, jsonify
from pathlib import Path
import logging
import os
import json
from L1_Infrastructure.audit_logger import AuditLogger

# 내부 로직 임포트
from L2_Logic.backup_manager import BackupManager
from L1_Infrastructure.path_manager import PathManager

logger = logging.getLogger("LimChat.PromptAPI")
_audit = AuditLogger()

# Flask Blueprint 생성
prompt_api_bp = Blueprint('prompt_api', __name__)

# 경로 설정
PROMPTS_DIR = PathManager.get_prompt_dir()
BACKUPS_DIR = PROMPTS_DIR / "backups"
HISTORY_FILE = PathManager.PROJECT_ROOT / "data" / "prompt_history.json"

# BackupManager 초기화
backup_manager = BackupManager(
    prompts_dir=str(PROMPTS_DIR),
    backups_dir=str(BACKUPS_DIR),
    history_file=str(HISTORY_FILE)
)

@prompt_api_bp.route('/api/prompts/<layer>', methods=['GET'])
def get_prompt(layer):
    """특정 계층의 프롬프트 내용을 가져옵니다."""
    try:
        file_path = PROMPTS_DIR / f"{layer}.md"
        if not file_path.exists():
            return jsonify({"error": "Prompt file not found"}), 404
        
        content = file_path.read_text(encoding='utf-8')
        _audit.log("L4", "prompt_get", layer=layer, ok=True)
        return jsonify({
            "layer": layer,
            "content": content
        })
    except Exception as e:
        logger.error(f"Failed to get prompt '{layer}': {e}")
        _audit.log("L4", "prompt_get", layer=layer, ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500

@prompt_api_bp.route('/api/prompts/<layer>', methods=['POST'])
def update_prompt(layer):
    """프롬프트 내용을 수정합니다 (저장 전 자동 백업)."""
    try:
        data = request.json
        new_content = data.get('content')
        change_reason = data.get('reason', "Manual edit via UI")
        
        if new_content is None:
            return jsonify({"error": "Content is required"}), 400
        
        file_path = PROMPTS_DIR / f"{layer}.md"
        
        # 1. 기존 파일이 있으면 백업 생성
        if file_path.exists():
            backup_manager.create_backup(layer, change_reason)
        
        # 2. 파일 저장
        file_path.write_text(new_content, encoding='utf-8')
        _audit.log("L4", "prompt_update", layer=layer, reason=change_reason, size=len(new_content))
        
        return jsonify({
            "status": "success",
            "message": f"Prompt '{layer}' updated and backed up."
        })
    except Exception as e:
        logger.error(f"Failed to update prompt '{layer}': {e}")
        _audit.log("L4", "prompt_update", layer=layer, ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500

@prompt_api_bp.route('/api/backups', methods=['GET'])
def list_backups():
    """모든 백업 목록 또는 특정 계층의 백업 목록을 가져옵니다."""
    try:
        layer = request.args.get('layer')
        limit = request.args.get('limit', type=int)
        
        backups = backup_manager.list_backups(layer_name=layer, limit=limit)
        _audit.log("L4", "backup_list", ok=True, count=len(backups))
        return jsonify(backups)
    except Exception as e:
        logger.error(f"Failed to list backups: {e}")
        _audit.log("L4", "backup_list", ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500

@prompt_api_bp.route('/api/prompts/restore', methods=['POST'])
def restore_prompt():
    """백업 파일로부터 프롬프트를 복원합니다."""
    try:
        data = request.json
        backup_filename = data.get('backup_filename')
        
        if not backup_filename:
            return jsonify({"error": "backup_filename is required"}), 400
        
        backup_manager.restore_backup(backup_filename)
        _audit.log("L4", "prompt_restore", backup_filename=backup_filename, ok=True)
        return jsonify({
            "status": "success",
            "message": f"Restored from {backup_filename}"
        })
    except Exception as e:
        logger.error(f"Failed to restore prompt: {e}")
        _audit.log("L4", "prompt_restore", backup_filename=backup_filename, ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500

@prompt_api_bp.route('/api/prompts/diff', methods=['GET'])
def get_prompt_diff():
    """현재 파일과 백업 파일의 차이점을 가져옵니다."""
    try:
        layer = request.args.get('layer')
        backup_filename = request.args.get('backup_filename')
        
        if not layer or not backup_filename:
            return jsonify({"error": "layer and backup_filename are required"}), 400
        
        diff = backup_manager.get_diff(layer, backup_filename)
        _audit.log("L4", "prompt_diff", layer=layer, backup_filename=backup_filename, ok=True, diff_len=len(diff) if isinstance(diff, str) else None)
        return jsonify({"diff": diff})
    except Exception as e:
        logger.error(f"Failed to get diff: {e}")
        _audit.log("L4", "prompt_diff", layer=layer, backup_filename=backup_filename, ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500

@prompt_api_bp.route('/api/prompts/history', methods=['GET'])
def get_history():
    """전체 변경 이력을 가져옵니다."""
    try:
        if not HISTORY_FILE.exists():
            return jsonify([])
        
        with open(HISTORY_FILE, 'r', encoding='utf-8') as f:
            history = json.load(f)
        _audit.log("L4", "prompt_history_get", ok=True, items=len(history))
        return jsonify(history)
    except Exception as e:
        logger.error(f"Failed to get history: {e}")
        _audit.log("L4", "prompt_history_get", ok=False, error=str(e))
        return jsonify({"error": str(e)}), 500
