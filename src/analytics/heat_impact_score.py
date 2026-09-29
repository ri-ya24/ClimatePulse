import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)

# Latest live temperature
live_query = """
SELECT *
FROM live_weather
ORDER BY time DESC
LIMIT 1;
"""

live_df = pd.read_sql(live_query, engine)

# Historical weather
historical_query = """
SELECT date, temperature_mean
FROM historical_weather;
"""

historical_df = pd.read_sql(historical_query, engine)

historical_df["date"] = pd.to_datetime(historical_df["date"])
live_df["time"] = pd.to_datetime(live_df["time"])

# Create historical daily temperature baseline
historical_df["month"] = historical_df["date"].dt.month
historical_df["day"] = historical_df["date"].dt.day

baseline = (
    historical_df
    .groupby(["month", "day"])["temperature_mean"]
    .mean()
    .reset_index()
    .rename(columns={
        "temperature_mean": "historical_mean_temperature"
    })
)

# Current date
live_month = live_df["time"].dt.month.iloc[0]
live_day = live_df["time"].dt.day.iloc[0]

# Historical normal for today
today_baseline = baseline[
    (baseline["month"] == live_month) &
    (baseline["day"] == live_day)
]["historical_mean_temperature"].iloc[0]

# Current temperature
current_temperature = live_df["temperature"].iloc[0]

# Temperature anomaly
temperature_anomaly = current_temperature - today_baseline

# Project-defined heat impact score
# 0°C anomaly = 0 impact
# +5°C anomaly or higher = 100 impact

heat_score = min(max((temperature_anomaly / 5) * 100, 0), 100)

print("\nClimatePulse Heat Impact")
print("------------------------")
print("Current temperature:", current_temperature, "°C")
print("Historical normal:", round(today_baseline, 2), "°C")
print("Temperature anomaly:", round(temperature_anomaly, 2), "°C")

print("\nHeat Impact Score")
print("-----------------")
print(round(heat_score, 2), "/ 100")