import sys
from pathlib import Path

from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.weather_api import (
    get_current_weather,
    clean_weather_data
)

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

print("Fetching live weather data...")

weather_data = get_current_weather()
clean_data = clean_weather_data(weather_data)

print("Live data fetched:")
print(clean_data)

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

import pandas as pd

df = pd.DataFrame([clean_data])

df.to_sql(
    "live_weather",
    engine,
    if_exists="append",
    index=False
)

print("\nLive weather successfully stored!")
print("Table: live_weather")