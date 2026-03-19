# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3
# Developer: LIMHWACHAN
# Version: 1.3

import json
import logging
from openai import OpenAI
from L2_Logic.data_processor import LimChatDataProcessor
from L4_Prompt.prompts import get_system_instruction, get_tool_intro
# NOTE: All modifications to prompt layers (L2, L3, L4) MUST follow /data/prompts/PRINCIPLES.md
from L3_Orchestration.tool_router import ToolRouter, RouterLock
from L1_Infrastructure.audit_logger import AuditLogger
from L2_Logic.profile_loader import ProfileLoader

# Pydantic 래퍼 선택적 import
try:
    from L2_Logic.data_processor_v2 import LimChatDataProcessorV2
    V2_AVAILABLE = True
except ImportError:
    V2_AVAILABLE = False

logger = logging.getLogger("LimChat.AIEngine")

class LimChatAIEngine:
    """
    [L3 Orchestration Layer]
    역할: 사용자 질문에 대해 AI 모델(OpenAI/DeepSeek 등)을 호출하고, 
    도구(MCP) 호출이 필요한 경우 설정된 횟수만큼 반복 수행합니다.
    이 계층은 전체 대화의 '흐름'을 지배하는 두뇌 역할을 합니다.
    
    v1.3en 신규 기능:
    - engine_config 파라미터: 반복 횟수, 컨텍스트 크기를 설정 파일로 제어
    """
    def __init__(self, api_key, model, base_url, use_schema=False, engine_config=None):
        """
        AI 엔진 초기화
        
        Args:
            api_key: OpenAI API 키
            model: 모델명 (예: gpt-4, deepseek-chat)
            base_url: API 엔드포인트
            use_schema: Pydantic 스키마 사용 여부
            engine_config: 엔진 설정 (max_iterations, context_limit 등)
        """
        self.client = OpenAI(api_key=api_key, base_url=base_url, timeout=60.0)
        self.model = model
        
        # [Configuration] 엔진 설정 로드 (하드코딩 제거)
        self.engine_config = engine_config or {
            "max_iterations": 30,
            "context_limit": 100000,
            "data_max_length": 100000
        }
        # Expose key config values as attributes for easier access
        self.max_iterations = self.engine_config['max_iterations']
        self.context_limit = self.engine_config['context_limit']
        logger.info(f"[AIEngine] Config: max_iterations={self.max_iterations}, context_limit={self.context_limit}")
        
        # 플래그로 프로세서 선택
        if use_schema and V2_AVAILABLE:
            self.processor = LimChatDataProcessorV2(use_schema=True)
            logger.info("[AIEngine] Using Pydantic schema mode")
        else:
            self.processor = LimChatDataProcessor()
            logger.info("[AIEngine] Using legacy mode")
        
        self.tool_router = ToolRouter()  # 도구 필터링 (의도 감지용)
        self.router_lock = None  # Hot-Swappable Intelligence 보안 계층 (페르소나 설정 시 초기화)
        self.profile_loader = ProfileLoader() # 페르소나 로더
        self.audit_logger = AuditLogger()  # 감사 로깅
        self._active_persona_id = None # 활성화된 페르소나 ID 저장 (Hot-Reload용)

    def process_chat(self, message, history_msgs, all_openai_tools, use_server, tool_map, clients, system_prompt_override=None):
        """
        자율 루프를 실행하여 최종 답변을 생성합니다.
        """
        tool_calls_log = []
        
        # [HOT-RELOAD] 매 요청마다 프롬프트를 새로 로드하여 .md 파일 변경사항 즉시 반영
        # [Modular Persona] active_persona 설정을 사용하여 L2, L3 오버라이드 적용
        l2_override = None
        l3_override = None
        
        # 현재 활성화된 페르소나 정보를 다시 로드하여 설정 확인 (캐싱 고려 가능하지만 Hot-Reload 위해 매번 로드)
        if self._active_persona_id:
             try:
                 profile = self.profile_loader.load_profile(self._active_persona_id)
                 l2_override = profile.get("l2_config")
                 l3_override = profile.get("l3_config")
                 # .md 확장자가 있으면 제거 (loader가 붙임)
                 if l2_override and l2_override.endswith('.md'): l2_override = l2_override[:-3]
                 if l3_override and l3_override.endswith('.md'): l3_override = l3_override[:-3]
             except:
                 pass # 페르소나 로드 실패 시 기본값 사용

        system_prompt = system_prompt_override or get_system_instruction(
            persona_id=self._active_persona_id, # [Fix] Corrected attribute name
            l2_override=l2_override,
            l3_override=l3_override
        )
        
        # 도구 목록이 비어있는 경우(모두 비활성화)에 대한 명시적 지침 추가
        if use_server and not all_openai_tools:
            tool_intro = "\n\n[SYSTEM INFO: All MCP tools are currently DISABLED by the user. Do not attempt to use any tools or suggest that you have active tools.]\n"
        else:
            tool_intro = get_tool_intro(all_openai_tools, tool_map) if use_server else ""
        
        # 히스토리 검증 및 정제 (400 에러 방지)
        validated_history = self._validate_history(history_msgs)
        
        messages = [{"role": "system", "content": system_prompt + tool_intro}]
        messages.extend(validated_history)

        
        # 현재 메시지 추가
        if not history_msgs or history_msgs[-1]["content"] != message:
            messages.append({"role": "user", "content": message})
        
        # 사용자 의도 감지 (Tool Router)
        intent = self.tool_router.detect_intent(message)
        logger.info(f"[ENGINE] Detected intent: {intent}")
        
        try:
            iteration = 0
            max_iterations = self.engine_config.get("max_iterations", 30)  # 설정 파일에서 로드
            ai_text = ""
            
            while iteration < max_iterations:
                iteration += 1
                req_args = {"model": self.model, "messages": messages, "stream": False}
                if all_openai_tools: req_args["tools"] = all_openai_tools
                
                logger.info(f"[ENGINE] AI Request (Round {iteration})...")
                comp = self.client.chat.completions.create(**req_args)
                msg = comp.choices[0].message
                ai_text = msg.content or ""
                
                # 도구 호출이 없는 경우 루프 종료
                if not msg.tool_calls or not use_server:
                    break

                messages.append(msg)
                logger.info(f"[ENGINE] Round {iteration}: Processing {len(msg.tool_calls)} tool calls")
                
                # [ROUTER LOCK] Hot-Swappable Intelligence 화이트리스트 기반 물리적 차단
                if self.router_lock:
                    filtered_tool_calls = self.router_lock.check_and_filter(msg.tool_calls)
                else:
                    # 페르소나 미설정 시 기존 ToolRouter 사용
                    filtered_tool_calls = self.tool_router.filter_tool_calls(intent, msg.tool_calls)
                
                if len(filtered_tool_calls) < len(msg.tool_calls):
                    blocked_count = len(msg.tool_calls) - len(filtered_tool_calls)
                    logger.warning(f"[ENGINE] {blocked_count} tool(s) blocked by Tool Router")
                
                # 도구 순차 처리
                # [FIX] 모든 tool_call_id에 대해 응답을 보장해야 400 에러를 방지할 수 있습니다.
                filtered_ids = {tc.id for tc in filtered_tool_calls}
                
                for tc in msg.tool_calls:
                    f_name = tc.function.name
                    tc_id = tc.id if getattr(tc, "id", None) else f"missing_id_{f_name}"
                    
                    # 1. 라우터에 의해 차단된 경우
                    if tc_id not in filtered_ids:
                        logger.warning(f"[ENGINE] Tool {f_name} blocked by Policy. Sending block response.")
                        messages.append({
                            "role": "tool", 
                            "tool_call_id": tc_id, 
                            "content": json.dumps({"error": f"Policy Block: Tool '{f_name}' is not allowed for this intent."})
                        })
                        continue

                    # 2. 허용된 도구 처리
                    f_args = self._safe_parse_args(tc.function.arguments)
                    val = tool_map.get(f_name)
                    
                    # [Namespacing Support] 'server:name' 형식 지원
                    if isinstance(val, str) and ":" in val:
                        srv_name, orig_tool_name = val.split(":", 1)
                    else:
                        srv_name = val
                        orig_tool_name = f_name

                    if srv_name and srv_name in clients:
                        try:
                            logger.info(f"[ENGINE] Action: {f_name} ({orig_tool_name}) | Args: {f_args}")
                            res_data = clients[srv_name].call_tool_sync(orig_tool_name, f_args)
                            tool_calls_log.append({"tool": f_name, "args": f_args, "result": res_data})

                            # [AUDIT LOG] 도구 호출 성공 기록
                            self.audit_logger.log_tool_call(f_name, f_args, result=res_data)

                            # [L2 Logic Layer 연동] 데이터 전처리 실행
                            content_for_ai = self.processor.process_tool_result(res_data)
                            
                            messages.append({"role": "tool", "tool_call_id": tc_id, "content": content_for_ai})
                        except Exception as e:
                            logger.error(f"[ENGINE] Tool Fail: {e}")
                            self.audit_logger.log_tool_call(f_name, f_args, error=e)
                            messages.append({"role": "tool", "tool_call_id": tc_id, "content": json.dumps({"error": str(e)})})
                    else:
                        logger.warning(f"[ENGINE] Tool {f_name} not found in any server.")
                        messages.append({"role": "tool", "tool_call_id": tc_id, "content": json.dumps({"error": "Tool not found or server disconnected"})})

                # 컨텍스트 크기 관리 (설정된 한계 초과 시 히스토리 정리)
                context_limit = self.engine_config.get("context_limit", 100000)
                total_chars = sum(len(str(m.get('content', '') if isinstance(m, dict) else m.content or "")) for m in messages)
                if total_chars > context_limit:
                    logger.info(f"[ENGINE] Context too large ({total_chars} chars, limit={context_limit}), trimming history")
                    messages = self._trim_history(messages, message)
                
                # 루프 최대치 도달 시 폴백 메시지
                if iteration == max_iterations and not ai_text:
                    ai_text = "Here are the tool execution results. Please let me know if you need further analysis."

            return {"response": ai_text, "tool_calls_log": tool_calls_log}

        except Exception as e:
            logger.error(f"[ENGINE] Error: {e}", exc_info=True)
            return {"response": f"❌ An error occurred: {str(e)}"}

    def set_persona(self, persona_name: str, allowed_tools_override: list = None) -> str:
        """
        [Hot-Swappable Intelligence]
        Sets the active persona by loading its profile, configuring RouterLock,
        and returning the system prompt.
        
        Args:
            persona_name: The name of the persona to load (e.g., "stock_analyst")
            allowed_tools_override: Dynamic whitelist from semantic binding (BridgeAPI)
            
        Returns:
            str: The system prompt content for the selected persona.
        """
        logger.info(f"[AIEngine] Switching persona to: {persona_name}")
        self._active_persona_id = persona_name
        
        try:
            # 1. Load Profile
            profile = self.profile_loader.load_profile(persona_name)
            
            # 2. Configure RouterLock (Security Layer)
            # 동적 화이트리스트 우선 사용 (Semantic Binding)
            if allowed_tools_override is not None:
                allowed_tools = allowed_tools_override
                logger.info(f"[AIEngine] Using dynamic whitelist ({len(allowed_tools)} tools)")
            else:
                # Fallback: 프로필의 allowed_tools (하위 호환성)
                allowed_tools = profile.get("allowed_tools", [])
                logger.warning(f"[AIEngine] Using static whitelist from profile")
            
            self.router_lock = RouterLock(allowed_tools)
            logger.info(f"[AIEngine] RouterLock engaged with {len(allowed_tools)} allowed tools.")
            
            # 3. Return System Prompt
            return profile.get("system_prompt", "")
            
        except Exception as e:
            logger.error(f"[AIEngine] Failed to set persona {persona_name}: {e}")
            raise

    def _safe_parse_args(self, raw_args):
        if not raw_args: return {}
        if isinstance(raw_args, dict): return raw_args
        try: return json.loads(raw_args)
        except: return {"raw": raw_args}

    def _trim_history(self, messages, current_query):
        # 시스템 프롬프트와 현재 질문은 남기고 중간 기록 삭제
        trimmed = [m for m in messages if 
                   (isinstance(m, dict) and m.get('role') in ['system', 'tool']) or 
                   (isinstance(m, dict) and m.get('role') == 'user' and m.get('content') == current_query) or 
                   not isinstance(m, dict)]
        return trimmed

    def _validate_history(self, history):
        """
        OpenAI API의 규칙을 준수하도록 히스토리를 정제합니다.
        규칙: assistant의 tool_calls 뒤에는 항상 모든 tool 응답이 따라와야 함.
        """
        if not history: return []
        
        validated = []
        pending_tool_calls = set()
        
        for msg in history:
            role = msg.get("role")
            
            if role == "assistant" and msg.get("tool_calls"):
                # 새로운 도구 호출 발생
                calls = msg.get("tool_calls")
                pending_tool_calls = {tc.get("id") for tc in calls if tc.get("id")}
                validated.append(msg)
            elif role == "tool":
                # 도구 결과 응답
                tid = msg.get("tool_call_id")
                if tid in pending_tool_calls:
                    pending_tool_calls.remove(tid)
                    validated.append(msg)
                else:
                    # 짝이 맞지 않는 tool 메시지는 버림
                    logger.warning(f"[ENGINE] Orphan tool message removed: {tid}")
                    continue
            else:
                # user나 일반 assistant 메시지인 경우
                # 만약 처리되지 않은 tool_calls가 있다면, 이 메시지 이전에 히스토리를 끊어야 함
                if pending_tool_calls:
                    logger.warning(f"[ENGINE] Break history: Unanswered tool calls found before {role}")
                    # 이 시점 이전의 assistant tool_calls 메시지도 무효화하기 위해 validated에서 제거
                    if validated and validated[-1].get("role") == "assistant" and validated[-1].get("tool_calls"):
                        validated.pop()
                    pending_tool_calls.clear()
                
                validated.append(msg)
        
        # 마지막에 아직 남은(대답 없는) tool_calls가 있다면 제거
        if pending_tool_calls:
            logger.warning(f"[ENGINE] Removing trailing unanswered tool calls")
            if validated and validated[-1].get("role") == "assistant" and validated[-1].get("tool_calls"):
                validated.pop()
                
        return validated
