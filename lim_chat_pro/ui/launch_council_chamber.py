"""
[LAUNCH_COUNCIL_CHAMBER.PY] - AI 전략 심의실 전용 런처
-----------------------------------------------------------
이 파일은 UI 디렉토리에서 독립된 'AI Council Chamber'로 진입하는 래퍼(Wrapper)입니다.
메인 시스템과는 별개로 동작하는 작전실을 즉시 가동합니다.
-----------------------------------------------------------
"""

import os
import sys
import subprocess
import time
import webbrowser
import socket
import psutil
from pathlib import Path
import json

def find_free_port(start_port=8080):
    """사용 가능한 빈 포트를 찾습니다."""
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def kill_existing_processes(target_path):
    """
    이전에 죽지 않고 살아있는(Ghost) 서버 프로세스를 정밀 타격하여 정리합니다.
    """
    current_pid = os.getpid()
    abs_target_path = str(Path(target_path).resolve())
    
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if not cmdline: continue
            
            full_cmd = " ".join(cmdline)
            if abs_target_path in full_cmd:
                if proc.info['pid'] != current_pid:
                    print(f"[Ghost Hunter] Killing existing server (PID: {proc.info['pid']})")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def launch():
    # 1. 경로 계산
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    chamber_dir = project_root / "packs" / "STOCK_COUNCIL"
    app_path = chamber_dir / "ui" / "app.py"
    characters_dir = chamber_dir / "data" / "variants" / "default" / "characters"

    if not app_path.exists():
        print(f"[Error] Chamber app path not found: {app_path}")

        return

    # 로컬 모델 블록 생성 옵션 처리
    argv = sys.argv[1:]
    def get_arg(flag):
        if flag in argv:
            idx = argv.index(flag)
            if idx + 1 < len(argv):
                return argv[idx + 1]
        return None
    local_block_name = get_arg("--local-block-name")
    local_model = get_arg("--model")
    local_base_url = get_arg("--base-url")
    local_api_key = get_arg("--api-key")
    local_system_prompt = get_arg("--system-prompt") or "Local model block"

    if local_block_name and local_model and local_base_url and local_api_key:
        try:
            unit_dir = characters_dir / local_block_name
            unit_dir.mkdir(parents=True, exist_ok=True)
            
            # Save persona.md (Soul)
            persona_path = unit_dir / "persona.md"
            with open(persona_path, "w", encoding="utf-8") as f:
                f.write(local_system_prompt)
                
            # Save config.json (Body)
            config_path = unit_dir / "config.json"
            with open(config_path, "w", encoding="utf-8") as f:
                json.dump(
                    {
                        "block_id": local_block_name,
                        "config": {
                            "model": local_model,
                            "api_key": local_api_key,
                            "base_url": local_base_url
                        },
                        "status": "verified"
                    },
                    f,
                    ensure_ascii=False,
                    indent=4
                )
            print(f"[Saved] Local model unit created: {unit_dir}")
        except Exception as e:
            print(f"[Error] Local model unit creation failed: {str(e)}")

    # 2. '이 프로젝트 주소의 app.py'만 정밀 타격하여 청소
    kill_existing_processes(app_path)
    port = find_free_port(8080)

    print(f"[System] AI 전략 심의실(AI Council Chamber) 가동 준비...")
    
    # 3. 백엔드 서버(FastAPI) 실행 (동적 포트 할당)
    try:
        # 로그를 확인할 수 있도록 새로운 콘솔창에서 실행
        # [Debug Fix] Use cmd /c ... & pause or just run python directly.
        # To keep window open on crash, we wrap in cmd /k
        cmd = ["cmd", "/k", sys.executable, str(app_path), "--port", str(port)]
        print(f"[System] Executing: {' '.join(cmd)}")
        
        # UTF-8 인코딩 강제 설정 (한글/이모지 깨짐 방지)
        env = os.environ.copy()
        env["PYTHONIOENCODING"] = "utf-8"

        # subprocess.Popen으로 실행하되, 필요 시 로그를 볼 수 있게 유지
        process = subprocess.Popen(
            cmd, 
            creationflags=subprocess.CREATE_NEW_CONSOLE,
            cwd=str(chamber_dir), # CWD를 packs/ai_council_chamber 로 설정해야 relative path가 맞음
            env=env
        )
        
        print(f"[System] Booting server on port {port} (Wait 3s for stability)...")
        time.sleep(3.0)
        
        # 서버가 즉시 종료되었는지 간단히 체크 (optional)
        if process.poll() is not None:
             print(f"[Critical] Server process died immediately with code {process.returncode}")
             return

        # 4. 브라우저 자동 실행
        url = f"http://127.0.0.1:{port}"
        print(f"[Success] Connection Ready: {url}")
        webbrowser.open(url)
        
    except Exception as e:
        print(f"[Critical] Launch Failed: {str(e)}")

if __name__ == "__main__":
    launch()
