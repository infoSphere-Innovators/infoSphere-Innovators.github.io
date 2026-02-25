import os
import pandas as pd
from joblib import dump

DATA_CSV = os.path.join(os.path.dirname(__file__), '..', 'davaobuild_dataset_2025_2026.csv')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')
os.makedirs(MODELS_DIR, exist_ok=True)

def prepare_series(df, material):
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    s = df[df['material'] == material].groupby('date')['price'].mean().reset_index().sort_values('date')
    s = s.rename(columns={'date':'ds','price':'y'})
    return s

def train_prophet(df, material):
    try:
        from prophet import Prophet
    except Exception as e:
        print('Prophet not available:', e)
        return None
    s = prepare_series(df, material)
    if len(s) < 10:
        print('Not enough data for prophet for', material)
        return None
    m = Prophet(yearly_seasonality=True, weekly_seasonality=False, daily_seasonality=False)
    m.fit(s)
    out_path = os.path.join(MODELS_DIR, f'prophet_{material}.joblib')
    dump(m, out_path)
    print('Saved', out_path)
    return out_path

def train_arima(df, material):
    try:
        from statsmodels.tsa.statespace.sarimax import SARIMAX
    except Exception as e:
        print('statsmodels not available:', e)
        return None
    s = prepare_series(df, material)
    if len(s) < 10:
        print('Not enough data for ARIMA for', material)
        return None
    y = s['y'].astype(float).values
    # simple SARIMAX(1,1,1)
    model = SARIMAX(y, order=(1,1,1), seasonal_order=(0,0,0,0), enforce_stationarity=False, enforce_invertibility=False)
    res = model.fit(disp=False)
    out_path = os.path.join(MODELS_DIR, f'arima_{material}.joblib')
    dump(res, out_path)
    print('Saved', out_path)
    return out_path

def main():
    print('Loading dataset:', DATA_CSV)
    df = pd.read_csv(DATA_CSV)
    materials = df['material'].unique().tolist()
    trained = []
    for m in materials:
        print('Training for', m)
        p = train_prophet(df, m)
        a = train_arima(df, m)
        if p or a:
            trained.append(m)
    print('Completed. Models saved for:', trained)

if __name__ == '__main__':
    main()
