# Customization Guide: Personas & Profiles

This guide explains how to customize the AI's behavior and environment in MCP ASDK Studio v0.9-4.

## 🎭 1. AI Personas (System Prompts)
Personas define "who" the AI is. They are raw text files containing system instructions.

- **Storage Path**: `lim_chat_pro/engine/L4_Prompt/personas/`
- **File Format**: `.txt`
- **How to Add**:
  1. Create a new `.txt` file (e.g., `expert_coder.txt`).
  2. Write the system prompt inside the file.
  3. Restart the App or Refresh. The new persona will appear in the dropdown menu.

## 📂 2. AI Profiles (Model & API Settings)
Profiles define the "engine" and "identity" for a session, including model choice and API keys.

- **Storage Path**: `user_data/profiles/`
- **File Format**: `.json`
- **Default File**: `default.json`
- **JSON Structure**:
  ```json
  {
    "profile_name": "Standard GPT-4",
    "model": "gpt-4-turbo",
    "api_key": "your-key-here",
    "api_base": "https://api.openai.com/v1",
    "temperature": 0.7,
    "default_persona": "default_assistant"
  }
  ```
- **How to Add**:
  1. Copy `default.json` and rename it (e.g., `claude_pro.json`).
  2. Modify the `model` and `api_key`.
  3. The profile will be selectable in the App's Profile dropdown.

## 🛠️ 3. Quick Tips for Builders
- **Persona Best Practices**: Start your `.txt` with "You are a [Role]..." to ensure clear context.
- **Profile Security**: Never commit your `user_data/profiles/` folder to public repositories. Use `.gitignore` (which is already set up in this project).
- **Auto-Loading**: The Studio always looks for `default.json` first as the baseline configuration.

---
© 2026 **lim_hwa_chan** | V5 Intelligence Matrix Customization Standard
