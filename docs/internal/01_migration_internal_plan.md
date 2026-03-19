# [INTERNAL] MCP ASDK Studio v1 마이그레이션 상세 계획

이 문서는 `Lim Chat Pro`에서 `MCP ASDK Studio`로의 마이그레이션을 위한 내부 기술 지침서입니다.

## 1. 개요
기존의 복잡한 'Intelligence Pack' 구조를 완전히 제거하고, 단일 스튜디오 환경으로 엔진을 통합합니다. 원본의 UI 디자인과 런처 로직을 최대한 유지하여 사용자가 기존과 동일한 프리미엄 경험을 갖도록 합니다.

## 2. 마이그레이션 핵심 원칙
- **팩(Pack) 제거**: `lim_chat_pro/packs` 폴더를 삭제하고, 모든 기능을 공용 `engine`과 `ui`로 통합.
- **원본 구조 유지**: `main.py` 진입점과 `lim_chat_pro` 패키지 구조를 유지하여 코드 가독성과 하위 호환성 확보.
- **상대 경로 안정화**: 13번 보고서의 원칙에 따라 `sys.executable` 및 `REPO_ROOT` 기반 동적 경로 처리.
- **보안 격리**: API Key 및 개인 프로파일은 `user_data/profiles`에서만 관리하며 Git 추적에서 제외.

## 3. 단계별 실행 계획

### 단계 1: 프로젝트 기초 구축 (현재 진행 중)
- 대상 디렉토리 생성 및 Git 초기화.
- `.gitignore` 설정을 통해 `user_data/`, `.env`, `__pycache__` 등을 원천 차단.

### 단계 2: 핵심 엔진 및 UI 이식
- `lim_chat_pro/ui` 및 `lim_chat_pro/engine` 내의 L1, L2, L3 레이어 복사.
- `IQ-Pack` 감지 로직을 삭제하고, 공용 MCP 서버 호출 방식으로 `ProBridgeAPI` 수정.

### 단계 3: 설정 및 런처 마이그레이션
- `main.py`의 `setup_paths()`를 신규 구조에 맞게 최적화.
- `user_data/profiles/default.json` 가이드 작성 (Grok 등 로컬 키 전용).

### 단계 4: 검증 및 공개 준비
- 내부용(`docs/internal`)과 외부용(`docs/public`) 문서를 최종 분리.
- GitHub에 첫 커밋 시 보안 스캔을 수행하여 민감 정보 포함 여부 재확인.

## 4. 특이 사항
- **Grok 연결**: 공개 배포용에는 키를 포함하지 않으며, 사용자가 `user_data`에 직접 입력하도록 유도.
- **서버 번들링**: 필수적인 기본 MCP 서버는 `servers/` 폴더에 포함하여 배포.
