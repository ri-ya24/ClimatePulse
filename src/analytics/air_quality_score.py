import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)

query = """
SELECT *
FROM live_air_quality
ORDER BY time DESC
LIMIT 1;
"""

df = pd.read_sql(query, engine)

# Get latest values
pm25 = df["pm2_5"].iloc[0]
pm10 = df["pm10"].iloc[0]
no2 = df["nitrogen_dioxide"].iloc[0]
so2 = df["sulphur_dioxide"].iloc[0]
o3 = df["ozone"].iloc[0]

# Project-defined normalization
# Values represent approximate concentration ranges
# used only for ClimatePulse's internal impact score.

pm25_score = min((pm25 / 75) * 100, 100)
pm10_score = min((pm10 / 150) * 100, 100)
no2_score = min((no2 / 80) * 100, 100)
so2_score = min((so2 / 80) * 100, 100)
o3_score = min((o3 / 180) * 100, 100)

# Weighted air-quality impact score
air_quality_score = (
    pm25_score * 0.35 +
    pm10_score * 0.25 +
    no2_score * 0.15 +
    so2_score * 0.10 +
    o3_score * 0.15
)

print("\nClimatePulse Air Quality Impact")
print("--------------------------------")
print("PM2.5:", pm25)
print("PM10:", pm10)
print("NO2:", no2)
print("SO2:", so2)
print("O3:", o3)

print("\nComponent Scores")
print("----------------")
print("PM2.5 score:", round(pm25_score, 2))
print("PM10 score:", round(pm10_score, 2))
print("NO2 score:", round(no2_score, 2))
print("SO2 score:", round(so2_score, 2))
print("O3 score:", round(o3_score, 2))

print("\nAir Quality Impact Score")
print("------------------------")
print(round(air_quality_score, 2), "/ 100")