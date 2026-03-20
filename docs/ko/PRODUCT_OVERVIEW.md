# 제품 개요 (Korean)

## 💎 MCP ASDK Studio v0.9-4란 무엇인가요?
**MCP ASDK Studio v0.9-4**은 개발자, 연구자 및 전문 AI 사용자를 위해 설계된 데스크톱 우선형 AI 워크스페이스입니다. 다양한 AI 모델 및 Model Context Protocol (MCP) 서버와 원활하게 상호 작용할 수 있는 표준화된 인터페이스를 제공합니다.

## 🚀 비전
이 스튜디오의 주요 목표는 특정 "IQ-Pack" 중심의 구조에서 벗어나, `Lim Chat PRO`에서 검증된 강력한 계층형 아키텍처를 활용하여 사용자가 직접 버티컬 AI 워크플로우를 구축할 수 있는 범용 환경을 제공하는 것입니다.

## 🏗️ 핵심 아키텍처
ASDK Studio는 **5계층 아키텍처 (L1-L5)**를 따릅니다:
- **L1 Infrastructure**: 중앙 집중식 경로 관리 및 시스템 유틸리티.
- **L2 AI & Logic**: 핵심 추론 엔진 및 데이터 처리 유닛.
- **L3 Orchestration**: 파이썬 백엔드와 JS 프론트엔드를 연결하는 브리지.
- **L4 Prompt**: 고정밀 AI 응답을 위한 구조화된 프롬프트 관리.
- **L5 Presentation**: 현대적 웹 기술 기반의 고성능 프리미엄 UI.

## 🔑 주요 개념
- **AI 프로필 (AI Profile)**: 모델 선택, API 키, 시스템 프롬프트를 포함하는 로컬 설정 파일입니다.
- **MCP 서버 (MCP Server)**: AI에게 추가 도구(주식 데이터, 뉴스, 파일 등)를 제공하는 모델 컨텍스트 프로토콜 서버입니다.
- **데스크톱 런타임 (Desktop Runtime)**: Python과 pywebview로 구축된 안전한 로컬 실행 환경입니다.

---

---

## 🌟 **지능형 실증 쇼케이스: AAPL(애플) 종합 분석**
ASDK Studio는 실제 MCP 서버와 연동하여 작동하는 분석 워크플로우를 투명하게 공개합니다. 시세, 차트, 공시, 뉴스 데이터를 결합하여 **팩트 중심(Fact-grounded)**의 입체적인 통찰을 제공합니다.

또한 각 tool 결과는 개별적으로 펼쳐 확인하고 raw JSON을 검증할 수 있어, AI 분석의 근거를 사용자가 직접 확인할 수 있습니다.

![실제 서버 연결](file:///C:/program_files/Lim%20Workspace/mcp_asdk_studio_v1/docs/assets/real-output-01-live-servers.png)
**실제 연결된 서버 및 툴 목록: 사용 가능한 기능을 UI에서 직접 확인**

![분석 결과](file:///C:/program_files/Lim%20Workspace/mcp_asdk_studio_v1/docs/assets/real-output-02-analysis-flow.png)
**다중 소스 교차 분석: 뉴스, 공시, 시세를 결합한 팩트 기반 요약 생성**

![Raw 데이터 검증](file:///C:/program_files/Lim%20Workspace/mcp_asdk_studio_v1/docs/assets/real-output-03-raw-results.png)
**데이터 투명성: 종합 의견과 함께 반환된 Raw 결과를 즉시 확인 가능**

> **"단순한 텍스트 답변이 아닌, 검증 가능한 데이터 기반의 분석 워크프페이스입니다."**

---

---

## 🔒 개인정보 보호 우선
모든 "비밀" 데이터(API 키, 대화 기록, 민감 설정)는 `user_data/` 디렉토리에 저장되며, 실수로 공개되는 것을 방지하기 위해 Git 관리 대상에서 제외됩니다.

---
© 2026 **lim_hwa_chan**
