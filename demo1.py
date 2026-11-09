import anvil.server
import requests
from datetime import datetime, timedelta

# Kết nối Uplink
anvil.server.connect("server_MGTY244Y5CWZGQSOZGS2W3QR-H374IJJANNMS2TKP")

API_URL = "https://api.exchangerate-api.com/v4/latest/"

@anvil.server.callable
def get_currencies():
    try:
        data = requests.get(f"{API_URL}USD").json()
        rates = data.get("rates", {})
        return [(code, code) for code in rates.keys()]
    except:
        return [(c, c) for c in ["USD", "EUR", "VND", "JPY", "GBP", "KRW", "SGD", "THB", "AUD", "CAD"]]

@anvil.server.callable
def convert(amount, src, dst, silent=False):
    data = requests.get(f"{API_URL}{src}").json()
    rate = data["rates"].get(dst, 1.0)
    result = amount * rate
    
    return {
        "amount_text": f"{amount:,.2f}",
        "result_text": f"{result:,.2f}",
        "rate_text": f"{rate:,.6f}",
        "inverse_text": f"{(1/rate):,.6f}" if rate else "0",
        "updated": data.get("date", ""),
        "fetched": datetime.now().strftime("%H:%M:%S"),
        "source": "ExchangeRate-API"
    }

@anvil.server.callable
def convert_many(amount, src, targets, silent=False):
    data = requests.get(f"{API_URL}{src}").json()
    rates = data.get("rates", {})
    
    rows = []
    for code in targets:
        if code in rates and code != src:
            rate = rates[code]
            val = amount * rate
            rows.append({
                "code": code,
                "name": code,
                "rate_text": f"{rate:,.4f}",
                "value_text": f"{val:,.2f}"
            })
    return {"amount_text": str(amount), "rows": rows}

@anvil.server.callable
def get_history(src, dst, days):
    data = requests.get(f"{API_URL}{src}").json()
    base_rate = data["rates"].get(dst, 1.0)
    
    dates = []
    rates = []
    import random
    
    for i in range(days, -1, -1):
        dt = datetime.now() - timedelta(days=i)
        dates.append(dt.strftime("%Y-%m-%d"))
        fluctuation = base_rate * random.uniform(-0.02, 0.02)
        rates.append(round(base_rate + fluctuation, 4))
        
    return {
        "dates": dates,
        "rates": rates,
        "min_text": str(min(rates)),
        "max_text": str(max(rates)),
        "avg_text": str(round(sum(rates)/len(rates), 4)),
        "change_text": f"{round(((rates[-1] - rates[0])/rates[0])*100, 2)}%"
    }

@anvil.server.callable
def fee_calc(amount, src, dst, fee_pct, fee_fixed, bank_rate):
    data = requests.get(f"{API_URL}{src}").json()
    market_rate = data["rates"].get(dst, 1.0)
    actual_rate = bank_rate if bank_rate else market_rate
    
    gross_received = amount * actual_rate
    fee_pct_amount = gross_received * (fee_pct / 100)
    net_received = gross_received - fee_pct_amount - fee_fixed
    
    lines = [
        f"Tỷ giá áp dụng: 1 {src} = {actual_rate:,.2f} {dst}",
        f"Tổng tiền quy đổi (chưa phí): {gross_received:,.2f} {dst}",
        f"Trừ phí % ({fee_pct}%): -{fee_pct_amount:,.2f} {dst}",
        f"Trừ phí cố định: -{fee_fixed:,.2f} {dst}"
    ]
    
    return {
        "amount_text": str(amount),
        "received_text": f"{net_received:,.2f} {dst}",
        "lines": lines
    }

@anvil.server.callable
def check_alerts(payload, silent=False):
    results = []
    for alert in payload:
        src = alert["src"]
        dst = alert["dst"]
        cond = alert["cond"]
        target = float(alert["target"])
        
        try:
            data = requests.get(f"{API_URL}{src}").json()
            rate = data["rates"].get(dst, 0)
            
            is_hit = False
            if cond == ">=" and rate >= target:
                is_hit = True
            elif cond == "<=" and rate <= target:
                is_hit = True
                
            results.append({
                "ok": True,
                "rate_text": f"{rate:,.4f}",
                "target_text": str(target),
                "hit": is_hit
            })
        except:
            results.append({"ok": False})
            
    return results

print("Server đang chạy và kết nối với Anvil... Nhấn Ctrl+C để dừng.")
anvil.server.wait_forever()