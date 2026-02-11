---
name: momentum-scanner
description: "Scan cryptocurrency markets for momentum signals - top gainers, losers, volume spikes, and trending coins. Identifies trading opportunities for momentum traders."
metadata: {"tradeclaw":{"emoji":"📊","requires":{"bins":["curl","jq"],"env":[]},"always":false}}
---

# Momentum Scanner Skill

Identify high-momentum cryptocurrency opportunities using CoinGecko data. Perfect for day traders and swing traders looking for explosive moves.

## Quick Start

```bash
# Ensure coingecko-api skill is available
# Then run these scans:
```

## Scanner Types

### 1. Top Gainers Scanner

Find coins with strongest upward momentum:

```bash
export CG_BASE="https://api.coingecko.com/api/v3"
export CG_KEY=""  # Add your key if using Pro

# Helper for API calls
get_cg() {
  if [ -n "$CG_KEY" ]; then
    curl -s "${CG_BASE}${1}" -H "x-cg-pro-api-key: ${CG_KEY}"
  else
    curl -s "${CG_BASE}${1}"
  fi
}

# Top 20 gainers in 1 hour (min $10M market cap)
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_1h_in_currency // -999) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    volume: .total_volume,
    mcap: .market_cap
  })'

# Top 20 gainers in 24 hours (min $10M market cap)
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // -999) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    volume: .total_volume,
    mcap: .market_cap
  })'

# Top 20 gainers in 7 days (min $10M market cap)
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=7d" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_7d_in_currency // -999) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_24h: .price_change_percentage_24h,
    change_7d: .price_change_percentage_7d_in_currency,
    volume: .total_volume,
    mcap: .market_cap
  })'
```

### 2. Top Losers Scanner

Find potential bounce plays or shorts:

```bash
# Top 20 losers in 24 hours (min $10M market cap)
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // 999) | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    volume: .total_volume,
    mcap: .market_cap
  })'
```

### 3. Volume Leaders Scanner

Identify where the money is flowing:

```bash
# Top 20 by trading volume (all market caps)
get_cg "/coins/markets?vs_currency=usd&order=volume_desc&per_page=50&page=1" | \
  jq '.[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    volume_24h: .total_volume,
    change_24h: .price_change_percentage_24h,
    mcap: .market_cap,
    volume_mcap_ratio: (.total_volume / .market_cap)
  })'

# High volume relative to market cap (indicates strong interest)
get_cg "/coins/markets?vs_currency=usd&order=volume_desc&per_page=100&page=1" | \
  jq '[.[] | select(.market_cap > 1000000)] | sort_by((.total_volume // 0) / (.market_cap // 1)) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    volume_24h: .total_volume,
    mcap: .market_cap,
    volume_mcap_ratio: ((.total_volume // 0) / (.market_cap // 1)),
    change_24h: .price_change_percentage_24h
  })'
```

### 4. Trending Coins Scanner

Discover what's hot right now:

```bash
# Trending from CoinGecko search
echo "=== TRENDING COINS ==="
get_cg "/search/trending" | jq '.coins[].item | {
  rank: .market_cap_rank,
  symbol: .symbol | ascii_upcase,
  name: .name,
  price_btc: .price_btc,
  score: .score
}'

# Combine trending with market data
echo "=== TRENDING + MARKET DATA ==="
get_cg "/search/trending" | jq -r '.coins[].item.id' | \
  while read coin_id; do
    get_cg "/coins/markets?vs_currency=usd&ids=${coin_id}" | jq '.[0] | {
      symbol: .symbol | ascii_upcase,
      name: .name,
      price: .current_price,
      change_24h: .price_change_percentage_24h,
      volume: .total_volume,
      mcap: .market_cap
    }'
  done
```

### 5. Multi-Timeframe Momentum Scanner

Find coins moving across multiple timeframes:

```bash
# Coins up on all timeframes (1h, 24h, 7d) - strong uptrend
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h,24h,7d" | \
  jq '[.[] | select(
    .market_cap >= 5000000 and
    (.price_change_percentage_1h_in_currency // 0) > 0 and
    (.price_change_percentage_24h // 0) > 0 and
    (.price_change_percentage_7d_in_currency // 0) > 0
  )] | sort_by(.price_change_percentage_24h) | reverse | .[:15] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    change_7d: .price_change_percentage_7d_in_currency,
    trend_strength: ((.price_change_percentage_1h_in_currency // 0) + (.price_change_percentage_24h // 0) + (.price_change_percentage_7d_in_currency // 0))
  })'

# Coins down on all timeframes - avoid or short
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h,24h,7d" | \
  jq '[.[] | select(
    .market_cap >= 5000000 and
    (.price_change_percentage_1h_in_currency // 0) < 0 and
    (.price_change_percentage_24h // 0) < 0 and
    (.price_change_percentage_7d_in_currency // 0) < 0
  )] | sort_by(.price_change_percentage_24h) | .[:15] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    change_7d: .price_change_percentage_7d_in_currency
  })'
```

### 6. Breakout Scanner

Find coins breaking out with volume:

```bash
# High volume + positive price action = potential breakout
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=1h,24h" | \
  jq '[.[] | select(
    .market_cap >= 10000000 and
    .market_cap <= 1000000000 and  # Mid-cap focus
    (.price_change_percentage_1h_in_currency // 0) > 3 and  # Strong 1h move
    (.price_change_percentage_24h // 0) > 5 and  # Strong 24h move
    .total_volume > 5000000  # Minimum volume
  )] | sort_by(.price_change_percentage_1h_in_currency) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency,
    change_24h: .price_change_percentage_24h,
    volume: .total_volume,
    mcap: .market_cap,
    breakout_score: ((.price_change_percentage_1h_in_currency // 0) * (.total_volume // 1) / 1000000)
  })'
```

### 7. Micro-Cap Gem Scanner

Find low market cap coins with momentum:

```bash
# Micro-caps ($1M - $50M market cap) with high volume
get_cg "/coins/markets?vs_currency=usd&order=volume_desc&per_page=250&page=1&price_change_percentage=24h" | \
  jq '[.[] | select(
    .market_cap >= 1000000 and
    .market_cap <= 50000000 and
    .total_volume > 1000000 and
    (.price_change_percentage_24h // 0) != 0
  )] | sort_by(.price_change_percentage_24h) | reverse | .[:20] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_24h: .price_change_percentage_24h,
    volume: .total_volume,
    mcap: .market_cap,
    risk_level: (if .market_cap < 10000000 then "HIGH" elif .market_cap < 30000000 then "MEDIUM" else "LOWER" end)
  })'
```

## Advanced Filters

### By Category

```bash
# DeFi coins with momentum
get_cg "/coins/markets?vs_currency=usd&category=decentralized-finance-defi&order=volume_desc&per_page=100" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // 0) | reverse | .[:15]'

# Layer 1 protocols
get_cg "/coins/markets?vs_currency=usd&category=layer-1&order=volume_desc&per_page=100" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // 0) | reverse | .[:15]'
```

### New Listings Watch

```bash
# Recently added coins (use with caution - high volatility)
# Note: This requires Pro API for /coins/list/new endpoint
# Free alternative: Track manually by comparing daily snapshots
```

## Output Formatting

### Pretty Table Format

```bash
# Create formatted output
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=24h" | \
  jq -r '.[] | select(.market_cap > 10000000) | @tsv' | \
  head -20 | \
  awk 'BEGIN {printf "%-8s %-12s %-12s %-12s %-15s\n", "SYMBOL", "PRICE", "24H %", "VOLUME", "MCAP"} 
       {printf "%-8s $%-11.2f %-12.2f $%-14.0f $%-14.0f\n", $3, $4, $22, $7, $6}'
```

### JSON for Dashboards

```bash
# Save scan results for dashboard
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h) | reverse | .[:50]' > \
  ~/.tradeclaw/workspace/momentum_scan_$(date +%Y%m%d_%H%M).json
```

## Trading Signals

### Signal Strength Calculation

```bash
# Combine multiple factors into signal score
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=100&page=1&price_change_percentage=1h,24h,7d" | \
  jq '[.[] | select(.market_cap > 10000000 and .market_cap < 10000000000)] | map({
    symbol: .symbol | ascii_upcase,
    name: .name,
    price: .current_price,
    change_1h: .price_change_percentage_1h_in_currency // 0,
    change_24h: .price_change_percentage_24h // 0,
    change_7d: .price_change_percentage_7d_in_currency // 0,
    volume: .total_volume // 0,
    mcap: .market_cap // 1,
    signal_score: (
      (.price_change_percentage_1h_in_currency // 0) * 0.3 +
      (.price_change_percentage_24h // 0) * 0.5 +
      (.price_change_percentage_7d_in_currency // 0) * 0.2
    ),
    volume_score: ((.total_volume // 0) / (.market_cap // 1) * 100)
  }) | sort_by(.signal_score) | reverse | .[:20]'
```

### Interpretation Guide

| Change % | Signal | Action |
|----------|--------|--------|
| > +20% in 1h | 🚨 FOMO/Dump risk | Wait for pullback |
| +5% to +20% in 1h | 🟢 Strong momentum | Consider entry |
| +2% to +5% in 1h | 🟡 Building momentum | Watch closely |
| -5% to +2% in 1h | ⚪ Consolidating | No action |
| <-5% in 1h | 🔴 Weakness | Avoid or short |
| <-20% in 1h | 🚨 Capitulation | Potential bounce |

## Best Practices

1. **Always use market cap filters** - Avoid illiquid micro-caps for entries
2. **Check volume** - High % gain on low volume = manipulation risk
3. **Multi-timeframe confirmation** - 1h + 24h + 7d alignment = stronger signal
4. **Set alerts** - Don't stare at screens, let subagents notify you
5. **Risk management** - Never risk more than 1-2% on momentum plays
6. **Take profits** - Momentum can reverse quickly; scale out

## Automation Script Template

```bash
#!/bin/bash
# ~/.tradeclaw/workspace/scripts/run_momentum_scan.sh

echo "🚀 Running Momentum Scan - $(date)"

# 1. Top Gainers 24h
echo -e "\n📈 TOP GAINERS (24h)"
get_cg "/coins/markets?vs_currency=usd&order=market_cap_desc&per_page=250&page=1&price_change_percentage=24h" | \
  jq '[.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h) | reverse | .[:10] | .[] | "\(.symbol | ascii_upcase): +\(.price_change_percentage_24h // 0)% ($\(.current_price // 0))"'

# 2. Top Volume
echo -e "\n💰 TOP VOLUME"
get_cg "/coins/markets?vs_currency=usd&order=volume_desc&per_page=20&page=1" | \
  jq '.[] | "\(.symbol | ascii_upcase): Vol $\(.total_volume // 0 | tostring)"'

# 3. Trending
echo -e "\n🔥 TRENDING"
get_cg "/search/trending" | jq '.coins[:5].item | "\(.symbol | ascii_upcase): Rank #\(.market_cap_rank // "N/A")"'

echo -e "\n✅ Scan Complete"
```
