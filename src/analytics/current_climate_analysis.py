import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)

# Get latest live weather
live_query = """
SELECT *
FROM live_weather
ORDER BY time DESC
LIMIT 1;
"""

live_df = pd.read_sql(live_query, engine)

# Historical weather
historical_query = """
SELECT date, temperature_mean, precipitation
FROM historical_weather;
"""

historical_df = pd.read_sql(historical_query, engine)

historical_df["date"] = pd.to_datetime(historical_df["date"])
live_df["time"] = pd.to_datetime(live_df["time"])

# Create historical daily baseline
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

# Get today's month and day
live_month = live_df["time"].dt.month.iloc[0]
live_day = live_df["time"].dt.day.iloc[0]

# Find historical normal for today
today_baseline = baseline[
    (baseline["month"] == live_month) &
    (baseline["day"] == live_day)
]["historical_mean_temperature"].iloc[0]

# Calculate anomaly
current_temperature = live_df["temperature"].iloc[0]

temperature_anomaly = current_temperature - today_baseline

print("\nCurrent Climate Analysis")
print("------------------------")
print("Current temperature:", current_temperature, "°C")
print("Historical normal:", round(today_baseline, 2), "°C")
print("Temperature anomaly:", round(temperature_anomaly, 2), "°C")
# Historical rainfall baseline
rainfall_baseline = (
    historical_df
    .groupby(["month", "day"])["precipitation"]
    .mean()
    .reset_index()
    .rename(columns={
        "precipitation": "historical_mean_rainfall"
    })
)

# Historical normal rainfall for today
today_rainfall_baseline = rainfall_baseline[
    (rainfall_baseline["month"] == live_month) &
    (rainfall_baseline["day"] == live_day)
]["historical_mean_rainfall"].iloc[0]

# Current rainfall
current_rainfall = live_df["precipitation"].iloc[0]

# Calculate rainfall anomaly
rainfall_anomaly = current_rainfall - today_rainfall_baseline

# Calculate percentage anomaly
if today_rainfall_baseline > 0:
    rainfall_anomaly_percent = (
        rainfall_anomaly / today_rainfall_baseline
    ) * 100
else:
    rainfall_anomaly_percent = None

print("\nRainfall Analysis")
print("-----------------")
print("Current rainfall:", current_rainfall, "mm")
print(
    "Historical normal rainfall:",
    round(today_rainfall_baseline, 2),
    "mm"
)
print(
    "Rainfall anomaly:",
    round(rainfall_anomaly, 2),
    "mm"
)

if rainfall_anomaly_percent is not None:
    print(
        "Rainfall anomaly percentage:",
        round(rainfall_anomaly_percent, 2),
        "%"
    )
else:
    print("Rainfall anomaly percentage: Not available")