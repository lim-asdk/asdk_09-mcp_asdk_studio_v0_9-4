# MCP 설정 가이드 (Korean)

모델 컨텍스트 프로토콜(MCP)은 AI가 외부 도구 및 데이터 소스와 상호 작용할 수 있도록 해줍니다.

## 1. 개념
MCP 서버는 AI에게 특정 기능(도구)을 제공하기 위해 ASDK Studio와 통신하는 별도의 프로세스입니다.

## 2. 설정 방법
MCP 서버를 추가하려면:
1. UI에서 **Settings** > **Servers** 탭을 엽니다.
2. **+ Create New Server**를 선택합니다.
3. 상세 정보를 입력합니다:
   - **Name**: 예: `sqlite_helper`
   - **Transport**: `stdio`(로컬 스크립트용) 또는 `http/sse`(원격용).
   - **Command**: `python`, `npx` 등.
   - **Arguments**: 서버 스크립트의 경로.

## 3. 번들 서버
본 스튜디오는 `servers/` 디렉토리에 기본 서버들을 포함하고 있습니다. 설정에서 해당 경로를 지정하여 즉시 사용할 수 있습니다.

---
© 2026 **lim_hwa_chan**
