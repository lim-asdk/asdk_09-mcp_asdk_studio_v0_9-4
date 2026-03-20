"""
[MAIN.PY] - MCP ASDK Studio v1 발사대 (Launcher)
-----------------------------------------------------------
이 파일은 MCP ASDK Studio 프로그램을 시작하는 '스위치'입니다.
로켓을 발사하듯, 필요한 연료(Pack)와 엔진(Engine)을 점검하고
최종적으로 사용자 화면(UI)을 띄우는 역할을 합니다.

작성자: lim_hwa_chan (ASDK Edition Sync)
역할: 프로그램 진입점 (Entry Point)
-----------------------------------------------------------
"""

import os
import sys
import webview  # 필요 패키지: pywebview, qtpy, PyQt6-WebEngine, mcp, openai
               # Python 3.14이면 pythonnet314-whl도 추가 필요
               # 예: python -m pip install pywebview qtpy PyQt6-WebEngine mcp openai pythonnet314-whl
import logging  # 작동 기록을 남기는 라이브러리
from pathlib import Path

# 1. 경로 설정 (Path Setup)
# 프로그램이 어디에 있든 엔진(Engine)을 정확히 찾도록 도와줍니다.
def setup_paths():
    """
    현재 파일의 위치와 상관없이 프로젝트 루트를 찾아냅니다.
    (스마트 탐색: 복사/이동 시에도 작동 보장)
    """
    current_path = Path(__file__).resolve()
    
    # 1. 위로 올라가며 루트 찾기
    found_root = None
    for i in range(5):
        parent = current_path.parents[i]
        # 'lim_chat_pro' 패키지 폴더가 있는 곳을 찾음
        if (parent / "lim_chat_pro").exists():
            found_root = parent
            break
            
    if not found_root:
        found_root = Path(__file__).resolve().parent

    # 2. 경로 등록
    project_root = found_root
    package_dir = project_root / "lim_chat_pro"
    
    # 패키지 자체를 import 할 수 있게 경로 추가
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    # 엔진(두뇌) 폴더를 경로에 추가
    engine_dir = package_dir / "engine"          
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))

setup_paths()

# 경로 설정이 끝난 후에 다른 부품들을 불러옵니다.
from L3_Orchestration.pro_bridge_api import ProBridgeAPI  # Python <-> JS 연결 다리
from L1_Infrastructure.path_manager import PathManager    # 파일 위치 관리자
from lim_chat_pro import get_available_packs              # 팩 감지기

# 로그 설정 (작동 기록)
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("ASDK.Pro.Launcher")

def main():
    logger.info("Initializing MCP ASDK Studio v1.0 (V5-D-10)...")

    # ----------------------------------------------------------------
    # 단계 1: 지능 팩(IQ-Pack) 선택
    # ----------------------------------------------------------------
    packs = get_available_packs()
    active_pack = None
    
    # 팩 탐색 우선순위: 1. stock_pro  2. 첫 번째 발견된 팩  3. 없음(Emergency Assistant)
    if "stock_pro" in packs:
        active_pack = "stock_pro"
    elif packs:
        active_pack = packs[0]
    
    if active_pack:
        logger.info(f"▶ 활성화된 지능 팩: {active_pack}")
        PathManager.set_active_pack(active_pack)
        display_mode = f"Pack: {active_pack}"
    else:
        logger.info("▶ 지능 팩이 발견되지 않음. [Emergency Assistant Mode]로 시작합니다.")
        PathManager.active_pack = None 
        display_mode = "Emergency Assistant"

    # ----------------------------------------------------------------
    # 단계 2: 연결 다리(Bridge API) 설치
    # ----------------------------------------------------------------
    api = ProBridgeAPI()

    # ----------------------------------------------------------------
    # 단계 3: 화면(UI) 준비
    # ----------------------------------------------------------------
    ui_path = PathManager.get_ui_path("index_pro.html")
    
    start_url = ""
    if ui_path.exists():
        start_url = str(ui_path)
        logger.info(f"UI 파일을 로드합니다: {ui_path}")
    else:
        logger.error(f"UI 파일이 없습니다!: {ui_path}")
        start_url = "data:text/html,<h1>Error: UI File Missing</h1>"

    # ----------------------------------------------------------------
    # 단계 4: 창 띄우기 (Launch)
    # ----------------------------------------------------------------
    window = webview.create_window(
        title=f"💎 MCP ASDK Studio v1 [{display_mode}]",
        url=start_url,
        js_api=api,
        width=1280,
        height=850,
        resizable=True,
        background_color='#1a0f2e',
        x=100, y=100
    )
    
    api.set_window(window)
    
    webview.start(gui='qt', debug=False)  # Qt 백엔드 사용

if __name__ == "__main__":
    main()
