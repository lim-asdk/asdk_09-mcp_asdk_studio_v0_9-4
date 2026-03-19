"""
[PACK EDITOR] - IQ-Pack 통합 관리 도구
-----------------------------------------------------------
이 파일은 Lim Chat Pro의 모든 설정을 관리하는 '종합 상황실'입니다.
프롬프트(뇌), 프로필(명찰), MCP(도구)를 모두 수정할 수 있습니다.

[특징]
1. 단일 파일 실행 (Standalone): 별도 설치 없이 이 파일만 있으면 됩니다.
2. 3단 탭 구조: 지식, 설정, 도구를 탭으로 구분하여 관리합니다.
3. 안전 백업: 저장할 때마다 날짜별로 백업하여 실수를 방지합니다.

작성자: lim_hwa_chan
버전: 2.0 (Multi-Tab Support + Detailed Comments)
-----------------------------------------------------------
"""
import os
import sys
import json
import shutil
import webview
from datetime import datetime
from pathlib import Path

# =========================================================
# 1. 경로 설정 (Path Setup)
# =========================================================
# 프로그램이 어디에 있든 엔진(Engine)을 정확히 찾도록 도와줍니다.
def setup_paths():
    """
    현재 파일의 위치와 상관없이 프로젝트 루트(lim_chat_pro_v1_0)를 찾아냅니다.
    위로 거슬러 올라가며 'setup.py'가 있는 곳을 찾습니다.
    (스마트 탐색: 복사/이동 시에도 작동 보장)
    """
    current_path = Path(__file__).resolve()
    
    # 1. 위로 올라가며 루트 찾기 (최대 5단계)
    found_root = None
    for i in range(5):
        parent = current_path.parents[i]
        # 'lim_chat_pro' 패키지 폴더나 'setup.py'가 있는 곳을 찾음
        if (parent / "setup.py").exists() or (parent / "lim_chat_pro").exists():
            found_root = parent
            if (parent / "setup.py").exists():
                break # setup.py가 있는 곳이 가장 확실한 루트
            
    if not found_root:
        # 못 찾으면 기본 상대 경로 시도
        found_root = Path(__file__).resolve().parent.parent.parent

    # 2. 경로 등록
    project_root = found_root
    package_dir = project_root / "lim_chat_pro"
    engine_dir = package_dir / "engine"

    if str(project_root) not in sys.path:
        sys.path.insert(0, str(project_root))
        
    if str(engine_dir) not in sys.path:
        sys.path.insert(0, str(engine_dir))
        
    print(f"[Editor] Project Root Found: {project_root}")

setup_paths()

# 엔진에서 필요한 도구들을 가져옵니다.
from L1_Infrastructure.path_manager import PathManager  # 길 안내 도구
from lim_chat_pro import get_available_packs            # 팩 탐지 도구

# =========================================================
# 2. 내장형 UI (HTML/CSS/JS)
# =========================================================
# 별도의 HTML 파일 없이, 이 문자열 자체가 화면이 됩니다.
HTML_TEMPLATE = """
<!DOCTYPE html>
<html lang="ko">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Lim Chat Pro - Pack Editor</title>
    <style>
        /* 
         * [디자인 테마] 
         * 눈이 편안한 다크 모드(Dark Mode)를 기본으로 합니다.
         */
        :root {
            --bg-color: #1a0f2e;       /* 전체 배경색 (진한 보라색) */
            --sidebar-color: #110a1f;  /* 왼쪽 메뉴 배경색 */
            --text-color: #e0e0e0;     /* 기본 글자색 (회색) */
            --accent-color: #00ff88;   /* 강조색 (형광 초록) */
            --accent-hover: #00cc6a;   /* 버튼 위에 올렸을 때 색 */
            --border-color: #333;      /* 테두리 색 */
            --tab-active: #2d2d2d;     /* 탭 선택되었을 때 배경 */
        }
        body {
            font-family: 'Segoe UI', sans-serif;
            background-color: var(--bg-color);
            color: var(--text-color);
            margin: 0;
            display: flex;
            height: 100vh; /* 화면 전체 높이 사용 */
            overflow: hidden;
        }
        
        /* 왼쪽 사이드바 (메뉴 영역) */
        #sidebar {
            width: 250px;
            background-color: var(--sidebar-color);
            border-right: 1px solid var(--border-color);
            padding: 20px;
            display: flex;
            flex-direction: column;
        }
        
        /* 오른쪽 에디터 영역 (작업 공간) */
        #editor-area {
            flex: 1; /* 남은 공간 모두 차지 */
            display: flex;
            flex-direction: column;
            padding: 20px;
        }
        
        h2 { margin-top: 0; font-size: 1.2rem; color: var(--accent-color); }
        
        /* 팩 선택 박스 스타일 */
        select {
            width: 100%;
            padding: 10px;
            margin-bottom: 20px;
            background: #2d2d2d;
            border: 1px solid var(--border-color);
            color: white; 
            border-radius: 4px;
            cursor: pointer;
        }

        /* 탭(Tab) 버튼 스타일 */
        .tab-container {
            display: flex;
            margin-bottom: 10px;
            border-bottom: 1px solid var(--border-color);
        }
        .tab {
            padding: 10px 15px;
            cursor: pointer;
            color: gray;
            border-bottom: 2px solid transparent; /* 평소엔 밑줄 없음 */
            transition: all 0.2s;
        }
        .tab:hover { color: white; background-color: #1e1e1e; }
        .tab.active {
            color: var(--accent-color);
            border-bottom: 2px solid var(--accent-color); /* 선택되면 형광 밑줄 */
            font-weight: bold;
        }

        /* 파일 목록 리스트 스타일 */
        ul { list-style: none; padding: 0; overflow-y: auto; flex: 1; margin-top: 10px; }
        li {
            padding: 8px 10px;
            cursor: pointer;
            border-bottom: 1px solid #222;
            font-size: 0.95rem;
        }
        li:hover { background-color: #2d2d2d; }
        li.active { background-color: #2d2d2d; border-left: 3px solid var(--accent-color); }
        
        /* 텍스트 편집기 스타일 */
        #editor {
            flex: 1;
            background-color: #1e1e1e;
            color: #d4d4d4;
            border: 1px solid var(--border-color);
            padding: 15px;
            font-family: 'Consolas', monospace; /* 코딩용 폰트 */
            font-size: 14px;
            line-height: 1.5;
            resize: none;
            outline: none;
            border-radius: 4px;
        }
        
        /* 저장 버튼 스타일 */
        button {
            background-color: var(--accent-color);
            color: #000;
            font-weight: bold;
            border: none;
            padding: 8px 16px;
            border-radius: 4px;
            cursor: pointer;
        }
        button:hover { background-color: var(--accent-hover); }

        /* 하단 상태바 */
        #status-bar {
            margin-top: 10px;
            font-size: 0.9rem;
            color: #888;
            display: flex;
            justify-content: space-between;
        }
    </style>
</head>
<body>
    <!-- 왼쪽 사이드바 -->
    <div id="sidebar">
        <h2>📦 Pack 선택</h2>
        <select id="pack-select" onchange="changePack()">
            <option value="" disabled selected>팩 로딩중...</option>
        </select>
        
        <!-- 3단 탭 버튼 -->
        <div class="tab-container">
            <div class="tab active" onclick="changeTab('prompts')">🧠 뇌 (Prompts)</div>
        </div>
        <div class="tab-container">
            <div class="tab" onclick="changeTab('profiles')">🏷️ 명찰 (AI Setup)</div>
        </div>
        <div class="tab-container">
            <div class="tab" onclick="changeTab('servers')">🔌 도구 (MCP)</div>
        </div>

        <ul id="file-list">
            <!-- 자바스크립트가 여기에 파일 목록을 채워넣습니다 -->
        </ul>
    </div>
    
    <!-- 오른쪽 편집 영역 -->
    <div id="editor-area">
        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 10px;">
            <h2 id="current-file" style="margin:0;">파일을 선택하세요</h2>
            <button onclick="saveFile()">💾 저장 & 백업</button>
        </div>
        <textarea id="editor" disabled></textarea> <!-- 내용을 보여주는 곳 -->
        <div id="status-bar">
            <span id="status-msg">준비됨</span>
            <span id="file-info"></span>
        </div>
    </div>

    <!-- 화면 동작 스크립트 (JavaScript) -->
    <script>
        let currentTab = 'prompts'; // 기본 탭: 뇌(Prompts)
        let currentFile = null;     // 현재 선택된 파일

        // [초기화] 프로그램이 켜지면 제일 먼저 실행됩니다.
        async function init() {
            // 파이썬에게 "설치된 팩 좀 알려줘" 라고 요청합니다.
            const packs = await pywebview.api.get_packs();
            const select = document.getElementById('pack-select');
            select.innerHTML = ''; // 목록 청소
            
            // 받아온 팩 목록을 화면에 추가합니다.
            packs.forEach(pack => {
                const option = document.createElement('option');
                option.value = pack;
                option.textContent = pack;
                select.appendChild(option);
            });
            
            // 팩이 하나라도 있으면, 첫 번째 팩을 자동으로 엽니다.
            if (packs.length > 0) {
                select.value = packs[0];
                changePack();
            }
        }

        // [팩 변경] 사용자가 콤보박스에서 팩을 바꿨을 때
        async function changePack() {
            const pack = document.getElementById('pack-select').value;
            // 파이썬에게 "이제부터 이 팩을 쓸 거야" 라고 알립니다.
            await pywebview.api.set_pack(pack);
            loadFileList(); // 파일 목록을 새로고침합니다.
        }

        // [탭 변경] 뇌 / 명찰 / 도구 탭을 클릭했을 때
        function changeTab(tabName) {
            currentTab = tabName;
            
            // 화면에서 어떤 탭이 눌렸는지 표시를 바꿉니다 (형광 밑줄).
            document.querySelectorAll('.tab').forEach(el => {
                el.classList.remove('active');
                if (el.textContent.includes(getTabLabel(tabName))) el.classList.add('active');
            });
            
            // 파일 목록을 잠깐 지우고 로딩 중임을 알립니다.
            document.getElementById('file-list').innerHTML = '<li style="color:#666">로드 중...</li>';
            
            loadFileList(); // 바뀐 탭의 파일들을 불러옵니다.
        }
        
        // 탭(영어) -> 한글 이름 변환기
        function getTabLabel(tab) {
            if (tab === 'prompts') return '뇌';
            if (tab === 'profiles') return '명찰';
            if (tab === 'servers') return '도구';
            return '';
        }

        // [목록 불러오기] 현재 팩, 현재 탭의 파일들을 가져옵니다.
        async function loadFileList() {
            const files = await pywebview.api.list_files(currentTab);
            const list = document.getElementById('file-list');
            list.innerHTML = '';
            
            if (files.length === 0) {
                list.innerHTML = '<li style="color:#666; cursor:default">파일 없음</li>';
                return;
            }

            files.forEach(file => {
                const li = document.createElement('li');
                li.textContent = file;
                // 파일을 클릭하면 loadFile 함수가 실행되게 합니다.
                li.onclick = () => loadFile(file, li);
                list.appendChild(li);
            });
        }

        // [파일 열기] 목록에서 파일을 클릭했을 때
        async function loadFile(filename, element) {
            // 선택된 항목 강조 표시
            document.querySelectorAll('li').forEach(el => el.classList.remove('active'));
            if (element) element.classList.add('active');
            
            currrentFile = filename; // 오타 수정: currrentFile -> currentFile
            currentFile = filename;
            
            // 제목과 내용창 활성화
            document.getElementById('current-file').textContent = `[${currentTab}] ${filename}`;
            document.getElementById('editor').disabled = false;
            
            // 파이썬에게 "내용 줘" 요청
            const content = await pywebview.api.read_file(currentTab, filename);
            document.getElementById('editor').value = content;
            document.getElementById('status-msg').textContent = "로드됨";
            document.getElementById('file-info').textContent = `${currentTab}/${filename}`;
        }

        // [저장 하기] 저장 버튼 눌렀을 때
        async function saveFile() {
            if (!currentFile) return;
            
            const content = document.getElementById('editor').value;
            document.getElementById('status-msg').textContent = "저장 중...";
            
            // 파이썬에게 "저장해줘(백업도 부탁해)" 요청
            const result = await pywebview.api.save_file(currentTab, currentFile, content);
            
            if (result.success) {
                document.getElementById('status-msg').textContent = "✅ 저장 및 백업 완료";
                setTimeout(() => document.getElementById('status-msg').textContent = "준비됨", 2000);
            } else {
                alert("오류: " + result.error);
                document.getElementById('status-msg').textContent = "저장 실패";
            }
        }

        // 준비가 되면 init 함수 실행!
        window.addEventListener('pywebviewready', init);
    </script>
</body>
</html>
"""

# =========================================================
# 3. Python API (Engine)
# =========================================================
# HTML 화면(JavaScript)과 대화하는 실제 '일꾼'입니다.
class EditorAPI:
    def __init__(self):
        self.active_pack = None

    def get_packs(self):
        """설치된 팩(Pack)들이 뭐가 있는지 반환합니다."""
        return get_available_packs()

    def set_pack(self, pack_name):
        """편집하려는 팩을 선택하고, PathManager에게 알립니다."""
        self.active_pack = pack_name
        # 이걸 해줘야 PathManager가 'stock_pro' 폴더를 가리키게 됩니다.
        PathManager.set_active_pack(pack_name)
        print(f"[Editor] 팩 전환: {pack_name}")

    def _get_dir(self, category):
        """탭(Category)에 따라 저장될 진짜 폴더 위치를 알려줍니다."""
        if category == 'prompts':
            return PathManager.get_prompt_dir()  # packs/stock_pro/prompts
        elif category == 'profiles':
            return PathManager.get_profile_dir() # packs/stock_pro/profiles
        elif category == 'servers':
            return PathManager.get_server_dir()  # packs/stock_pro/servers
        return None

    def list_files(self, category):
        """해당 탭(카테고리)에 있는 파일 목록을 보여줍니다."""
        if not self.active_pack: return []
        
        target_dir = self._get_dir(category)
        if not target_dir or not target_dir.exists(): return []
        
        # 프롬프트는 .md 파일만, 나머지는 .json 파일만 보여줍니다.
        ext = "*.md" if category == "prompts" else "*.json"
        return [f.name for f in target_dir.glob(ext)]

    def read_file(self, category, filename):
        """파일 내용을 읽어서 화면에 보내줍니다."""
        target_dir = self._get_dir(category)
        file_path = target_dir / filename
        if file_path.exists():
            return file_path.read_text(encoding='utf-8')
        return ""

    def save_file(self, category, filename, content):
        """파일을 저장합니다. (가장 중요한 부분!)"""
        try:
            target_dir = self._get_dir(category)
            file_path = target_dir / filename
            
            # 1. 안전 백업 (Safety Backup) -------------------
            # 실수로 내용을 지워도 복구할 수 있게 먼저 복사해둡니다.
            if file_path.exists():
                # 저장 위치: user_data/backups/팩이름/카테고리/
                backup_root = PathManager.USER_DATA_ROOT / "backups" / self.active_pack / category
                backup_root.mkdir(parents=True, exist_ok=True)
                
                # 파일명 뒤에 날짜_시간을 붙여서 절대 겹치지 않게 합니다.
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                backup_path = backup_root / f"{filename}_{timestamp}.bak"
                
                shutil.copy2(file_path, backup_path)
                print(f"[Editor] 백업: {backup_path}")
            # ---------------------------------------------

            # 2. 진짜 저장 (Overwrite)
            file_path.write_text(content, encoding='utf-8')
            return {"success": True}
        except Exception as e:
            return {"success": False, "error": str(e)}

# =========================================================
# 4. 실행 (Launch)
# =========================================================
def main():
    api = EditorAPI()
    
    # 창(Window)을 만듭니다.
    window = webview.create_window(
        title="Lim Chat Pro - Pack Editor Suite",
        html=HTML_TEMPLATE,
        js_api=api,
        width=1100,
        height=800,
        resizable=True,
        background_color='#1a0f2e' # 어두운 보라색 배경
    )
    # 프로그램을 시작합니다.
    webview.start()

if __name__ == "__main__":
    main()
