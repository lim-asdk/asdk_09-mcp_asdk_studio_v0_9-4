# Quick Start Guide (English)

Follow these steps to get MCP ASDK Studio v1 up and running on your local machine.

## 1. Prerequisites
- Python 3.10 or higher.
- Git (optional, for cloning).

## 2. Installation
Clone the repository and navigate to the project root:
```bash
git clone https://github.com/lim-asdk/mcp_asdk_studio_v1.git
cd mcp_asdk_studio_v1
```

## 3. Configuration
The studio uses `user_data/` to store your private profiles.
1. **Create Profile Directory**: Ensure `user_data/profiles/` exists.
2. **Create Default Profile**: Create a file named `default.json` in that folder:
   ```json
   {
       "name": "My AI Assistant",
       "model": "grok-beta",
       "api_key": "your-key-here",
       "base_url": "https://api.x.ai/v1",
       "system_prompt": "You are a helpful studio assistant."
   }
   ```

## 4. Execution
Run the main launcher:
```bash
python main.py
```

## 5. Connecting MCP Servers
To add custom tools, use the **Settings** menu in the UI to register your MCP servers.

---
### ⚠️ Security Warning
Do **NOT** commit your `user_data` folder or any JSON files containing your real API keys. Stay safe!
