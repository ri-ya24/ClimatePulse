import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.historical_weather_api import (
    get_historical_weather,
    clean_historical_weather
)

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

print("Fetching historical weather data...")

weather_data = get_historical_weather(
    "1990-01-01",
    "2025-12-31"
)

df = clean_historical_weather(weather_data)

print("Rows fetched:", len(df))

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

df.to_sql(
    "historical_weather",
    engine,
    if_exists="replace",
    index=False
)

print("\nData successfully stored in PostgreSQL!")
print("Table: historical_weather")
print("Rows:", len(df))