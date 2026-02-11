# tradeclaw

A crypto trading intellegence AI agent based-on HKUDS/nanobot inspired by OpenClaw. 

# Demo

![tradeclaw video demo](DEMO.mp4)

![tradeclaw video demo](DEMO.png)

<video src="DEMO.mp4" controls width="600"></video>


## Quick Start

```bash
cd tradeclaw
uv run python -m tradeclaw

OR

pip install tradeclaw
tradeclaw onboard                    # Initialize config
# Add API key to ~/.tradeclaw/config.json
tradeclaw agent -m "Identify momentum in last 6 hours."     # Single query
tradeclaw agent                      # Interactive mode
```

## Features

- **Multi-Provider LLM**: OpenAI, Anthropic, DeepSeek, Groq, Gemini via LiteLLM
- **Chat Channels**: WhatsApp, Telegram, Discord, Slack, Feishu, DingTalk, Email, QQ
- **Tool System**: Filesystem, shell, web search/fetch, messaging, cron scheduling
- **Skills**: Markdown-based extensions (GitHub, weather, crypto, etc.)
- **Subagents**: Spawn background tasks with isolated context
- **Security**: Workspace isolation, allow-lists, dangerous command blocking

## Configuration

```json
{
  "providers": {
    "openrouter": {
      "apiKey": "sk-or-..."
    }
  },
  "channels": {
    "telegram": {
      "enabled": true,
      "token": "..."
    }
  }
}
```

## Structure

```
tradeclaw/
├── agent/          # Core loop, context, memory, tools
├── channels/       # Messaging platform integrations  
├── providers/      # LLM provider registry
├── skills/         # Domain-specific capabilities
├── bus/            # Async message queue
└── cron/           # Scheduled task service
```

MIT License
