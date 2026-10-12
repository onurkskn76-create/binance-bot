import ccxt
import time
import requests

# Telegram Bilgilerin (Kendi bilgilerini buraya yaz)
TELEGRAM_TOKEN = "BURAYA_BOT_TOKENINI_YAZ"
TELEGRAM_CHAT_ID = "BURAYA_CHAT_ID_YAZ"

def send_telegram(message):
    url = f"https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage"
    payload = {"chat_id": TELEGRAM_CHAT_ID, "text": message, "parse_mode": "Markdown"}
    try:
        requests.post(url, json=payload, timeout=10)
    except:
        pass

def run_scanner():
    exchange = ccxt.binance({'options': {'defaultType': 'future'}, 'enableRateLimit': True})
    markets = exchange.load_markets()
    symbols = [s for s, m in markets.items() if m['linear'] and m['active'] and s.endswith('/USDT:USDT')]
    
    try:
        btc_ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', timeframe='15m', limit=100)
        btc_closes = [c[4] for c in btc_ohlcv]
        is_btc_bull = btc_closes[-1] > (sum(btc_closes[-50:]) / 50) # Daha esnek kısa EMA
    except:
        is_btc_bull = True

    for symbol in symbols:
        try:
            ohlcv_15m = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=100)
            
            if len(ohlcv_15m) < 50:
                continue
                
            closes_15m = [c[4] for c in ohlcv_15m]
            highs_15m  = [c[2] for c in ohlcv_15m]
            lows_15m   = [c[3] for c in ohlcv_15m]
            vols_15m   = [c[5] for c in ohlcv_15m]
            opens_15m  = [c[1] for c in ohlcv_15m]
            
            c_val, op_val = closes_15m[-1], opens_15m[-1]
            h_val, l_val, v_val = highs_15m[-1], lows_15m[-1], vols_15m[-1]
            
            # --- AGRESİF & SERİ FİLTRELEME ---
            # 1. 15m Kısa Trend (50 EMA - Daha hızlı tepki verir)
            ema_fast = sum(closes_15m[-50:]) / 50
            trend_up   = c_val > ema_fast
            trend_down = c_val < ema_fast
            
            # 2. CVD Hacim Baskısı (Hafif esnetildi)
            delta = (c_val - op_val) / (h_val - l_val if h_val != l_val else 1) * v_val
            cvd_bull = delta >= 0
            cvd_bear = delta <= 0
            
            # 3. Kaos Filtresi (Aşırı aşırı kaos olmadıkça tıkamaz)
            tr_list = [max(highs_15m[i] - lows_15m[i], abs(highs_15m[i] - closes_15m[i-1])) for i in range(1, len(ohlcv_15m))]
            is_chaos = (sum(tr_list[-10:]) / 10) > ((sum(tr_list[-30:]) / 30) * 2.8)
            
            is_clean = not is_chaos
            
            # Daha seri tetiklenen esnetilmiş karar mekanizması
            long_signal  = is_clean and trend_up and cvd_bull
            short_signal = is_clean and trend_down and cvd_bear
            
            coin_name = symbol.split('/')[0]
            
            if long_signal:
                send_telegram(f"⚡ *SERİ LONG SİNYALİ!*\nCoin: `{coin_name}USDT`\nFiyat: `{c_val}`")
            elif short_signal:
                send_telegram(f"⚡ *SERİ SHORT SİNYALİ!*\nCoin: `{coin_name}USDT`\nFiyat: `{c_val}`")
                
            time.sleep(0.05)
        except:
            continue

if __name__ == "__main__":
    run_scanner()
