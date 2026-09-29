import sys
from pathlib import Path

import pandas as pd
import requests
from sqlalchemy import create_engine, text

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

LATITUDE = 26.8467
LONGITUDE = 80.9462

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# GET SAVED ML PREDICTION
# --------------------------------------------------

query = """
SELECT forecast_date, predicted_temperature
FROM temperature_forecast
ORDER BY created_at DESC
LIMIT 1;
"""

ml_forecast = pd.read_sql(query, engine)

ml_date = ml_forecast["forecast_date"].iloc[0]
ml_prediction = ml_forecast["predicted_temperature"].iloc[0]


# --------------------------------------------------
# GET OPEN-METEO FORECAST
# --------------------------------------------------

url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "daily": "temperature_2m_mean",
    "forecast_days": 2,
    "timezone": "Asia/Kolkata",
}

response = requests.get(
    url,
    params=params,
    timeout=30
)

response.raise_for_status()

weather_data = response.json()

forecast_df = pd.DataFrame({
    "date": pd.to_datetime(
        weather_data["daily"]["time"]
    ),
    "temperature": (
        weather_data["daily"]["temperature_2m_mean"]
    )
})

forecast_df["date"] = forecast_df["date"].dt.date

open_meteo_prediction = forecast_df[
    forecast_df["date"] == ml_date
]["temperature"].iloc[0]


# --------------------------------------------------
# COMPARISON
# --------------------------------------------------

difference = (
    ml_prediction - open_meteo_prediction
)

absolute_difference = abs(difference)


print("\nForecast Comparison")
print("-------------------")

print(
    "Forecast date:",
    ml_date
)

print(
    "XGBoost prediction:",
    round(ml_prediction, 2),
    "°C"
)

print(
    "Open-Meteo forecast:",
    round(open_meteo_prediction, 2),
    "°C"
)

print(
    "Difference:",
    round(difference, 2),
    "°C"
)

print(
    "Absolute difference:",
    round(absolute_difference, 2),
    "°C"
)