# V5 Intelligence Matrix: Architectural Proof (L1-L5)

This document provides technical evidence of the **V5 Architecture**, ensuring the project meets professional-grade standards for "Visible Tooling" and "Modular Intelligence."

## 🏛️ Layered Design Philosophy
The ASDK Studio is built on a strictly decoupled 5-layer system to prevent circular dependencies and ensure scalability.

### L1: Infrastructure (Foundation)
- **Responsibility**: Environment stability, path management, and logging.
- **Evidence**: `lim_chat_pro/engine/L1_Infrastructure/path_manager.py`.
- **Key Feature**: Instance-based `PathManager` with `.env` support and auto-directory creation.

### L2: Intelligence (Cognition)
- **Responsibility**: AI logic, state transition, and core data processing.
- **Evidence**: `lim_chat_pro/engine/L2_Intelligence/`.
- **Key Feature**: Isolation of AI response logic from UI components.

### L3: Orchestration (Bridge)
- **Responsibility**: Bidirectional communication between Python and the Web-based Frontend.
- **Evidence**: `lim_chat_pro/engine/L3_Orchestration/pro_bridge_api.py`.
- **Key Feature**: Reusable API methods for MCP server inspection and persona hot-swapping.

### L4: Prompt (Context)
- **Responsibility**: Persona management and prompt engineering.
- **Evidence**: `lim_chat_pro/engine/L4_Prompt/personas/`.
- **Key Feature**: Plain-text persona blocks for easy user modification without code changes.

### L5: Presentation (Experience)
- **Responsibility**: Premium, high-performance UI.
- **Evidence**: `lim_chat_pro/engine/L5_Presentation/index_pro.html`.
- **Key Feature**: Clean HTML5/CSS3 implementation optimized for desktop pywebview.

## 🛠️ Verification Checklist for Builders
1. **Modularity**: Can I replace L5 with a different UI? → **Yes**.
2. **Path Generalization**: Does it work if I move the folder? → **Yes**, via PathManager.
3. **Security**: Are keys safe? → **Yes**, isolation via `.env` and `user_data/`.

---
© 2026 **lim_hwa_chan** | V5 Intelligence Matrix Standard
