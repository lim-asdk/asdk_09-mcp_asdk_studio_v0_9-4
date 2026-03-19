# 빠른 시작 가이드 (Korean)

로컬 환경에서 MCP ASDK Studio v1을 시작하려면 아래 단계를 따르세요.

## 1. 사전 요구 사항
- Python 3.10 이상.
- Git (선택 사항, 클로닝용).

## 2. 설치
저장소를 복제하고 프로젝트 루트로 이동합니다:
```bash
git clone https://github.com/lim-asdk/mcp_asdk_studio_v1.git
cd mcp_asdk_studio_v1
```

## 3. 설정 (Configuration)
스튜디오는 `user_data/` 폴더를 사용하여 개인 프로필을 저장합니다.
1. **프로필 디렉토리**: `user_data/profiles/` 폴더가 있는지 확인합니다.
2. **기본 프로필 생성**: 해당 폴더에 `default.json` 파일을 만듭니다:
   ```json
   {
       "name": "나의 AI 비서",
       "model": "grok-beta",
       "api_key": "여기에-키-입력",
       "base_url": "https://api.x.ai/v1",
       "system_prompt": "당신은 유능한 스튜디오 비서입니다."
   }
   ```

## 4. 실행
메인 런처를 실행합니다:
```bash
python main.py
```

## 5. MCP 서버 연결
AI에게 추가 도구를 연결하려면 UI의 **Settings** 메뉴에서 MCP 서버를 등록하세요.

---
### ⚠️ 보안 주의사항
`user_data` 폴더나 실제 API 키가 포함된 JSON 파일을 Git에 커밋하지 마세요. 보안을 최우선으로 관리하십시오!
