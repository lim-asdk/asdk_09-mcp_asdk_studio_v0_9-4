# MCP ASDK Studio v1 (Public Beta)

**MCP ASDK Studio is a desktop-first AI workspace and a "Practice-Ready" environment for learning AI-MCP workflows.** It lets users configure their own AI providers, connect MCP servers, inspect tools, and run chat-driven workflows through a product-style interface.

> [!NOTE]
> This version is released as a **Public Beta (Exercise/Practice Edition)**. It is ideal for users who want to practice building their own AI Studio based on the robust `Lim Chat PRO` engine.

---

[![Language: English](https://img.shields.io/badge/Language-English-blue.svg)](docs/en/PRODUCT_OVERVIEW.md)
[![Language: Korean](https://img.shields.io/badge/Language-Korean-red.svg)](docs/ko/PRODUCT_OVERVIEW.md)

## 💎 Overview
MCP ASDK Studio v1 is a general-purpose AI development and execution environment migrated from the advanced `Lim Chat PRO` engine. It provides a robust, layered architecture (L1-L5) for building vertical AI solutions and managing Model Context Protocol (MCP) integrations.

## 🚀 Key Features
- **General Studio Mode**: Standalone execution without pack dependencies.
- **MCP Integration**: Real-time Model Context Protocol server connection and tool inspection.
- **AI Persona Management**: Create and switch between custom AI profiles (Grok, Gemini, GPT, etc.).
- **Safe Data Handling**: All sensitive keys and local configs are isolated in `user_data/` (Git excluded).

## 🛠️ Quick Start
1. **Clone**: `git clone https://github.com/lim-asdk/asdk_09-mcp_asdk_studio_v0_9-4.git`
2. **Setup**: Create your profile in `user_data/profiles/default.json`.
3. **Launch**: Run `python main.py` to start the desktop studio.

## 📂 Project Structure
- `main.py`: Desktop Launcher & Entry Point.
- `lim_chat_pro/`: Core Vertical AI Engine & UI Assets.
- `user_data/`: Local private data (Profiles, History, MCP configs). **(Git Excluded)**
- `servers/`: Bundled MCP server scripts.
- `docs/`: Multi-language documentation and guides.

## 📖 Documentation
- [Product Overview (EN)](docs/en/PRODUCT_OVERVIEW.md) / [제품 개요 (KO)](docs/ko/PRODUCT_OVERVIEW.md)
- [Quick Start Guide (EN)](docs/en/QUICK_START.md) / [빠른 시작 (KO)](docs/ko/QUICK_START.md)
- [MCP Setup Guide (EN)](docs/en/MCP_SETUP.md) / [MCP 설정 (KO)](docs/ko/MCP_SETUP.md)

## 🔒 Security & Privacy
We prioritize your privacy. No API keys or personal paths are stored in the code. Users must manually manage their keys in the `user_data/` folder, which is strictly ignored by version control.

---
© 2026 **lim_hwa_chan**. All rights reserved.
