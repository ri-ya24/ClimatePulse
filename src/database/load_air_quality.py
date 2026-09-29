import sys
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


# Allow imports from src/
sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.air_quality_api import (
    get_air_quality,
    clean_air_quality_data
)


# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")


# Create database engine
engine = create_engine(DATABASE_URL)


print("Fetching live air quality data...")

air_data = get_air_quality()

clean_data = clean_air_quality_data(air_data)

print("Air quality data fetched:")
print(clean_data)


print("\nConnecting to PostgreSQL...")

df = pd.DataFrame([clean_data])

df.to_sql(
    "live_air_quality",
    engine,
    if_exists="append",
    index=False
)


print("\nAir quality successfully stored.")
print("Table: live_air_quality")