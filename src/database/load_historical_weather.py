import sys
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.historical_weather_api import (
    get_historical_weather,
    clean_historical_weather
)


# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")


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