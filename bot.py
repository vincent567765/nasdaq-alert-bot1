import yfinance as yf
import pandas as pd
import numpy as np
import requests
import json
import time
from datetime import datetime
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

# =====================================================================
# CONFIGURATION
# =====================================================================
DISCORD_WEBHOOK_URL = "YOUR_DISCORD_WEBHOOK_URL_HERE"
TICKER_SYMBOL = "QQQ"
CHECK_INTERVAL_SECONDS = 900  

# --- Dummy Web Server to satisfy Render's Free Web Service Tier ---
class TinyServer(BaseHTTPRequestHandler):
    def do_GET(self):
        self.send_response(200)
        self.send_header("Content-type", "text/html")
        self.end_headers()
        self.wfile.write(b"Bot is active and running!")

def run_web_server():
    # Render automatically expects your web app to listen on port 10000
    server = HTTPServer(('0.0.0.0', 10000), TinyServer)
    server.serve_forever()

def send_discord_alert(message):
    payload = {"content": message}
    headers = {"Content-Type": "application/json"}
    try:
        response = requests.post(DISCORD_WEBHOOK_URL, data=json.dumps(payload), headers=headers)
    except Exception as e:
        print(f"Network error: {e}")

# =====================================================================
# START THE ALGO LOOP
# =====================================================================
print("Starting background web server thread...")
web_thread = threading.Thread(target=run_web_server, daemon=True)
web_thread.start()

print("ALGO BOT ONLINE: Scanning Nasdaq...")

while True:
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"[{current_time}] Checking market...")
    
    try:
        data = yf.download(TICKER_SYMBOL, period="5d", interval="15m", progress=False)
        if not data.empty and len(data) >= 21:
            if isinstance(data.columns, pd.MultiIndex):
                data.columns = data.columns.get_level_values(0)

            data['Rolling_Mean'] = data['Close'].rolling(window=20).mean()
            data['Rolling_Std'] = data['Close'].rolling(window=20).std()
            data['Upper_Band'] = data['Rolling_Mean'] + (1.2 * data['Rolling_Std'])
            data['Lower_Band'] = data['Rolling_Mean'] - (1.2 * data['Rolling_Std'])

            latest_candle = data.iloc[-2]
            close_price = float(latest_candle['Close'])
            upper_band = float(latest_candle['Upper_Band'])
            lower_band = float(latest_candle['Lower_Band'])

            if close_price < lower_band:
                send_discord_alert(f"ALGO BUY SIGNAL\nAsset: Nasdaq\nPrice: ${close_price:.2f}")
            elif close_price > upper_band:
                send_discord_alert(f"ALGO SELL SIGNAL\nAsset: Nasdaq\nPrice: ${close_price:.2f}")
    except Exception as e:
        print(f"Error: {e}")

    time.sleep(CHECK_INTERVAL_SECONDS)
