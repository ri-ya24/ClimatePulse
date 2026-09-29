import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# FORECAST DATA
# --------------------------------------------------

forecast_date = pd.Timestamp.now().normalize() + pd.Timedelta(days=1)

predicted_temperature = 27.28


# --------------------------------------------------
# CREATE TABLE
# --------------------------------------------------

create_table_query = """
CREATE TABLE IF NOT EXISTS temperature_forecast (
    id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    predicted_temperature DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as connection:
    connection.execute(
        text(create_table_query)
    )


# --------------------------------------------------
# SAVE FORECAST
# --------------------------------------------------

insert_query = """
INSERT INTO temperature_forecast (
    forecast_date,
    predicted_temperature
)
VALUES (
    :forecast_date,
    :predicted_temperature
);
"""

with engine.begin() as connection:
    connection.execute(
        text(insert_query),
        {
            "forecast_date": forecast_date.date(),
            "predicted_temperature": predicted_temperature
        }
    )


print("\nTemperature Forecast Saved")
print("--------------------------")
print(
    "Forecast date:",
    forecast_date.date()
)
print(
    "Predicted temperature:",
    predicted_temperature,
    "Â°C"
)
import os
import sys
from pathlib import Path

import pandas as pd
import requests
import joblib
from sqlalchemy import create_engine, text


# --------------------------------------------------
# PATHS
# --------------------------------------------------

MODEL_PATH = (
    Path(__file__).resolve().parents[1]
    / "models"
    / "temperature_xgboost_model.pkl"
)


# --------------------------------------------------
# LOCATION
# --------------------------------------------------

LATITUDE = 26.8467
LONGITUDE = 80.9462


# --------------------------------------------------
# DATABASE
# --------------------------------------------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# LOAD MODEL
# --------------------------------------------------

print("Loading XGBoost model...")

model = joblib.load(MODEL_PATH)

print("Model loaded successfully!")


# --------------------------------------------------
# FETCH RECENT WEATHER
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


# --------------------------------------------------
# CREATE FEATURES
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
# GET LATEST FEATURES
# --------------------------------------------------

features = [
    "temperature_lag_1",
    "temperature_lag_2",
    "temperature_lag_7",
    "temperature_rolling_7",
    "temperature_rolling_30"
]

today = pd.Timestamp.now().normalize()

df = df[
    df["date"] <= today
].copy()

latest = df.dropna().iloc[[-1]]

X_live = latest[features]


# --------------------------------------------------
# PREDICT
# --------------------------------------------------

predicted_temperature = model.predict(
    X_live
)[0]

forecast_date = (
    latest["date"].iloc[0]
    + pd.Timedelta(days=1)
)


print("\nLive Temperature Forecast")
print("-------------------------")

print(
    "Forecast date:",
    forecast_date.date()
)

print(
    "Predicted temperature:",
    round(predicted_temperature, 2),
    "Â°C"
)


# --------------------------------------------------
# CREATE TABLE
# --------------------------------------------------

create_table_query = """
CREATE TABLE IF NOT EXISTS temperature_forecast (
    id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    predicted_temperature DOUBLE PRECISION NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as connection:
    connection.execute(
        text(create_table_query)
    )


# --------------------------------------------------
# SAVE FORECAST
# --------------------------------------------------

insert_query = """
INSERT INTO temperature_forecast (
    forecast_date,
    predicted_temperature
)
VALUES (
    :forecast_date,
    :predicted_temperature
);
"""

with engine.begin() as connection:
    connection.execute(
        text(insert_query),
        {
            "forecast_date": forecast_date.date(),
            "predicted_temperature": float(
                predicted_temperature
            )
        }
    )


print("\nForecast saved to PostgreSQL successfully!")
