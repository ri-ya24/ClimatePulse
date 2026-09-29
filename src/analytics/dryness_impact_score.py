import sys
from pathlib import Path
import requests
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

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

# Fetch current month's rainfall
url = "https://api.open-meteo.com/v1/forecast"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": start_date,
    "end_date": end_date,
    "daily": "precipitation_sum",
    "timezone": "Asia/Kolkata",
}

response = requests.get(
    url,
    params=params,
    timeout=60
)

response.raise_for_status()

weather_data = response.json()

current_df = pd.DataFrame({
    "date": pd.to_datetime(weather_data["daily"]["time"]),
    "precipitation": weather_data["daily"]["precipitation_sum"]
})

current_df["precipitation"] = (
    current_df["precipitation"].fillna(0)
)

# Identify dry days
current_df["dry_day"] = (
    current_df["precipitation"] < 1.0
)

# Identify consecutive dry periods
current_df["dry_group"] = (
    current_df["dry_day"]
    .ne(current_df["dry_day"].shift())
    .cumsum()
)

dry_spells = (
    current_df[current_df["dry_day"]]
    .groupby("dry_group")
    .agg(
        start_date=("date", "min"),
        end_date=("date", "max"),
        duration_days=("date", "count")
    )
    .reset_index(drop=True)
)

# Current consecutive dry spell
current_dry_days = 0

if len(dry_spells) > 0:

    latest_spell = dry_spells.iloc[-1]

    if latest_spell["end_date"].date() == today.date():
        current_dry_days = int(
            latest_spell["duration_days"]
        )

# Project-defined dryness score
# 0 dry days = 0 impact
# 30+ consecutive dry days = 100 impact

dryness_score = min(
    (current_dry_days / 30) * 100,
    100
)

print("\nClimatePulse Dryness Impact")
print("---------------------------")

print(
    "Period:",
    f"{start_date} to {end_date}"
)

print(
    "Current consecutive dry days:",
    current_dry_days
)

print("\nDryness Impact Score")
print("--------------------")

print(
    round(dryness_score, 2),
    "/ 100"
)