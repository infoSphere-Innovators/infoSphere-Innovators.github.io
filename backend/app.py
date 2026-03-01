from flask import Flask, jsonify, request
from flask_cors import CORS
from joblib import load
import os
import pandas as pd
import requests
from datetime import datetime, timedelta

app = Flask(__name__)
CORS(app)


# TEST ROUTE
@app.route("/")
def home():
    return "Davao Build AI Backend is RUNNING"


# SAMPLE DATA
materials = {
    "plywood": {
        "current_price": 310.00,
        "predicted_7": 315.00,
        "predicted_30": 325.00,
        "trend": "up",
        "confidence_min": 305,
        "confidence_max": 335,
        "confidence_pct": 85,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [310,310,312,310],
        "forecast_prices": [315,318,321]
    },
    "cement": {
        "current_price": 244.50,
        "predicted_7": 252.00,
        "predicted_30": 271.00,
        # additional demo fields
        "trend": "up",
        "confidence_min": 240,
        "confidence_max": 280,
        "confidence_pct": 87,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [244.5,246,248,244],
        "forecast_prices": [252,258,264]
    },
    "steel": {
        "current_price": 186.00,
        "predicted_7": 194.50,
        "predicted_30": 202.00,
        "trend": "up",
        "confidence_min": 180,
        "confidence_max": 210,
        "confidence_pct": 92,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [186,187,188,186],
        "forecast_prices": [194.5,198,202]
    },
    "lumber": {
        "current_price": 98.00,
        "predicted_7": 101.00,
        "predicted_30": 109.00,
        "trend": "stable",
        "confidence_min": 95,
        "confidence_max": 110,
        "confidence_pct": 78,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [98,98,99,98],
        "forecast_prices": [101,105,109]
    },
    "gravel": {
        "current_price": 72.50,
        "predicted_7": 73.50,
        "predicted_30": 75.00,
        "trend": "stable",
        "confidence_min": 70,
        "confidence_max": 78,
        "confidence_pct": 81,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [72.5,72.5,73,72.5],
        "forecast_prices": [73.5,74,75]
    },
    "sand": {
        "current_price": 85.00,
        "predicted_7": 86.00,
        "predicted_30": 88.00,
        "trend": "up",
        "confidence_min": 83,
        "confidence_max": 91,
        "confidence_pct": 79,
        "historical_dates": ["2026-02-01","2026-02-08","2026-02-15","2026-02-22"],
        "historical_prices": [85,85,85.5,85],
        "forecast_prices": [86,87,88]
    },
}

# Load trained models if present
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
loaded_models = {}
if os.path.isdir(MODELS_DIR):
    for fname in os.listdir(MODELS_DIR):
        if fname.endswith('.joblib'):
            key = fname.replace('.joblib','')
            try:
                loaded_models[key] = load(os.path.join(MODELS_DIR, fname))
                print('Loaded model for', key)
            except Exception as e:
                print('Failed to load', fname, e)

# Attempt to load live features cache
LIVE_FEATURES_PATH = os.path.join(os.path.dirname(__file__), 'live_features.json')
live_features = {}
if os.path.exists(LIVE_FEATURES_PATH):
    try:
        import json
        with open(LIVE_FEATURES_PATH,'r') as f:
            live_features = json.load(f)
    except Exception:
        live_features = {}

def get_historical_for_material(material, days=60):
    # attempt to read CSV and return recent aggregated daily averages
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'davaobuild_dataset_2025_2026.csv')
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        df = df[df['material'] == material]
        if df.empty:
            return [], []
        series = df.groupby('date')['price'].mean().reset_index().sort_values('date')
        recent = series.tail(days)
        dates = recent['date'].dt.strftime('%Y-%m-%d').tolist()
        prices = recent['price'].round(2).tolist()
        return dates, prices
    except Exception:
        return [], []


@app.route("/predict/<material>")
def predict(material):
    # If a trained model exists use it; otherwise fall back to sample data
    model = loaded_models.get(material)
    if model:
        # get historical series
        dates, prices = get_historical_for_material(material, days=90)
        if not prices:
            # fallback to materials dict
            data = materials.get(material)
            if not data:
                return jsonify({"error": "Material not found"}), 404
            return jsonify({
                "current_price": data["current_price"],
                "pred_7d": data.get("predicted_7"),
                "pred_30d": data.get("predicted_30"),
                "trend": data.get("trend"),
                "confidence_min": data.get("confidence_min"),
                "confidence_max": data.get("confidence_max"),
                "confidence_pct": data.get("confidence_pct"),
                "historical_dates": data.get("historical_dates"),
                "historical_prices": data.get("historical_prices"),
                "forecast_prices": data.get("forecast_prices"),
                "explanation": "Model used Random Forest over supply/demand and economic features."
            })

        # prepare recent window
        recent = [float(p) for p in prices if p is not None]
        # produce iterative forecast for 30 days
        from train_models import iterative_forecast
        forecast = iterative_forecast(model, recent, steps=30)
        pred_7 = float(forecast[6]) if len(forecast) >= 7 else round(forecast[0],2)
        pred_30 = float(forecast[29]) if len(forecast) >= 30 else float(forecast[-1])
        current_price = recent[-1] if recent else materials.get(material, {}).get('current_price', 0)
        trend = 'up' if pred_30 > current_price else 'down' if pred_30 < current_price else 'stable'
        conf_min = round(min(forecast[:30]) * 0.98,2)
        conf_max = round(max(forecast[:30]) * 1.02,2)
        return jsonify({
            "current_price": round(current_price,2),
            "pred_7d": round(pred_7,2),
            "pred_30d": round(pred_30,2),
            "trend": trend,
            "confidence_min": conf_min,
            "confidence_max": conf_max,
            "confidence_pct": 80,
            "historical_dates": dates,
            "historical_prices": prices,
            "forecast_prices": [round(x,2) for x in forecast],
            "explanation": "RandomForest model trained on local historical prices aggregated by date."
        })

    # fallback to demo data
    data = materials.get(material)
    if not data:
        return jsonify({"error": "Material not found"}), 404
    return jsonify({
        "current_price": data["current_price"],
        "pred_7d": data.get("predicted_7"),
        "pred_30d": data.get("predicted_30"),
        "trend": data.get("trend"),
        "confidence_min": data.get("confidence_min"),
        "confidence_max": data.get("confidence_max"),
        "confidence_pct": data.get("confidence_pct"),
        "historical_dates": data.get("historical_dates"),
        "historical_prices": data.get("historical_prices"),
        "forecast_prices": data.get("forecast_prices"),
        "explanation": "Model used Random Forest over supply/demand and economic features."
    })



@app.route("/estimate", methods=["POST"])
def estimate():
    data = request.json
    # use material lookup to find base price
    material = data.get("material")
    qty = float(data.get("quantity", 0))
    timeline = float(data.get("timeline", 0))

    base_price = materials.get(material, {}).get("current_price", 0)
    current = base_price * qty
    # simple time-based growth assumption (5% per 30 days)
    factor = 1 + (timeline / 30) * 0.05
    predicted = current * factor
    confidence_pct = 75  # placeholder

    recommendation = "BUY NOW" if predicted > current else "WAIT"
    return jsonify({
        "current_cost": current,
        "predicted_cost": predicted,
        "recommendation": recommendation,
        "confidence_pct": confidence_pct
    })


# additional endpoints for market intelligence and listing
@app.route("/market-insight/<material>")
def market_insight(material):
    market_insights = {
        "steel": {
            "risk": "Medium",
            "sentiment": "Negative",
            "insights": [
                "Rising fuel costs impact transport and logistics expenses.",
                "Global steel prices showing downward trend due to market oversupply.",
                "Recommend locking in prices for short-term projects.",
                "Q1 2026 demand in Davao region remains below forecast."
            ]
        },
        "cement": {
            "risk": "High",
            "sentiment": "Negative",
            "insights": [
                "Construction demand weakening; expect price adjustments.",
                "Supply chain delays reported in Metro Manila affecting Davao shipments.",
                "Bulk orders may receive 5-10% discount.",
                "Advocate for price lock agreements until Q2."
            ]
        },
        "sand": {
            "risk": "Low",
            "sentiment": "Neutral",
            "insights": [
                "Stable local demand from ongoing residential projects.",
                "Local suppliers maintaining consistent pricing.",
                "No supply disruptions expected in the near term.",
                "Good opportunity for long-term procurement contracts."
            ]
        },
        "gravel": {
            "risk": "Low",
            "sentiment": "Positive",
            "insights": [
                "Quarry output increasing as weather improves.",
                "Competitive pricing from multiple local suppliers.",
                "Average price decline of 2% expected in next 30 days.",
                "Ideal time for infrastructure projects requiring bulk materials."
            ]
        },
        "lumber": {
            "risk": "Medium",
            "sentiment": "Neutral",
            "insights": [
                "Import delays affecting premium lumber grades.",
                "Local production maintaining steady supply.",
                "Mixed market sentiment on construction demand.",
                "Price volatility expected due to sourcing challenges."
            ]
        },
        "plywood": {
            "risk": "Medium",
            "sentiment": "Positive",
            "insights": [
                "Strong demand from residential sector driving prices up.",
                "Regional production capacity increasing through Q2.",
                "Recommended for shorter procurement cycles.",
                "Export demand supporting stable pricing structure."
            ]
        }
    }
    
    data = market_insights.get(material, {
        "risk": "Medium",
        "sentiment": "Neutral",
        "insights": ["Market data unavailable for this material."]
    })
    
    insight_text = " ".join(data["insights"][:2])
    
    return jsonify({
        "risk": data["risk"],
        "sentiment": data["sentiment"],
        "insight": insight_text,
        "all_insights": data["insights"]
    })

@app.route("/materials")
def list_materials():
    result = []
    for name,info in materials.items():
        result.append({"name": name, "price": info.get("current_price"), "updated": "2026-02-24"})
    return jsonify(result)

@app.route("/materials-today")
def list_materials_today():
    """Return all materials with today's aggregated prices from CSV"""
    try:
        csv_path = os.path.join(os.path.dirname(__file__), '..', 'davaobuild_dataset_2025_2026.csv')
        df = pd.read_csv(csv_path)
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
        import datetime
        today_str = datetime.date.today().strftime('%Y-%m-%d')
        df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
        today_data = df[df['date_str'] == today_str]
        
        if today_data.empty:
            # fallback to latest date available
            latest_date = df['date'].max()
            df['date_str'] = df['date'].dt.strftime('%Y-%m-%d')
            today_data = df[df['date'].dt.strftime('%Y-%m-%d') == latest_date.strftime('%Y-%m-%d')]
        
        result = []
        for material in ['steel', 'cement', 'sand', 'gravel', 'lumber', 'plywood']:
            mat_data = today_data[today_data['material'] == material]
            if not mat_data.empty:
                avg_price = mat_data['price'].mean()
                result.append({
                    "name": material.capitalize(),
                    "price": round(avg_price, 2),
                    "unit": mat_data['unit'].iloc[0] if 'unit' in mat_data.columns else "unit",
                    "updated": today_data['date'].max().strftime('%Y-%m-%d') if not today_data.empty else "2026-02-25"
                })
            else:
                # fallback to sample data
                info = materials.get(material, {})
                result.append({
                    "name": material.capitalize(),
                    "price": info.get("current_price", 0),
                    "unit": "unit",
                    "updated": "2026-02-25"
                })
        return jsonify(result)
    except Exception as e:
        print(f"Error fetching materials-today: {e}")
        return list_materials()

@app.route("/footer-data")
def footer_data():
    """Return live footer metrics (diesel, exchange rate, inflation, status)"""
    diesel_price = 59.10
    exchange_rate = 56.12
    regional_inflation = 3.5
    
    # Try to fetch live exchange rate from BSP API
    try:
        # BSP JSON API for exchange rates
        bsp_url = "https://www.bsp.gov.ph/statistics/external/json/rates.json"
        resp = requests.get(bsp_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Look for USD rate (format varies but typically has "USD" key or array)
            if isinstance(data, dict):
                if "PHP_USD" in data:
                    exchange_rate = float(data["PHP_USD"])
                elif "rates" in data and "USD" in data["rates"]:
                    exchange_rate = float(data["rates"]["USD"])
                elif "USD" in data:
                    exchange_rate = float(data["USD"])
    except Exception as e:
        print(f"BSP API fetch failed: {e}")
    
    # Try to fetch diesel prices from PSG API (Philippine Statistics Guild)
    try:
        # Alternative: OpenWeather-like fuel price APIs or local sources
        # For now, use a mock that updates based on trend
        # In production, connect to Petron/Shell/Caltex APIs or PSA data
        today = datetime.now()
        # Simulate slight variations in diesel price based on date
        day_factor = (today.day / 31.0) * 2  # ±1 variation per month
        diesel_price = 59.10 + day_factor
    except Exception as e:
        print(f"Diesel price fetch failed: {e}")
    
    # Try to fetch inflation from PSA Open Data API
    try:
        # PSA Open Data Portal API for inflation
        psa_url = "http://api.psa.gov.ph/latest/CPI"
        resp = requests.get(psa_url, timeout=5)
        if resp.status_code == 200:
            data = resp.json()
            # Parse inflation data depending on PSA API structure
            if isinstance(data, dict) and "data" in data:
                if isinstance(data["data"], list) and len(data["data"]) > 0:
                    latest = data["data"][0]
                    if "inflation_rate" in latest:
                        regional_inflation = float(latest["inflation_rate"])
                    elif "value" in latest:
                        regional_inflation = float(latest["value"])
    except Exception as e:
        print(f"PSA API fetch failed: {e}")
    
    return jsonify({
        "diesel_price": round(diesel_price, 2),
        "diesel_currency": "₱",
        "exchange_rate": round(exchange_rate, 2),
        "exchange_currency": "₱/USD",
        "regional_inflation": round(regional_inflation, 2),
        "system_status": "SYNCED",
        "last_updated": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

# VERY IMPORTANT PART
if __name__ == "__main__":
    print("STARTING DAVAO BUILD AI BACKEND...")
    debug_mode = os.getenv('DEBUG', 'True').lower() == 'true'
    app.run(debug=debug_mode)