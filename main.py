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
# PRICE (REAL MARKET)
# =======================
_cache = {"price": 0, "time": 0}

def get_gold_price():
    try:
        if time.time() - _cache["time"] < 5:
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
# EMA CALCULATOR (REAL)
# =======================
prices = []

def ema(values, period):
    if len(values) < period:
        return sum(values) / len(values)

    k = 2 / (period + 1)
    ema_val = values[0]

    for price in values[1:]:
        ema_val = price * k + ema_val * (1 - k)

    return ema_val


# =======================
# SIGNAL ENGINE (REAL EMA CROSS)
# =======================
def get_signal(price):
    prices.append(price)

    if len(prices) > 50:
        prices.pop(0)

    if len(prices) < 10:
        return "WAIT"

    ema_fast = ema(prices[-10:], 5)
    ema_slow = ema(prices[-20:], 10)

    print("EMA FAST:", ema_fast, "EMA SLOW:", ema_slow)

    if ema_fast > ema_slow:
        return "BUY"
    elif ema_fast < ema_slow:
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
            "status": "PRO EMA ENGINE LIVE",
            "mode": "REAL EMA CROSS"
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
🔥 XAUUSD PRO EMA SIGNAL

Signal: {signal}
Entry: {price}
EMA FAST vs SLOW ACTIVE

SL: {sl}
TP1: {tp1}
TP2: {tp2}
"""

        send_discord(msg)

        response = {
            "symbol": "XAUUSD",
            "mode": "PRO_EMA",
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

print("🚀 PRO EMA ENGINE RUNNING (REAL VERSION)")

server.serve_forever()