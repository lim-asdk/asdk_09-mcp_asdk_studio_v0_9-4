"""
[MAIN.PY] - MCP ASDK Studio v1 발사대 (Launcher)
-----------------------------------------------------------
이 파일은 MCP ASDK Studio 프로그램을 시작하는 진입점입니다.
기존 Lim Chat Pro의 UI 성능을 유지하면서, 범용적인 스튜디오 환경을 제공합니다.

역할: 프로그램 진입점 (Entry Point)
-----------------------------------------------------------
"""

import os
import sys
import webview
import logging
from pathlib import Path

# 1. 경로 설정 (Path Setup)
def setup_paths():
    """
    현재 프로젝트 루트(mcp_asdk_studio_v1)를 기반으로 패키지 및 엔진 경로를 등록합니다.
    """
    project_root = Path(__file__).resolve().parent
    package_dir = project_root / "lim_chat_pro"
    engine_dir = package_dir / "engine"
    
    # 프로젝트 루트 등록
    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    # 엔진(두뇌) 폴더 등록
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))
        print(f"[Launcher] ASDK Studio 엔진 경로 등록 완료: {engine_dir}")

setup_paths()

# 엔진 로드 후 부품 불러오기
from L3_Orchestration.pro_bridge_api import ProBridgeAPI  # Python <-> JS 연결 다리
from L1_Infrastructure.path_manager import PathManager    # 파일 위치 관리자

# 로그 설정
logging.basicConfig(level=logging.INFO, format='%(asctime)s [%(levelname)s] %(name)s: %(message)s')
logger = logging.getLogger("ASDK.Studio.Launcher")

def main():
    logger.info("Initializing MCP ASDK Studio v1.0...")

    display_mode = "Studio Mode"

    # ----------------------------------------------------------------
    # 단계 1: 연결 다리(Bridge API) 설치
    # ----------------------------------------------------------------
    api = ProBridgeAPI()

    # ----------------------------------------------------------------
    # 단계 2: 화면(UI) 준비
    # ----------------------------------------------------------------
    # 공용 UI 파일인 index_pro.html을 로드합니다.
    ui_path = PathManager.get_ui_path("index_pro.html")
    
    start_url = ""
    if ui_path.exists():
        start_url = str(ui_path)
        logger.info(f"UI 파일을 로드합니다: {ui_path}")
    else:
        logger.error(f"UI 파일이 없습니다!: {ui_path}")
        # L5_Presentation 내의 다른 HTML 시도
        fallback_ui = PathManager.L5_UI_DIR / "index.html"
        if fallback_ui.exists():
             start_url = str(fallback_ui)
        else:
             start_url = "data:text/html,<h1>Error: UI File Missing</h1>"

    # ----------------------------------------------------------------
    # 단계 3: 창 띄우기 (Launch)
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
    
    # 메인 루프 실행
    webview.start(debug=False)

if __name__ == "__main__":
    main()
