# MCP Setup Guide (English)

Model Context Protocol (MCP) allows your AI to interact with external tools and data sources.

## 1. Concept
MCP servers are separate processes that communicate with ASDK Studio to expose functions (tools).

## 2. Configuration
To add an MCP server:
1. Open **Settings** > **Servers** in the UI.
2. Select **+ Create New Server**.
3. Fill in the details:
   - **Name**: e.g., `sqlite_helper`
   - **Transport**: `stdio` (for local scripts) or `http/sse` (for remote).
   - **Command**: `python`, `npx`, etc.
   - **Arguments**: Path to your server script.

## 3. Bundled Servers
This studio includes default servers in the `servers/` directory. You can use them by pointing to their absolute paths in the settings.

---
© 2026 **lim_hwa_chan**
