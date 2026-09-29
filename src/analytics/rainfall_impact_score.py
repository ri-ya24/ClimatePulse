import os
import sys
from pathlib import Path
import requests
import pandas as pd
from sqlalchemy import create_engine

from dotenv import load_dotenv
sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
LATITUDE = 26.8467
LONGITUDE = 80.9462

engine = create_engine(DATABASE_URL)

# Current date
today = pd.Timestamp.now().normalize()

current_year = today.year
current_month = today.month
current_day = today.day

start_date = f"{current_year}-{current_month:02d}-01"
end_date = today.strftime("%Y-%m-%d")

# Fetch current year's daily rainfall
url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": start_date,
    "end_date": end_date,
    "daily": "precipitation_sum",
    "timezone": "Asia/Kolkata",
}

response = requests.get(url, params=params, timeout=30)
response.raise_for_status()

weather_data = response.json()

current_rainfall = sum(
    value or 0
    for value in weather_data["daily"]["precipitation_sum"]
)

# Historical rainfall
query = """
SELECT date, precipitation
FROM historical_weather
ORDER BY date;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])

# Historical same-period rainfall
historical_period = df[
    (df["date"].dt.year < current_year) &
    (df["date"].dt.month == current_month) &
    (df["date"].dt.day <= current_day)
]

historical_yearly_totals = (
    historical_period
    .groupby(historical_period["date"].dt.year)["precipitation"]
    .sum()
)

historical_normal = historical_yearly_totals.mean()

# Rainfall anomaly
rainfall_difference = current_rainfall - historical_normal

rainfall_anomaly_percent = (
    rainfall_difference / historical_normal
) * 100

# Project-defined impact score
rainfall_impact_score = min(
    abs(rainfall_anomaly_percent),
    100
)

print("\nClimatePulse Rainfall Impact")
print("----------------------------")
print(
    "Period:",
    f"{start_date} to {end_date}"
)

print(
    "Current rainfall:",
    round(current_rainfall, 2),
    "mm"
)

print(
    "Historical normal for same period:",
    round(historical_normal, 2),
    "mm"
)

print("\nRainfall Anomaly")
print("----------------")
print(
    "Difference:",
    round(rainfall_difference, 2),
    "mm"
)

print(
    "Anomaly:",
    round(rainfall_anomaly_percent, 2),
    "%"
)

print("\nRainfall Impact Score")
print("--------------------")
print(
    round(rainfall_impact_score, 2),
    "/ 100"
)
