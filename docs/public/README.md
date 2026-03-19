# MCP ASDK Studio v1

💎 **Advanced Intelligence Edition with Vertical AI capabilities.**

General purpose AI Council Chamber & MCP Development Studio migrated from Lim Chat Pro.

## Features
- **General Studio Mode**: No more pack dependencies. Standalone execution.
- **MCP Integration**: Seamlessly connect to Model Context Protocol servers.
- **Persona Management**: Custom AI profiles located in `user_data/profiles`.
- **Vertical AI**: Powerful reasoning engine based on L1-L5 layered architecture.

## Installation & Setup
1. **Clone the repository**:
   ```bash
   git clone https://github.com/lim-asdk/mcp_asdk_studio_v1.git
   ```
2. **Setup Environment**:
   - Create your AI profile in `user_data/profiles/your_persona.json`.
   - Add your API keys to the profile (Grok, OpenAI, etc.).
3. **Launch**:
   ```bash
   python main.py
   ```

## Folder Structure
- `apps/`: UI logic and Entry points.
- `lim_chat_pro/`: Core engine package.
- `servers/`: Bundled MCP server scripts.
- `user_data/`: Local settings (Git excluded).
- `docs/`: Guides and technical documentation.

## Security
- All sensitive keys are stored in `user_data/` which is excluded from Git.
- Never commit your `*.local.json` or `.env` files.

---
Developed by **lim_hwa_chan**
