# AI Agent Directive: MCP ASDK Studio v0.9-4

This document is intended for AI agents (like yourself) who have been tasked to explore, maintain, or extend this project.

## 🤖 AI Context
- **Name**: MCP ASDK Studio
- **Version**: v0.9-4 (Public Beta)
- **Identity**: A desktop-first local AI workspace specializing in Model Context Protocol (MCP).
- **Architecture**: V5 Intelligence Matrix (L1 to L5 Layered Design).

## 📂 Repository Structure for AI Analysis

### L1: Infrastructure (`lim_chat_pro/engine/L1_Infrastructure`)
- **PathManager**: Global singleton for dynamic path resolution. Use `PathManager.get_instance()` to get directories.
- **Generalization**: All paths are relative to the project root or OS-standard data folders.

### L2: Intelligence (`lim_chat_pro/engine/L2_Intelligence`)
- Contains the core logic for processing AI responses and managing the state.

### L3: Orchestration (`lim_chat_pro/engine/L3_Orchestration`)
- **ProBridgeAPI**: The bridge between Python (Backend) and pywebview (JS Frontend).
- **Key Methods**: 
  - `send_message_to_js()`: Push data to UI.
  - `get_personas()`: List available AI personas.
  - `get_mcp_servers()`: Inspect connected MCP servers.

### L4: Prompt & Persona (`user_data/profiles`, `lim_chat_pro/engine/L4_Prompt`)
- **Profiles**: JSON files defining model (GPT-4, Claude-3), API keys, and system prompts.
- **Personas**: Specialized system instruction blocks.

### L5: Presentation (`lim_chat_pro/engine/L5_Presentation`)
- **UI Engine**: Modern HTML5/CSS3/JS running inside a `pywebview` container.
- **Main Entry**: `index_pro.html`.

## 🛠️ How to Extend this Project
1. **Adding a Persona**: Create a `.txt` file in `lim_chat_pro/engine/L4_Prompt/personas/`. No code change needed.
2. **Adding a UI Feature**: Modify `index_pro.html` and add corresponding listener in `ProBridgeAPI.py`.
3. **Environment Setup**:
   - Install: `pip install -r requirements.txt` (requires `pywebview`).
   - Run: `python main.py`.

## ⚖️ MIT License Compliance
This project is open-source. When modifying, you MUST maintain the original copyright notices as per the MIT License.

## 🎯 Mission for AI Collaborators
Maintain the "Pure Local" and "Visible Tooling" philosophy. Ensure all path handling remains Generalized and Health-checks stay accurate.
