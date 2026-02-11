---
name: coingecko-api
description: "CoinGecko cryptocurrency API integration - Free tier by default, Pro tier optional with API key. Supports spot market data and on-chain DEX data."
metadata: {"tradeclaw":{"emoji":"🪙","requires":{"bins":["curl","jq"],"env":[]},"always":false}}
---

# CoinGecko API Skill

Complete cryptocurrency market data from CoinGecko. Free tier supports most endpoints; Pro tier adds on-chain DEX data and higher rate limits.

## Configuration

Add to `~/.tradeclaw/config.json`:

```json
{
  "coingecko": {
    "api_key": null,
    "use_pro": false,
    "base_url": "https://api.coingecko.com/api/v3"
  }
}
```

For Pro API, set `api_key` and `use_pro: true`:

```json
{
  "coingecko": {
    "api_key": "CG-your-key-here",
    "use_pro": true,
    "base_url": "https://pro-api.coingecko.com/api/v3"
  }
}
```

## Rate Limits

| Tier | Calls/Min | Best For |
|------|-----------|----------|
| Free | 10-30 | Personal monitoring, moderate scanning |
| Pro | 500+ | High-frequency trading bots, on-chain data |

## Core Endpoints (Free Tier)

### Get Current Prices

```bash
# Single or multiple coins
export CG_API_KEY=""  # Leave empty for free tier
export CG_BASE="https://api.coingecko.com/api/v3"

# Get Bitcoin and Ethereum prices
curl -s "${CG_BASE}/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true&include_market_cap=true&include_24hr_vol=true" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq .
```

### Get Market Data (Top Movers, Volume Leaders)

```bash
# Top 100 by market cap with full metrics
curl -s "${CG_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&sparkline=false&price_change_percentage=1h,24h,7d" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq .

# Top gainers in 24h (client-side sort)
curl -s "${CG_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '. | sort_by(.price_change_percentage_24h) | reverse | .[:20]'

# Top losers in 24h
curl -s "${CG_BASE}/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '. | sort_by(.price_change_percentage_24h) | .[:20]'

# Most traded by volume
curl -s "${CG_BASE}/coins/markets?vs_currency=usd&order=volume_desc&per_page=50&page=1" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '.[:20]'
```

### Search & Discovery

```bash
# Search for coins
curl -s "${CG_BASE}/search?query=bitcoin" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '.coins[:5]'

# Trending coins (last 24h)
curl -s "${CG_BASE}/search/trending" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '.coins[].item | {name, symbol, market_cap_rank, price_btc}'

# Get coin list (ID mapping)
curl -s "${CG_BASE}/coins/list" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '.[] | select(.symbol == "btc")'
```

### Categories

```bash
# Top categories by market cap
curl -s "${CG_BASE}/coins/categories" \
  ${CG_API_KEY:+-H "x-cg-pro-api-key: $CG_API_KEY"} | jq '.[:10] | map({name, market_cap, volume_24h})'
```

## Pro API Endpoints (On-Chain DEX Data)

**Requires**: `use_pro: true` and valid `api_key`

### DEX Pools

```bash
export CG_BASE="https://pro-api.coingecko.com/api/v3"
export CG_API_KEY="your-pro-key"

# Get pools on Ethereum
curl -s "${CG_BASE}/onchain/networks/eth/pools?include=base_token,native_token&page=1" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.data[:10]'

# Get specific pool data
curl -s "${CG_BASE}/onchain/networks/eth/pools/0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.'

# Pool OHLCV data
curl -s "${CG_BASE}/onchain/networks/eth/pools/0x8ad599c3a0ff1de082011efddc58f1908eb6e6d8/ohlcv/day?limit=7" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.data.attributes.ohlcv_list'
```

### Token On-Chain Data

```bash
# Get token data by address (WETH on Ethereum)
curl -s "${CG_BASE}/onchain/networks/eth/tokens/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.'

# Get token price across DEXes
curl -s "${CG_BASE}/onchain/simple/networks/eth/token_price/0xc02aaa39b223fe8d0a0e5c4f27ead9083c756cc2" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.'
```

### Top Gainers/Losers (Pro Only)

```bash
# Pre-calculated top gainers (saves computation)
curl -s "${CG_BASE}/coins/top_gainers_losers?vs_currency=usd&duration=24h&top_coins=300" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.top_gainers[:10]'

# Pre-calculated top losers
curl -s "${CG_BASE}/coins/top_gainers_losers?vs_currency=usd&duration=24h&top_coins=300" \
  -H "x-cg-pro-api-key: ${CG_API_KEY}" | jq '.top_losers[:10]'
```

## Helper Scripts

Save these as shell functions in your workspace:

```bash
# ~/.tradeclaw/workspace/scripts/coingecko_helpers.sh

# Get API config from config.json
get_cg_config() {
  python3 -c "import json; c=json.load(open('$HOME/.tradeclaw/config.json')); print(c['coingecko']['base_url'] if c['coingecko']['use_pro'] else 'https://api.coingecko.com/api/v3')" 2>/dev/null || echo "https://api.coingecko.com/api/v3"
}

get_cg_key() {
  python3 -c "import json; c=json.load(open('$HOME/.tradeclaw/config.json')); print(c['coingecko']['api_key'] or '')" 2>/dev/null || echo ""
}

# Fetch with auto config
get_cg() {
  local endpoint="$1"
  local base=$(get_cg_config)
  local key=$(get_cg_key)
  
  if [ -n "$key" ]; then
    curl -s "${base}${endpoint}" -H "x-cg-pro-api-key: ${key}"
  else
    curl -s "${base}${endpoint}"
  fi
}

# Usage:
# get_cg "/coins/markets?vs_currency=usd&per_page=10" | jq .
```

## Response Fields Reference

### /coins/markets response:

```json
{
  "id": "bitcoin",
  "symbol": "btc",
  "name": "Bitcoin",
  "current_price": 97234.52,
  "market_cap": 1923847293847,
  "total_volume": 45382938472,
  "price_change_percentage_1h_in_currency": 0.5,
  "price_change_percentage_24h": 2.3,
  "price_change_percentage_7d_in_currency": 5.1,
  "circulating_supply": 19847263,
  "ath": 108786,
  "ath_change_percentage": -10.5,
  "last_updated": "2026-02-11T14:30:00.000Z"
}
```

## Error Handling

Common errors and solutions:

```bash
# Rate limit exceeded (429)
# Solution: Add delay between calls, upgrade to Pro

# Coin not found (404)
# Solution: Use /coins/list to find correct ID

# Invalid API key (401)
# Solution: Check key validity for Pro endpoints
```

## Tips for Subagents

1. **Always check rate limits**: Free tier allows ~1 call per 2-3 seconds
2. **Cache results**: Store previous fetches in workspace files
3. **Filter client-side**: Fetch 250 coins, then filter/sort in code
4. **Use jq for parsing**: Fast JSON transformation
5. **Handle missing data**: Some fields may be null for low-cap coins
