# -*- coding: utf-8 -*-
# Project: lim_chat_v1_3en
# Developer: LIMHWACHAN
# Version: 1.3

"""
[L4 Prompt Layer]
역할: AI의 페르소나와 작업 지침을 정의합니다. 
이제 외부 .md 파일에서 동적으로 로드하여 코드 수정 없이 프롬프트를 변경할 수 있습니다.
"""

from .prompt_loader import PromptLoader

# Initialize the prompt loader (singleton pattern)
_loader = PromptLoader()


def get_system_instruction(persona_id=None, l2_override=None, l3_override=None):
    """
    Get the complete system instruction by combining all layer prompts.
    
    This function loads prompts from external .md files every time it's called,
    enabling hot-reload functionality (edit .md files without restarting the app).
    
    Args:
        persona_id: Optional persona ID for the L4 layer.
        l2_override: Optional filename for L2 layer.
        l3_override: Optional filename for L3 layer.
        
    Returns:
        Combined system instruction string.
    """
    prompts = _loader.load_all(persona_id=persona_id, l2_file=l2_override, l3_file=l3_override)
    
    # Combine in order: L4 (identity) -> L3 (reasoning) -> L2 (data processing)
    combined = prompts['L4']
    
    if prompts['L3']:
        combined += "\n\n" + prompts['L3']
    
    if prompts['L2']:
        combined += "\n\n" + prompts['L2']
    
    return combined


def get_tool_intro(tools, tool_map=None):
    """
    MCP 도구 목록을 프롬프트에 포함하기 위한 텍스트를 생성합니다.
    
    Args:
        tools: List of tool definitions from MCP server
        tool_map: Dict mapping tool names to server names (optional)
    
    Returns:
        Formatted tool introduction string
    """
    if not tools:
        return ""
    
    intro = "\n\n[SYSTEM INFO: Connected MCP (Model Context Protocol) Environment]\n"
    intro += "You are connected to the following MCP Servers and Tools. "
    intro += "If the user asks about 'MCP', 'Servers', 'Tools', or 'Capabilities', provide a summary based on this list.\n"
    
    # 툴을 서버별로 그룹화
    server_tools = {}
    if tool_map:
        for t in tools:
            t_name = t['function']['name']
            s_name = tool_map.get(t_name, "Unknown Server")
            if s_name not in server_tools: server_tools[s_name] = []
            server_tools[s_name].append(t)
    else:
        server_tools["Default"] = tools

    for s_name, t_list in server_tools.items():
        intro += f"\n### Server: {s_name}\n"
        for t in t_list:
            intro += f"- {t['function']['name']}: {t['function']['description']}\n"
    
    intro += "\n[INSTRUCTION]\n"
    intro += "1. Always prioritize these tools for stock queries.\n"
    intro += "2. If asked 'What tools do you have?' or 'What is MCP?', output the server/tool structure above naturally.\n"
    intro += "3. Do not just say 'I have tools'. specific capability (e.g., 'I can fetch SEC filings via finance_helper server')."
    return intro


# Legacy compatibility: Keep STOCK_SYSTEM_INSTRUCTION for backward compatibility
# This will be deprecated in future versions
STOCK_SYSTEM_INSTRUCTION = get_system_instruction()
