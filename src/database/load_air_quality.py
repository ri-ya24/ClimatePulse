import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.air_quality_api import (
    get_air_quality,
    clean_air_quality_data
)

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

print("Fetching live air quality data...")

air_data = get_air_quality()
clean_data = clean_air_quality_data(air_data)

print("Air quality data fetched:")
print(clean_data)

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

df = pd.DataFrame([clean_data])

df.to_sql(
    "live_air_quality",
    engine,
    if_exists="append",
    index=False
)

print("\nAir quality successfully stored!")
print("Table: live_air_quality")