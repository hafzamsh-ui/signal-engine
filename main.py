from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import requests
import os
import time

PORT = int(os.environ.get("PORT", 8000))

DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1507761546023931914/PXFUVJqsRs_cJ3tW_3TvqmoMyr0XDF718ddne06ETtox6wJ4ItCK4FPT6qgbkZPTYihw"

# =======================
# DISCORD
# =======================
def send_discord(msg):
    try:
        requests.post(DISCORD_WEBHOOK, json={"content": msg}, timeout=5)
    except:
        pass


# =======================
# REAL PRICE (Yahoo Finance)
# =======================
_cache = {"price": 0, "time": 0}

def get_gold_price():
    try:
        if time.time() - _cache["time"] < 10 and _cache["price"] != 0:
            return _cache["price"]

        url = "https://query1.finance.yahoo.com/v8/finance/chart/XAUUSD=X"
        r = requests.get(url, timeout=5)
        data = r.json()

        price = data["chart"]["result"][0]["meta"]["regularMarketPrice"]

        _cache["price"] = float(price)
        _cache["time"] = time.time()

        return float(price)

    except:
        return _cache["price"]


# =======================
# SIMPLE REAL LOGIC (TREND-BASED)
# =======================
prices = []

def get_signal(price):
    prices.append(price)

    # keep last 10 candles only
    if len(prices) > 10:
        prices.pop(0)

    if len(prices) < 5:
        return "WAIT"

    # EMA simple approximation
    avg_short = sum(prices[-3:]) / 3
    avg_long = sum(prices) / len(prices)

    # RSI simple approximation
    changes = [prices[i] - prices[i-1] for i in range(1, len(prices))]
    gains = sum([c for c in changes if c > 0])
    losses = abs(sum([c for c in changes if c < 0])) or 1

    rs = gains / losses
    rsi = 100 - (100 / (1 + rs))

    # REAL DECISION LOGIC
    if avg_short > avg_long and rsi < 70:
        return "BUY"
    elif avg_short < avg_long and rsi > 30:
        return "SELL"
    else:
        return "HOLD"


# =======================
# SERVER
# =======================
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps({
            "status": "REAL ENGINE LIVE",
            "mode": "EMA + RSI"
        }).encode())

    def do_POST(self):

        price = get_gold_price()
        signal = get_signal(price)

        if signal == "BUY":
            sl = price - 5
            tp1 = price + 10
            tp2 = price + 20
        elif signal == "SELL":
            sl = price + 5
            tp1 = price - 10
            tp2 = price - 20
        else:
            sl = tp1 = tp2 = price

        msg = f"""
🔥 XAUUSD REAL SIGNAL (EMA+RSI)

Signal: {signal}
Entry: {price}
SL: {sl}
TP1: {tp1}
TP2: {tp2}
"""

        send_discord(msg)

        response = {
            "symbol": "XAUUSD",
            "mode": "REAL_EMA_RSI",
            "signal": signal,
            "entry": price,
            "sl": sl,
            "tp1": tp1,
            "tp2": tp2
        }

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        self.wfile.write(json.dumps(response).encode())


server = HTTPServer(("0.0.0.0", PORT), Handler)

print("🚀 REAL EMA + RSI ENGINE RUNNING")

server.serve_forever()