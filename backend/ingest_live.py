import os
import json
import requests
from datetime import datetime

OUT_PATH = os.path.join(os.path.dirname(__file__), 'live_features.json')

def fetch_bsp_rate():
    try:
        url = 'https://www.bsp.gov.ph/statistics/external/json/rates.json'
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # fallback parsing
            if isinstance(data, dict):
                if 'USD' in data:
                    return float(data['USD'])
                if 'rates' in data and 'USD' in data['rates']:
                    return float(data['rates']['USD'])
    except Exception:
        pass
    return None

def fetch_psa_inflation():
    try:
        url = 'https://open-data.psa.gov.ph/api/3/action/datastore_search?resource_id=cpi_resource_id&limit=1'
        r = requests.get(url, timeout=5)
        if r.status_code == 200:
            data = r.json()
            # implement parsing based on actual PSA response
            return None
    except Exception:
        pass
    return None

def fetch_diesel_price():
    # No standard free API for diesel prices; simulate or connect to supplier APIs
    try:
        base = 59.1
        today = datetime.now().day
        return round(base + (today % 3) * 0.5, 2)
    except Exception:
        return None

def save_features():
    features = {
        'timestamp': datetime.now().isoformat(),
        'exchange_rate': fetch_bsp_rate(),
        'inflation': fetch_psa_inflation(),
        'diesel_price': fetch_diesel_price()
    }
    with open(OUT_PATH, 'w') as f:
        json.dump(features, f)
    print('Saved live features to', OUT_PATH)

if __name__ == '__main__':
    save_features()
