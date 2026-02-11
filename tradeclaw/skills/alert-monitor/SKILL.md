---
name: alert-monitor
description: "Persistent cryptocurrency monitoring subagent - continuously watches for price movements, volume spikes, and trending signals. Triggers alerts when thresholds are crossed."
metadata: {"tradeclaw":{"emoji":"🚨","requires":{"bins":["curl","jq"],"env":[]},"always":false}}
---

# Alert Monitor Skill

Run a **persistent subagent** that continuously monitors cryptocurrency markets and triggers alerts when significant moves occur. Perfect for day traders who need real-time notifications.

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                 PERSISTENT MONITOR LOOP                      │
│                   (Runs Every N Seconds)                     │
├─────────────────────────────────────────────────────────────┤
│                                                              │
│   1. LOAD STATE → 2. FETCH DATA → 3. ANALYZE → 4. ALERT   │
│        ↑__________________________________________↓         │
│                                                              │
│   State Files:                                               │
│   • price_cache.json        - Previous prices                │
│   • volume_baseline.json    - Rolling volume averages        │
│   • alerts_log.json         - All triggered alerts           │
│   • monitor_config.json     - Thresholds & settings          │
│                                                              │
└─────────────────────────────────────────────────────────────┘
```

## Setup

### 1. Create Monitor Configuration

```bash
# Create config directory
mkdir -p ~/.tradeclaw/workspace/crypto_monitor

# Create monitor configuration
cat > ~/.tradeclaw/workspace/crypto_monitor/config.json << 'EOF'
{
  "monitor": {
    "interval_seconds": 300,
    "alert_threshold_pct": 5.0,
    "volume_spike_multiplier": 2.0,
    "min_market_cap_usd": 10000000,
    "max_market_cap_usd": 100000000000,
    "watchlist": ["bitcoin", "ethereum", "solana", "cardano", "polkadot"],
    "auto_discover_trending": true,
    "onchain_enabled": false
  },
  "coingecko": {
    "api_key": null,
    "use_pro": false
  },
  "alerts": {
    "price_spike": true,
    "volume_spike": true,
    "new_trending": true,
    "breakout": true,
    "dump": true
  }
}
EOF
```

### 2. Initialize State Files

```bash
# Initialize empty state files
echo '{}' > ~/.tradeclaw/workspace/crypto_monitor/price_cache.json
echo '{}' > ~/.tradeclaw/workspace/crypto_monitor/volume_baseline.json
echo '[]' > ~/.tradeclaw/workspace/crypto_monitor/alerts_log.json
```

## The Monitor Script

Create this script that the subagent will run continuously:

```bash
#!/bin/bash
# ~/.tradeclaw/workspace/crypto_monitor/monitor.sh

CONFIG_FILE="$HOME/.tradeclaw/workspace/crypto_monitor/config.json"
PRICE_CACHE="$HOME/.tradeclaw/workspace/crypto_monitor/price_cache.json"
VOLUME_BASELINE="$HOME/.tradeclaw/workspace/crypto_monitor/volume_baseline.json"
ALERTS_LOG="$HOME/.tradeclaw/workspace/crypto_monitor/alerts_log.json"
DASHBOARD_FILE="$HOME/.tradeclaw/workspace/crypto_monitor/dashboard.json"

# Load config
INTERVAL=$(jq -r '.monitor.interval_seconds // 300' "$CONFIG_FILE")
THRESHOLD=$(jq -r '.monitor.alert_threshold_pct // 5.0' "$CONFIG_FILE")
VOLUME_MULT=$(jq -r '.monitor.volume_spike_multiplier // 2.0' "$CONFIG_FILE")
MIN_MCAP=$(jq -r '.monitor.min_market_cap_usd // 10000000' "$CONFIG_FILE")
MAX_MCAP=$(jq -r '.monitor.max_market_cap_usd // 100000000000' "$CONFIG_FILE")
WATCHLIST=$(jq -r '.monitor.watchlist | join(",")' "$CONFIG_FILE")
USE_PRO=$(jq -r '.coingecko.use_pro // false' "$CONFIG_FILE")
API_KEY=$(jq -r '.coingecko.api_key // empty' "$CONFIG_FILE")

# API setup
if [ "$USE_PRO" = "true" ] && [ -n "$API_KEY" ]; then
  CG_BASE="https://pro-api.coingecko.com/api/v3"
  AUTH_HEADER="-H x-cg-pro-api-key: ${API_KEY}"
else
  CG_BASE="https://api.coingecko.com/api/v3"
  AUTH_HEADER=""
fi

log() {
  echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

fetch_market_data() {
  local ids="$1"
  if [ -n "$AUTH_HEADER" ]; then
    curl -s "${CG_BASE}/coins/markets?vs_currency=usd&ids=${ids}&price_change_percentage=1h,24h" \
      -H "x-cg-pro-api-key: ${API_KEY}"
  else
    curl -s "${CG_BASE}/coins/markets?vs_currency=usd&ids=${ids}&price_change_percentage=1h,24h"
  fi
}

fetch_trending() {
  if [ -n "$AUTH_HEADER" ]; then
    curl -s "${CG_BASE}/search/trending" \
      -H "x-cg-pro-api-key: ${API_KEY}"
  else
    curl -s "${CG_BASE}/search/trending"
  fi
}

check_price_alerts() {
  local data="$1"
  local alerts=""
  
  alerts=$(echo "$data" | jq --arg threshold "$THRESHOLD" --argjson cache "$(cat $PRICE_CACHE)" '
    .[] | select(.current_price != null) | 
    .id as $id |
    .current_price as $new_price |
    .price_change_percentage_1h_in_currency as $change_1h |
    .price_change_percentage_24h as $change_24h |
    .symbol as $symbol |
    .name as $name |
    ($cache[$id] // .current_price) as $old_price |
    if (($change_1h | fabs) >= ($threshold | tonumber)) then
      {
        type: (if $change_1h > 0 then "PRICE_SPIKE" else "PRICE_DUMP" end),
        symbol: ($symbol | ascii_upcase),
        name: $name,
        change_1h: $change_1h,
        change_24h: $change_24h,
        price: $new_price,
        timestamp: now | todate
      }
    elif (($change_24h | fabs) >= ($threshold | tonumber)) then
      {
        type: (if $change_24h > 0 then "PRICE_SPIKE_24H" else "PRICE_DUMP_24H" end),
        symbol: ($symbol | ascii_upcase),
        name: $name,
        change_1h: $change_1h,
        change_24h: $change_24h,
        price: $new_price,
        timestamp: now | todate
      }
    else
      empty
    end
  ')
  
  echo "$alerts"
}

check_volume_spikes() {
  local data="$1"
  local alerts=""
  
  alerts=$(echo "$data" | jq --arg mult "$VOLUME_MULT" --argjson baseline "$(cat $VOLUME_BASELINE)" '
    .[] | select(.total_volume != null) |
    .id as $id |
    .total_volume as $new_vol |
    .symbol as $symbol |
    .name as $name |
    .current_price as $price |
    ($baseline[$id] // ($new_vol / 2)) as $avg_vol |
    if $new_vol > ($avg_vol * ($mult | tonumber)) then
      {
        type: "VOLUME_SPIKE",
        symbol: ($symbol | ascii_upcase),
        name: $name,
        volume: $new_vol,
        avg_volume: $avg_vol,
        spike_ratio: ($new_vol / $avg_vol),
        price: $price,
        timestamp: now | todate
      }
    else
      empty
    end
  ')
  
  echo "$alerts"
}

check_breakouts() {
  local data="$1"
  
  echo "$data" | jq '
    .[] | select(
      .market_cap >= 10000000 and
      .market_cap <= 1000000000 and
      (.price_change_percentage_1h_in_currency // 0) > 5 and
      (.price_change_percentage_24h // 0) > 10 and
      .total_volume > 5000000
    ) | {
      type: "BREAKOUT",
      symbol: (.symbol | ascii_upcase),
      name: .name,
      price: .current_price,
      change_1h: .price_change_percentage_1h_in_currency,
      change_24h: .price_change_percentage_24h,
      volume: .total_volume,
      mcap: .market_cap,
      timestamp: now | todate
    }
  '
}

update_cache() {
  local data="$1"
  
  # Update price cache
  echo "$data" | jq '[.[] | select(.current_price != null)] | map({(.id): .current_price}) | add // {}' > "$PRICE_CACHE"
  
  # Update volume baseline (rolling average)
  echo "$data" | jq --argjson baseline "$(cat $VOLUME_BASELINE)" '
    [ .[] | select(.total_volume != null) ] |
    map({
      key: .id,
      value: ((($baseline[.id] // .total_volume) * 0.7) + (.total_volume * 0.3))
    }) |
    from_entries
  ' > "$VOLUME_BASELINE"
}

log_alert() {
  local alert="$1"
  echo "$alert" | jq '.' >> "$ALERTS_LOG"
}

format_alert_message() {
  local alert="$1"
  local type=$(echo "$alert" | jq -r '.type')
  local symbol=$(echo "$alert" | jq -r '.symbol')
  local name=$(echo "$alert" | jq -r '.name')
  local price=$(echo "$alert" | jq -r '.price // 0')
  
  case "$type" in
    "PRICE_SPIKE")
      local change=$(echo "$alert" | jq -r '.change_1h // 0')
      echo "🚀 PRICE ALERT: $symbol (+${change}%) at $${price}"
      ;;
    "PRICE_DUMP")
      local change=$(echo "$alert" | jq -r '.change_1h // 0')
      echo "🔻 DUMP ALERT: $symbol (${change}%) at $${price}"
      ;;
    "VOLUME_SPIKE")
      local ratio=$(echo "$alert" | jq -r '.spike_ratio // 0')
      echo "💥 VOLUME SPIKE: $symbol (${ratio}x avg volume) at $${price}"
      ;;
    "BREAKOUT")
      local change=$(echo "$alert" | jq -r '.change_24h // 0')
      echo "⚡ BREAKOUT: $symbol (+${change}% in 24h) at $${price}"
      ;;
    *)
      echo "📊 ALERT: $symbol ($type) at $${price}"
      ;;
  esac
}

update_dashboard() {
  local data="$1"
  local timestamp=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
  
  echo "$data" | jq --arg ts "$timestamp" '{
    last_updated: $ts,
    top_gainers: ([.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // 0) | reverse | .[:10] | map({symbol: (.symbol | ascii_upcase), change_24h: .price_change_percentage_24h, price: .current_price})),
    top_losers: ([.[] | select(.market_cap > 10000000)] | sort_by(.price_change_percentage_24h // 0) | .[:10] | map({symbol: (.symbol | ascii_upcase), change_24h: .price_change_percentage_24h, price: .current_price})),
    volume_leaders: (. | sort_by(.total_volume // 0) | reverse | .[:10] | map({symbol: (.symbol | ascii_upcase), volume: .total_volume, price: .current_price})),
    total_monitored: length
  }' > "$DASHBOARD_FILE"
}

# Main monitoring loop
log "Starting crypto monitor (interval: ${INTERVAL}s, threshold: ${THRESHOLD}%)"
log "Monitoring: $WATCHLIST"

while true; do
  log "Fetching market data..."
  
  # Fetch data for watchlist
  DATA=$(fetch_market_data "$WATCHLIST")
  
  if [ -z "$DATA" ] || [ "$DATA" = "[]" ]; then
    log "⚠️  No data received, retrying in ${INTERVAL}s..."
    sleep "$INTERVAL"
    continue
  fi
  
  # Check for alerts
  PRICE_ALERTS=$(check_price_alerts "$DATA")
  VOLUME_ALERTS=$(check_volume_spikes "$DATA")
  BREAKOUT_ALERTS=$(check_breakouts "$DATA")
  
  # Process and log alerts
  ALL_ALERTS=$(echo -e "${PRICE_ALERTS}\n${VOLUME_ALERTS}\n${BREAKOUT_ALERTS}" | jq -s '. | flatten | map(select(. != null))')
  
  if [ "$(echo "$ALL_ALERTS" | jq 'length')" -gt 0 ]; then
    log "🚨 $(echo "$ALL_ALERTS" | jq 'length') alert(s) triggered:"
    echo "$ALL_ALERTS" | jq -c '.[]' | while read -r alert; do
      msg=$(format_alert_message "$alert")
      log "$msg"
      log_alert "$alert"
      
      # Write to notifications file for main agent pickup
      echo "$msg" >> "$HOME/.tradeclaw/workspace/crypto_monitor/notifications.txt"
    done
  fi
  
  # Update caches
  update_cache "$DATA"
  
  # Update dashboard
  update_dashboard "$DATA"
  
  log "✅ Cycle complete. Sleeping ${INTERVAL}s..."
  log "------------------------------------------------"
  
  sleep "$INTERVAL"
done
```

## Running the Monitor

### Start Persistent Subagent

```bash
# Method 1: Direct spawn
tradeclaw agent -m "Spawn a persistent subagent to run the crypto monitor script at ~/.tradeclaw/workspace/crypto_monitor/monitor.sh and report any alerts immediately"

# Method 2: Background execution with log
nohup bash ~/.tradeclaw/workspace/crypto_monitor/monitor.sh > ~/.tradeclaw/workspace/crypto_monitor/monitor.log 2>&1 &
echo $! > ~/.tradeclaw/workspace/crypto_monitor/monitor.pid
```

### Stop Monitor

```bash
# Kill the background process
kill $(cat ~/.tradeclaw/workspace/crypto_monitor/monitor.pid)
```

## Alert Output Examples

### Price Spike Alert
```
🚀 PRICE ALERT: SOL (+8.45%) at $198.34
├── Previous: $182.89
├── Change: +$15.45 (+8.45%)
├── Volume: $4.2B (1.8x average)
├── Signal: STRONG MOMENTUM
└── Action: Monitor for continuation or pullback
```

### Volume Spike Alert
```
💥 VOLUME SPIKE: PEPE (4.2x avg volume) at $0.0000089
├── Volume: $890M (vs $212M avg)
├── Price: +12.3% (1h)
├── Social: Trending on Twitter
└── Signal: HIGH INTEREST - Possible whale activity
```

### Breakout Alert
```
⚡ BREAKOUT: AR +18.4% in 24h at $12.45
├── Market Cap: $890M (mid-cap)
├── Volume: $45M (5.2x average)
├── Resistance: Broken at $11.80
├── Next Target: $15.00
└── Signal: MOMENTUM BREAKOUT
```

### Dump Alert
```
🔻 DUMP ALERT: DOGE (-7.2%) at $0.082
├── Support: $0.080 level
├── Volume: $1.2B (high selling pressure)
├── Change: -$0.0064
└── Signal: STOP LOSS HIT - Avoid catching knife
```

## Advanced Features

### 1. Multi-Timeframe Alerts

Modify `check_price_alerts()` to track multiple timeframes:

```bash
# Alert on 1h, 4h, and 24h moves
check_multitimeframe() {
  # Requires storing 1h, 4h, and 24h price history
  # Alert when all three show same direction
}
```

### 2. Support/Resistance Breaks

```bash
# Track key levels and alert on breaks
check_breaks() {
  local data="$1"
  # Compare current price against stored S/R levels
  # Alert on confirmed break with volume
}
```

### 3. On-Chain DEX Monitoring (Pro API)

```bash
# Monitor DEX pool changes
monitor_onchain() {
  if [ "$USE_PRO" = "true" ]; then
    # Fetch /onchain/networks/eth/pools
    # Alert on liquidity changes > 20%
    # Alert on new pool creation for watchlist tokens
  fi
}
```

### 4. Trending Discovery Integration

```bash
# Auto-add trending coins to watchlist
auto_discover() {
  if [ "$AUTO_DISCOVER" = "true" ]; then
    TRENDING=$(fetch_trending | jq -r '.coins[].item.id')
    # Update watchlist with new trending coins
    # Remove old ones if list gets too long
  fi
}
```

## Dashboard File

The monitor creates a live dashboard at:
`~/.tradeclaw/workspace/crypto_monitor/dashboard.json`

```json
{
  "last_updated": "2026-02-11T14:45:00Z",
  "top_gainers": [
    {"symbol": "SOL", "change_24h": 12.3, "price": 198.45},
    {"symbol": "PEPE", "change_24h": 28.4, "price": 0.0000089}
  ],
  "top_losers": [
    {"symbol": "DOGE", "change_24h": -7.2, "price": 0.082}
  ],
  "volume_leaders": [
    {"symbol": "BTC", "volume": 45200000000, "price": 97234}
  ],
  "total_monitored": 25
}
```

## Best Practices

1. **Rate Limiting**: Free tier = 5 min intervals minimum
2. **Battery Life**: Use longer intervals (600s+) for mobile
3. **Noise Reduction**: Increase threshold % in volatile markets
4. **Market Cap Filters**: Always filter out < $10M (illiquid)
5. **Volume Confirmation**: Never trust price moves without volume
6. **Logging**: Keep alerts_log.json for backtesting
7. **Health Checks**: Monitor if script is still running

## Troubleshooting

```bash
# Check if monitor is running
ps aux | grep monitor.sh

# View recent logs
tail -50 ~/.tradeclaw/workspace/crypto_monitor/monitor.log

# Check alert count
jq 'length' ~/.tradeclaw/workspace/crypto_monitor/alerts_log.json

# Reset all state
rm ~/.tradeclaw/workspace/crypto_monitor/*.json
echo '{}' > ~/.tradeclaw/workspace/crypto_monitor/price_cache.json
echo '{}' > ~/.tradeclaw/workspace/crypto_monitor/volume_baseline.json
echo '[]' > ~/.tradeclaw/workspace/crypto_monitor/alerts_log.json
```

## Integration with Main Agent

The subagent writes alerts to `notifications.txt` which the main agent can read:

```bash
# Main agent command to check for alerts
tradeclaw agent -m "Check ~/.tradeclaw/workspace/crypto_monitor/notifications.txt for new alerts and summarize them"
```

Or set up a file watcher to trigger alerts instantly!
