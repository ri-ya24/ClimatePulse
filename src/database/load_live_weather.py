import sys
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.weather_api import (
    get_current_weather,
    clean_weather_data
)


# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")


print("Fetching live weather data...")

weather_data = get_current_weather()
clean_data = clean_weather_data(weather_data)

print("Live data fetched:")
print(clean_data)

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

df = pd.DataFrame([clean_data])

df.to_sql(
    "live_weather",
    engine,
    if_exists="append",
    index=False
)

print("\nLive weather successfully stored!")
print("Table: live_weather")