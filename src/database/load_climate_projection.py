import sys
from pathlib import Path
import os

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv


sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.climate_projection_api import (
    get_climate_projection,
    clean_climate_projection
)


# Load environment variables
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")


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