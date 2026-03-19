# AI 제공자 설정 가이드 (Korean)

ASDK Studio는 OpenAI 호환 엔드포인트를 통해 다양한 AI 제공자를 지원합니다.

## 1. API 키 발급
다음 제공자 중 하나 이상에서 API 키를 발급받아야 합니다:
- **xAI (Grok)**: [https://console.x.ai/](https://console.x.ai/)
- **Google (Gemini)**: [https://aistudio.google.com/](https://aistudio.google.com/)
- **OpenAI (GPT)**: [https://platform.openai.com/](https://platform.openai.com/)
- **DeepSeek**: [https://platform.deepseek.com/](https://platform.deepseek.com/)

## 2. 스튜디오 설정
1. UI에서 **Settings** > **AI Profiles**를 엽니다.
2. 프로필(기본값: `default`)을 선택합니다.
3. **API Key**와 **Model ID**를 입력합니다.
4. **Base URL**을 설정합니다 (예: `https://api.x.ai/v1`).
5. **Test Key**를 클릭하여 유효성을 확인합니다.
6. **Save**를 클릭하여 저장합니다.

## 3. 로컬 저장 원칙
사용자의 키는 `user_data/` 폴더에 로컬로 저장되며, 당사의 서버로 전송되거나 Git에 포함되지 않습니다.

---
© 2026 **lim_hwa_chan**
