from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import requests
import os
import time

PORT = int(os.environ.get("PORT", 8000"))

# ====================================
# DISCORD WEBHOOK
# ====================================
DISCORD_WEBHOOK = "https://discord.com/api/webhooks/1507761546023931914/PXFUVJqsRs_cJ3tW_3TvqmoMyr0XDF718ddne06ETtox6wJ4ItCK4FPT6qgbkZPTYihw"

# ====================================
# TWELVEDATA API KEY
# ====================================
API_KEY = "a0fddede1549489f85e5ba07f4f98ac5"


# ====================================
# SEND DISCORD
# ====================================
def send_discord(msg):
    try:
        requests.post(
            DISCORD_WEBHOOK,
            json={"content": msg},
            timeout=5
        )
    except Exception as e:
        print("DISCORD ERROR:", e)


# ====================================
# GET REAL GOLD PRICE
# ====================================
def get_gold_price():

    try:
        url = f"https://api.twelvedata.com/price?symbol=XAU/USD&apikey={API_KEY}"

        r = requests.get(url, timeout=10)

        data = r.json()

        print("PRICE DATA:", data)

        if "price" not in data:
            return 0

        return float(data["price"])

    except Exception as e:
        print("PRICE ERROR:", e)
        return 0


# ====================================
# REAL EMA ENGINE
# ====================================
prices = [
    4500,
    4501,
    4502,
    4503,
    4504,
    4505,
    4506,
    4507,
    4508,
    4509
]


def ema(values, period):

    k = 2 / (period + 1)

    ema_value = values[0]

    for price in values[1:]:
        ema_value = price * k + ema_value * (1 - k)

    return ema_value


# ====================================
# SIGNAL LOGIC
# ====================================
def get_signal(price):

    prices.append(price)

    if len(prices) > 50:
        prices.pop(0)

    ema_fast = ema(prices[-5:], 5)
    ema_slow = ema(prices[-10:], 10)

    print("EMA FAST:", ema_fast)
    print("EMA SLOW:", ema_slow)

    if ema_fast > ema_slow:
        return "BUY"

    elif ema_fast < ema_slow:
        return "SELL"

    else:
        return "HOLD"


# ====================================
# HTTP SERVER
# ====================================
class Handler(BaseHTTPRequestHandler):

    def do_GET(self):

        self.send_response(200)
        self.send_header("Content-type", "application/json")
        self.end_headers()

        response = {
            "status": "PRO EMA ENGINE LIVE",
            "mode": "PRO_EMA_TWELVEDATA"
        }

        self.wfile.write(json.dumps(response).encode())

    def do_POST(self):

        price = get_gold_price()

        if price == 0:

            response = {
                "error": "NO REAL PRICE"
            }

            self.send_response(500)
            self.send_header("Content-type", "application/json")
            self.end_headers()

            self.wfile.write(json.dumps(response).encode())
            return

        signal = get_signal(price)

        if signal == "BUY":

            sl = round(price - 5, 2)
            tp1 = round(price + 10, 2)
            tp2 = round(price + 20, 2)

        elif signal == "SELL":

            sl = round(price + 5, 2)
            tp1 = round(price - 10, 2)
            tp2 = round(price - 20, 2)

        else:

            sl = price
            tp1 = price
            tp2 = price

        msg = f"""
🔥 XAUUSD PRO EMA SIGNAL

Signal: {signal}
Entry: {price}

SL: {sl}
TP1: {tp1}
TP2: {tp2}
"""

        send_discord(msg)

        response = {
            "symbol": "XAUUSD",
            "mode": "PRO_EMA_TWELVEDATA",
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


# ====================================
# START SERVER
# ====================================
server = HTTPServer(("0.0.0.0", PORT), Handler)

print("🚀 PRO EMA TWELVEDATA ENGINE RUNNING")

server.serve_forever()