# Smart Terminal Assistant 🤖💻

An intelligent CLI tool that interprets natural language requests and executes safe system commands using AI. Combines LLM capabilities with strict security checks for responsible automation.

**Key Features**:
- 🧠 AI-powered command generation (using Ollama + deepseek-coder)
- 🔒 Multi-layer safety checks for dangerous operations
- 🖥️ OS-aware context gathering (supports Linux, macOS, Windows)
- 📝 Activity logging and system context persistence
- 🎨 Color-coded terminal interface with real-time feedback

**Safety First**:
- 🛡️ Blocklist of dangerous commands/keywords
- 🔍 Regex-based input sanitization
- ⏱️ Execution timeouts (15s max)
- 📂 Isolated context gathering system

**Tech Stack**:
- Python 3.10+
- Ollama local AI framework
- Subprocess management
- JSON context storage
- Cross-platform compatibility

```bash
# Prerequisites
- Ollama installed with deepseek-coder model
- Python 3.10+ with colorama
- Configured context_commands.txt for your OS

# Basic Usage
1. Describe your task in natural language
2. AI generates appropriate command
3. Automatic safety validation
4. Execute verified commands with audit trail
