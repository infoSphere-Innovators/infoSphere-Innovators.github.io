import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.model_selection import train_test_split
from joblib import dump

DATA_PATH = os.path.join(os.path.dirname(__file__), '..', 'davaobuild_dataset_2025_2026.csv')
MODELS_DIR = os.path.join(os.path.dirname(__file__), 'models')

os.makedirs(MODELS_DIR, exist_ok=True)

def prepare_series(df):
    df['date'] = pd.to_datetime(df['date'], dayfirst=True, errors='coerce')
    df = df.sort_values('date')
    series = df.groupby('date')['price'].mean().reset_index()
    series = series.set_index('date')
    return series

def featurize(series, lags=7):
    df = series.copy()
    for i in range(1, lags+1):
        df[f'lag_{i}'] = df['price'].shift(i)
    df = df.dropna()
    return df

def train_for_material(df_all, material):
    df = df_all[df_all['material'] == material][['date','price']].copy()
    if df.empty:
        print(f'No data for {material}')
        return None
    series = prepare_series(df)
    feat = featurize(series, lags=7)
    X = feat[[f'lag_{i}' for i in range(1,8)]].values
    y = feat['price'].values
    if len(X) < 50:
        print(f'Not enough samples to train for {material} (need >=50, have {len(X)})')
        return None
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X_train, y_train)
    print(f'Trained model for {material}, test score: {model.score(X_test,y_test):.3f}')
    return model

def iterative_forecast(model, recent_prices, steps=30):
    preds = []
    window = recent_prices[-7:].copy()
    for _ in range(steps):
        x = np.array(window[-7:]).reshape(1, -1)
        p = float(model.predict(x)[0])
        preds.append(p)
        window.append(p)
    return preds

def main():
    print('Loading dataset:', DATA_PATH)
    df = pd.read_csv(DATA_PATH)
    materials = df['material'].unique()
    saved = []
    for m in materials:
        model = train_for_material(df, m)
        if model is None:
            continue
        path = os.path.join(MODELS_DIR, f'{m}.joblib')
        dump(model, path)
        print('Saved', path)
        saved.append(m)
    print('Completed. Models saved for:', saved)

if __name__ == '__main__':
    main()
