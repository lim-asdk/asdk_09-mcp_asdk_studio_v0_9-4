import os
import sys
from pathlib import Path
import json
import subprocess as sp

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
    serverless_app = chamber_dir / "ui" / "desktop_webview.py"
    inventory_dir = chamber_dir / "data" / "variants" / "default" / "characters"

    if not serverless_app.exists():
        print("❌ serverless 실행 파일을 찾을 수 없습니다.")
        return

    args = sys.argv[1:]
    local_block_name = get_arg("--local-block-name", args)
    local_model = get_arg("--model", args)
    local_base_url = get_arg("--base-url", args)
    local_api_key = get_arg("--api-key", args)
    local_system_prompt = get_arg("--system-prompt", args) or "Local model block"

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

    exec_path = sys.executable
    si = None
    env = dict(**os.environ)
    py_path = env.get("PYTHONPATH", "")
    engine_dir = project_root / "engine"
    env["PYTHONPATH"] = os.pathsep.join([str(project_root), str(engine_dir), py_path]) if py_path else os.pathsep.join([str(project_root), str(engine_dir)])
    env["PYTHONIOENCODING"] = "utf-8"
    sp.Popen([exec_path, str(serverless_app)], env=env)

if __name__ == "__main__":
    launch()
