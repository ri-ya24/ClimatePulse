import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.climate_projection_api import (
    get_climate_projection,
    clean_climate_projection
)

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

print("Fetching future climate projection...")

climate_data = get_climate_projection()
df = clean_climate_projection(climate_data)

print("Rows fetched:", len(df))

print("\nConnecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

df.to_sql(
    "climate_projection",
    engine,
    if_exists="replace",
    index=False
)

print("\nClimate projection successfully stored!")
print("Table: climate_projection")
print("Rows:", len(df))