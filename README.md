# tradeclaw

A real-time crypto trading dashboard in Telegram chat. An AI agent based-on HKUDS/nanobot inspired by Clawdbot. 

# Demo

![tradeclaw background video demo](DEMO_background.mp4)

![tradeclaw chat video demo](DEMO_chat.mp4)

![tradeclaw video demo](DEMO.png)

<video src="DEMO_background.mp4" controls width="600"></video>

<video src="DEMO_chat.mp4" controls width="600"></video>

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

Clawdbot of real-time crypto trading dashboard using CoinGecko.

#### Descriptions

An AI agent which has access to crypto trading real-time data, provides alert monitor, trading momentum scanner and answer pricing data. 

#### Problem

Dashboard is not feasible to check on phone. 

Clawdbot demostrated general public is happy about interacting AI agent through mobile messenging app.

#### Solution

Crypto trading data is presented as chats with AI agent, instead of interacting with a dashboard. (echo with a trend talked by one of the Concensus stage speaker).

#### Tech descriptions

Based on HKUDS/nanobot, which is a lightweight version of Clawdbot. 

Wrapped functionalities in subagents, further instructions in agent skills.

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
