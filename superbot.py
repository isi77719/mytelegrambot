import requests
import time
import re
import random
from datetime import datetime

TOKEN = "7795533464:AAEOZW-KBoV-1TwGHbCiRsp8-8wHhY8i8BA"
URL = f"https://api.telegram.org/bot{TOKEN}/"
ALERTS = {}
LAST_PRICES = {}
ADMIN_CHAT_IDS = [5385459830]

MOTIVASIYA = [
    "Uğurlu ticarət planla başlayır, emosiyalarla yox.",
    "Dəyərli bir imkan – səbr edən üçündür.",
    "Risk – idarə etdikdə fürsətə çevrilir.",
    "Qorxunu tanı, bazarı yox, özünü qalib et."
]

def get_updates():
    response = requests.get(URL + "getUpdates")
    return response.json()

def send_message(chat_id, text):
    requests.post(URL + "sendMessage", data={"chat_id": chat_id, "text": text})

def get_price(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/price?symbol={symbol.upper()}USDT"
        r = requests.get(url)
        return float(r.json()['price'])
    except:
        return None

def analyze_market(symbol):
    try:
        url = f"https://api.binance.com/api/v3/ticker/24hr?symbol={symbol.upper()}USDT"
        r = requests.get(url).json()
        price = float(r['lastPrice'])
        change = float(r['priceChangePercent'])
        high = float(r['highPrice'])
        low = float(r['lowPrice'])
        return f"📊 {symbol.upper()} Analizi:\n🔺 Dəyişmə: {change}%\n📈 Yüksək: {high}$\n📉 Aşağı: {low}$\n💰 Son qiymət: {price}$"
    except:
        return "❌ Analiz alınmadı."

def format_signal_message(coin, price, note, current_price):
    now = datetime.now().strftime("%d.%m.%Y | %H:%M")
    note_text = f"\n💬 Qeyd: {note}" if note else ""
    return (
        f"🚨 Siqnal gəldi!\n"
        f"🪙 Coin: {coin.upper()}\n"
        f"🎯 Hədəf: {price}$\n"
        f"💰 Hazır qiymət: {current_price}${note_text}\n"
        f"📅 {now}"
    )

def calc_position(capital, stop_percent, leverage):
    risk = capital * (stop_percent / 100)
    position = round((risk * leverage), 2)
    return f"💰 Mövqe Tövsiyəsi:\n• Kapital: {capital}$\n• Stop-loss: {stop_percent}%\n• Leverage: {leverage}x\n➡️ Maks. Mövqe Ölçüsü: {position}$"

def check_volatility(symbol):
    try:
        url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}USDT&interval=1h&limit=8"
        r = requests.get(url).json()
        ranges = [float(i[2]) - float(i[3]) for i in r]  # high - low
        avg_range = sum(ranges) / len(ranges)
        if avg_range / float(r[-1][4]) < 0.002:  # 0.2% lik aralıq
            return "❄️ Bazar çox sakitdir. Ticarət risklidir."
        return None
    except:
        return None

def get_klines(symbol, interval='4h', limit=10):
    url = f"https://api.binance.com/api/v3/klines?symbol={symbol.upper()}USDT&interval={interval}&limit={limit}"
    try:
        return requests.get(url).json()
    except:
        return []

def detect_msb(symbol):
    klines = get_klines(symbol, '4h', 10)
    if not klines or len(klines) < 5:
        return None
    highs = [float(k[2]) for k in klines]
    lows = [float(k[3]) for k in klines]
    if highs[-1] > highs[-2] and lows[-1] > lows[-2] and highs[-2] < highs[-3]:
        return "🟢 Uptrend MSB"
    elif highs[-1] < highs[-2] and lows[-1] < lows[-2] and lows[-2] > lows[-3]:
        return "🔻 Downtrend MSB"
    return None

def main():
    last_update_id = None
    print("✅ Bot işləyir...")

    while True:
        updates = get_updates()
        for result in updates.get("result", []):
            update_id = result["update_id"]
            if last_update_id is None or update_id > last_update_id:
                message = result["message"].get("text", "")
                chat_id = result["message"]["chat"]["id"]

                if message.startswith("/start"):
                    send_message(chat_id, "👋 Xoş gəlmisiniz! Siqnal yazın: btc-55000-qeyd")
                elif message.startswith("/help"):
                    send_message(chat_id, "📚 Yardım: btc-55000-qeyd\n/analiz btc\n/qeydlər\n/kapital 100 5 10")
                elif message.startswith("/motivasiya"):
                    send_message(chat_id, random.choice(MOTIVASIYA))
                elif message.startswith("/analiz"):
                    parts = message.split()
                    if len(parts) == 2:
                        send_message(chat_id, analyze_market(parts[1]))
                        vol = check_volatility(parts[1])
                        if vol:
                            send_message(chat_id, vol)
                        msb = detect_msb(parts[1])
                        if msb:
                            send_message(chat_id, f"📉 MSB Siqnalı: {msb}")
                    else:
                        send_message(chat_id, "❌ İstifadə: /analiz btc")
                elif message.startswith("/kapital"):
                    parts = message.split()
                    if len(parts) == 4:
                        try:
                            capital = float(parts[1])
                            stop = float(parts[2])
                            lev = float(parts[3])
                            send_message(chat_id, calc_position(capital, stop, lev))
                        except:
                            send_message(chat_id, "❌ Format: /kapital 100 5 10")

                elif message.startswith("/siyahı"):
                    user_alerts = ALERTS.get(chat_id, [])
                    if not user_alerts:
                        send_message(chat_id, "📭 Aktiv siqnal yoxdur.")
                    else:
                        msg = "📌 Siqnallarınız:\n"
                        for coin, price, note in user_alerts:
                            note_text = f" ({note})" if note else ""
                            msg += f"• {coin.upper()} - {price}${note_text}\n"
                        send_message(chat_id, msg)
                elif message.startswith("/hamısını_sil"):
                    ALERTS[chat_id] = []
                    send_message(chat_id, "🧹 Bütün siqnallar silindi.")
                elif message.startswith("sil"):
                    match = re.match(r"sil ([a-zA-Z]+)-(\d+(\.\d+)?)", message)
                    if match:
                        coin = match.group(1).lower()
                        price = float(match.group(2))
                        if chat_id in ALERTS:
                            ALERTS[chat_id] = [a for a in ALERTS[chat_id] if not (a[0]==coin and a[1]==price)]
                            send_message(chat_id, f"❌ {coin.upper()} {price}$ siqnalı silindi.")
                else:
                    match = re.match(r"([a-zA-Z]+)-(\d+(\.\d+)?)(-(.*))?", message)
                    if match:
                        coin = match.group(1).lower()
                        price = float(match.group(2))
                        note = match.group(5) or ""
                        if chat_id not in ALERTS:
                            ALERTS[chat_id] = []
                        ALERTS[chat_id].append((coin, price, note))
                        send_message(chat_id, f"✅ {coin.upper()} üçün siqnal əlavə olundu: {price}$\n💬 Qeyd: {note}" if note else f"✅ {coin.upper()} üçün siqnal əlavə olundu: {price}$")

                last_update_id = update_id

        # Siqnal yoxlama bölməsi
        for chat_id, alerts in list(ALERTS.items()):
            new_alerts = []
            for coin, target_price, note in alerts:
                current_price = get_price(coin)
                if current_price:
                    last_price = LAST_PRICES.get(coin, current_price)
                    if (last_price < target_price <= current_price) or (last_price > target_price >= current_price):
                        msg = format_signal_message(coin, target_price, note, current_price)
                        send_message(chat_id, msg)
                    else:
                        new_alerts.append((coin, target_price, note))
                    LAST_PRICES[coin] = current_price
                else:
                    new_alerts.append((coin, target_price, note))
            ALERTS[chat_id] = new_alerts

        time.sleep(15)

if __name__ == "__main__":
    main()
