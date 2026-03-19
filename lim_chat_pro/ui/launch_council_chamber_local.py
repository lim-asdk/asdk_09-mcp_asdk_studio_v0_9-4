import os
import sys
import subprocess
import time
import socket
import psutil
from pathlib import Path
import json
import webview
import subprocess as sp
import urllib.request
import urllib.error

def find_free_port(start_port=8080):
    port = start_port
    while port < start_port + 100:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(('127.0.0.1', port)) != 0:
                return port
        port += 1
    return start_port

def kill_existing_processes(target_path):
    current_pid = os.getpid()
    abs_target_path = str(Path(target_path).resolve())
    for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
        try:
            cmdline = proc.info.get('cmdline')
            if not cmdline:
                continue
            full_cmd = " ".join(cmdline)
            if abs_target_path in full_cmd:
                if proc.info['pid'] != current_pid:
                    print(f"👻 기존 서버 발견(PID: {proc.info['pid']}), 종료합니다.")
                    proc.kill()
        except (psutil.NoSuchProcess, psutil.AccessDenied):
            continue

def get_arg(flag, args):
    if flag in args:
        idx = args.index(flag)
        if idx + 1 < len(args):
            return args[idx + 1]
    return None

def launch():
    current_dir = Path(__file__).parent
    project_root = current_dir.parent
    chamber_dir = project_root / "packs" / "STOCK_COUNCIL"
    app_path = chamber_dir / "ui" / "app.py"
    inventory_dir = chamber_dir / "data" / "variants" / "default" / "characters"

    if not app_path.exists():
        print(f"[Error] Path not found: {app_path}")
        return

    args = sys.argv[1:]
    local_block_name = get_arg("--local-block-name", args)
    local_model = get_arg("--model", args)
    local_base_url = get_arg("--base-url", args)
    local_api_key = get_arg("--api-key", args)
    local_system_prompt = get_arg("--system-prompt", args) or "Local model block"
    no_server = ("--no-server" in args)
    no_ui = ("--no-ui" in args)
    serverless = True

    if local_block_name and local_model and local_base_url and local_api_key:
        try:
            unit_dir = inventory_dir / local_block_name
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

    if no_server:
        print("🛑 서버 기동을 생략합니다 (--no-server). 인벤토리만 업데이트했습니다.")
        return
    if serverless:
        serverless_app = chamber_dir / "ui" / "desktop_webview.py"
        if not serverless_app.exists():
            print("[Error] serverless execution file not found.")
            return
        print("[System] Running in serverless mode.")
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        exec_path = str(pythonw) if pythonw.exists() else sys.executable
        si = sp.STARTUPINFO()
        si.dwFlags |= sp.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        env = os.environ.copy()
        py_path = env.get("PYTHONPATH", "")
        engine_dir = project_root / "engine"
        env["PYTHONPATH"] = os.pathsep.join([str(project_root), str(engine_dir), py_path]) if py_path else os.pathsep.join([str(project_root), str(engine_dir)])
        sp.Popen([exec_path, str(serverless_app)], startupinfo=si, creationflags=sp.CREATE_NO_WINDOW, env=env)
        return
    kill_existing_processes(app_path)
    port = find_free_port(8080)
    print(f"🛡️ AI 전략 심의실 로컬 버전 가동 준비...")
    try:
        pythonw = Path(sys.executable).with_name("pythonw.exe")
        exec_path = str(pythonw) if pythonw.exists() else sys.executable
        si = sp.STARTUPINFO()
        si.dwFlags |= sp.STARTF_USESHOWWINDOW
        si.wShowWindow = 0
        cmd = [exec_path, str(app_path), "--port", str(port)]
        sp.Popen(cmd, startupinfo=si, creationflags=sp.CREATE_NO_WINDOW)
        print(f"⏳ 포트 {port} 부팅 중...")
        def wait_for_http(url, timeout=30.0, interval=0.5):
            deadline = time.time() + timeout
            last_err = None
            while time.time() < deadline:
                try:
                    with urllib.request.urlopen(url, timeout=2) as resp:
                        if resp.status == 200:
                            return True
                except Exception as e:
                    last_err = e
                time.sleep(interval)
            if last_err:
                print(f"⚠️ 서버 응답 대기 시간 초과: {str(last_err)}")
            return False
        url = f"http://127.0.0.1:{port}"
        ok = wait_for_http(url, timeout=35.0, interval=0.7)
        if not ok:
            print("❌ 서버가 예상 시간 내에 준비되지 않았습니다. 창을 열면 연결 오류가 보일 수 있습니다.")
        print(f"🔗 작전실 준비 완료: {url}")
        print("브라우저는 자동으로 열지 않습니다.")
        if not no_ui:
            window = webview.create_window(
                title="AI Council Chamber (Local)",
                url=url,
                width=1280,
                height=850,
                resizable=True,
            )
            webview.start(debug=False)
    except Exception as e:
        print(f"❌ 가동 실패: {str(e)}")

if __name__ == "__main__":
    launch()
