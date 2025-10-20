# stock_api.py
import os
import requests

API_KEY = "eU3Dq0r2CtLvfZRWaaieGg==4TZuOWxv5ttEHJ9T"



def build_ticker(nse_code: str = None, bse_code: str = None) -> str | None:
    nse = (nse_code or "").strip()
    bse = (bse_code or "").strip()
    if nse:
        return f"{nse}.NS"
    if bse:
        return f"{bse}.BO"
    return None

def get_stock_price(ticker: str):
    api_url = f"https://api.api-ninjas.com/v1/stockprice?ticker={ticker}"
    try:
        resp = requests.get(api_url, headers={'X-Api-Key': API_KEY}, timeout=10)
        if resp.status_code == 200:
            # Example wanted: {"ticker":"ENDURANCE.NS","name":"...","price":2892,"exchange":"NSE","updated":..., "currency":"INR"}
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}", "message": resp.text}
    except requests.exceptions.RequestException as e:
        return {"error": "Request failed", "message": str(e)}
