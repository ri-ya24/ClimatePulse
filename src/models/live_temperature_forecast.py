import sys
from pathlib import Path

import pandas as pd
import requests
import joblib


# --------------------------------------------------
# PATHS
# --------------------------------------------------

BASE_DIR = Path(__file__).resolve().parents[1]

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "temperature_xgboost_model.pkl"
)


# --------------------------------------------------
# LOCATION
# --------------------------------------------------

LATITUDE = 26.8467
LONGITUDE = 80.9462


# --------------------------------------------------
# LOAD TRAINED MODEL
# --------------------------------------------------

print("Loading trained XGBoost model...")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


# --------------------------------------------------
# FETCH RECENT WEATHER DATA
# --------------------------------------------------

print("\nFetching recent weather data...")

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "past_days": 31,
    "daily": "temperature_2m_mean",
    "timezone": "Asia/Kolkata",
}

response = requests.get(
    url,
    params=params,
    timeout=30
)

response.raise_for_status()

weather_data = response.json()


# --------------------------------------------------
# CREATE DATAFRAME
# --------------------------------------------------

df = pd.DataFrame({
    "date": pd.to_datetime(
        weather_data["daily"]["time"]
    ),
    "temperature_mean": (
        weather_data["daily"]["temperature_2m_mean"]
    )
})

print("\nRecent Weather Data")
print("-------------------")
print("Rows:", len(df))
print(
    "Start date:",
    df["date"].min().date()
)
print(
    "End date:",
    df["date"].max().date()
)


# --------------------------------------------------
# CREATE ML FEATURES
# --------------------------------------------------

df["temperature_lag_1"] = (
    df["temperature_mean"].shift(1)
)

df["temperature_lag_2"] = (
    df["temperature_mean"].shift(2)
)

df["temperature_lag_7"] = (
    df["temperature_mean"].shift(7)
)

df["temperature_rolling_7"] = (
    df["temperature_mean"]
    .shift(1)
    .rolling(7)
    .mean()
)

df["temperature_rolling_30"] = (
    df["temperature_mean"]
    .shift(1)
    .rolling(30)
    .mean()
)


# --------------------------------------------------
# LATEST ROW
# --------------------------------------------------

latest = df.dropna().iloc[[-1]]

features = [
    "temperature_lag_1",
    "temperature_lag_2",
    "temperature_lag_7",
    "temperature_rolling_7",
    "temperature_rolling_30"
]

X_live = latest[features]


print("\nLatest ML Features")
print("------------------")
print(X_live.to_string(index=False))
# --------------------------------------------------
# LIVE TEMPERATURE PREDICTION
# --------------------------------------------------

print("\nGenerating live temperature prediction...")
print("-----------------------------------------")

prediction = model.predict(X_live)[0]

print(
    "Predicted next-day temperature:",
    round(prediction, 2),
    "°C"
)