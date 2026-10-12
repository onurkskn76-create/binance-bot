import ccxt
import time
import requests

# 1. ADIMDA ALDIĞIN TELEGRAM BİLGİLERİNİ BURAYA YAZ:
TELEGRAM_TOKEN = "8136411060:AAEq_ESAkhg-f-eKAfKk6jzXO7j2FzJ9Zdw"
TELEGRAM_CHAT_ID = "7380293899"

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
        btc_ohlcv = exchange.fetch_ohlcv('BTC/USDT:USDT', timeframe='15m', limit=200)
        btc_closes = [c[4] for c in btc_ohlcv]
        is_btc_bull = btc_closes[-1] > (sum(btc_closes) / len(btc_closes))
    except:
        is_btc_bull = True

    for symbol in symbols:
        try:
            ohlcv_15m = exchange.fetch_ohlcv(symbol, timeframe='15m', limit=200)
            ohlcv_1h  = exchange.fetch_ohlcv(symbol, timeframe='1h', limit=50)
            
            if len(ohlcv_15m) < 200 or len(ohlcv_1h) < 50:
                continue
                
            closes_15m = [c[4] for c in ohlcv_15m]
            highs_15m  = [c[2] for c in ohlcv_15m]
            lows_15m   = [c[3] for c in ohlcv_15m]
            vols_15m   = [c[5] for c in ohlcv_15m]
            opens_15m  = [c[1] for c in ohlcv_15m]
            
            c_val, op_val = closes_15m[-1], opens_15m[-1]
            h_val, l_val, v_val = highs_15m[-1], lows_15m[-1], vols_15m[-1]
            
            # 5 Altın Filtre Kuralı
            trend_up   = c_val > (sum(closes_15m) / 200)
            trend_down = c_val < (sum(closes_15m) / 200)
            htf_bull   = closes_1h[-1] > (sum([c[4] for c in ohlcv_1h]) / 50)
            
            delta = (c_val - op_val) / (h_val - l_val if h_val != l_val else 1) * v_val
            cvd_bull = delta > 0
            cvd_bear = delta < 0
            
            tr_list = [max(highs_15m[i] - lows_15m[i], abs(highs_15m[i] - closes_15m[i-1])) for i in range(1, len(ohlcv_15m))]
            is_chaos = (sum(tr_list[-14:]) / 14) > ((sum(tr_list[-50:]) / 50) * 2.2)
            
            is_clean = not is_chaos
            long_signal  = is_clean and trend_up and htf_bull and is_btc_bull and cvd_bull
            short_signal = is_clean and trend_down and not htf_bull and not is_btc_bull and cvd_bear
            
            coin_name = symbol.split('/')[0]
            
            if long_signal:
                send_telegram(f"🚀 *NET LONG SİNYALİ!*\nCoin: `{coin_name}USDT`\nFiyat: `{c_val}`")
            elif short_signal:
                send_telegram(f"💥 *NET SHORT SİNYALİ!*\nCoin: `{coin_name}USDT`\nFiyat: `{c_val}`")
                
            time.sleep(0.1)
        except:
            continue

if __name__ == "__main__":
    run_scanner()
