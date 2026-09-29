import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

from dotenv import load_dotenv
sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
print("Connecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

query = """
SELECT *
FROM historical_weather
ORDER BY date;
"""

df = pd.read_sql(query, engine)

print("\nHistorical Weather Data")
print("----------------------")
print("Rows:", len(df))
print("Columns:", list(df.columns))
print("Start date:", df["date"].min().date())
print("End date:", df["date"].max().date())

print("\nFirst 5 rows:")
print(df.head())

print("\nMissing values:")
print(df.isna().sum())
print("\nCalculating historical temperature baseline...")

df["month"] = df["date"].dt.month
df["day"] = df["date"].dt.day

daily_baseline = (
    df.groupby(["month", "day"])["temperature_mean"]
    .mean()
    .reset_index()
    .rename(columns={"temperature_mean": "historical_mean_temperature"})
)

print("\nHistorical baseline created!")
print("Baseline rows:", len(daily_baseline))

print("\nSample baseline:")
print(daily_baseline.head(10))
# Calculate historical baseline for each date
df["historical_mean_temperature"] = df.apply(
    lambda row: daily_baseline[
        (daily_baseline["month"] == row["month"]) &
        (daily_baseline["day"] == row["day"])
    ]["historical_mean_temperature"].iloc[0],
    axis=1
)

# Calculate temperature anomaly
df["temperature_anomaly"] = (
    df["temperature_mean"] - df["historical_mean_temperature"]
)

print("\nTemperature Anomaly Sample")
print("--------------------------")
print(
    df[
        [
            "date",
            "temperature_mean",
            "historical_mean_temperature",
            "temperature_anomaly"
        ]
    ].tail(10)
)
# Calculate standardized temperature anomaly (Z-score)

mean_anomaly = df["temperature_anomaly"].mean()
std_anomaly = df["temperature_anomaly"].std()

df["temperature_anomaly_zscore"] = (
    (df["temperature_anomaly"] - mean_anomaly)
    / std_anomaly
)

print("\nStandardized Temperature Anomaly")
print("-------------------------------")

print(
    df[
        [
            "date",
            "temperature_anomaly",
            "temperature_anomaly_zscore"
        ]
    ].tail(10)
)
# Detect extreme heat days using the 95th percentile

heat_threshold = df["temperature_mean"].quantile(0.95)

df["extreme_heat_day"] = (
    df["temperature_mean"] > heat_threshold
)

print("\nExtreme Heat Analysis")
print("---------------------")
print("95th percentile threshold:",
      round(heat_threshold, 2), "Â°C")

print("Extreme heat days:",
      df["extreme_heat_day"].sum())
# Identify consecutive extreme heat events

df["heat_group"] = (
    df["extreme_heat_day"]
    .ne(df["extreme_heat_day"].shift())
    .cumsum()
)

heat_events = (
    df[df["extreme_heat_day"]]
    .groupby("heat_group")
    .agg(
        start_date=("date", "min"),
        end_date=("date", "max"),
        duration_days=("date", "count"),
        max_temperature=("temperature_mean", "max")
    )
    .reset_index(drop=True)
)

# Keep only events lasting 3 or more consecutive days
heat_events = heat_events[
    heat_events["duration_days"] >= 3
]

print("\nExtreme Heat Events (3+ consecutive days)")
print("------------------------------------------")
print("Number of heat events:", len(heat_events))

print("\nTop heat events:")
print(
    heat_events
    .sort_values("max_temperature", ascending=False)
    .head(10)
    .to_string(index=False)
)
# Annual rainfall analysis

df["year"] = df["date"].dt.year

annual_rainfall = (
    df.groupby("year")["precipitation"]
    .sum()
    .reset_index()
    .rename(columns={
        "precipitation": "annual_rainfall"
    })
)

print("\nAnnual Rainfall Analysis")
print("-----------------------")
print("Average annual rainfall:",
      round(annual_rainfall["annual_rainfall"].mean(), 2), "mm")

print("\nFirst 5 years:")
print(annual_rainfall.head())

print("\nLast 5 years:")
print(annual_rainfall.tail())
# Long-term annual rainfall trend

from sklearn.linear_model import LinearRegression

X_rain = annual_rainfall[["year"]]
y_rain = annual_rainfall["annual_rainfall"]

rain_model = LinearRegression()
rain_model.fit(X_rain, y_rain)

rain_trend_per_year = rain_model.coef_[0]
rain_trend_per_decade = rain_trend_per_year * 10

print("\nRainfall Trend")
print("--------------")
print(
    "Trend:",
    round(rain_trend_per_year, 2),
    "mm per year"
)
print(
    "Trend:",
    round(rain_trend_per_decade, 2),
    "mm per decade"
)
# Detect dry spells

df["dry_day"] = df["precipitation"] < 1.0

df["dry_group"] = (
    df["dry_day"]
    .ne(df["dry_day"].shift())
    .cumsum()
)

dry_spells = (
    df[df["dry_day"]]
    .groupby("dry_group")
    .agg(
        start_date=("date", "min"),
        end_date=("date", "max"),
        duration_days=("date", "count")
    )
    .reset_index(drop=True)
)

# Keep dry spells lasting 5 or more days
dry_spells = dry_spells[
    dry_spells["duration_days"] >= 5
]

print("\nDry Spell Analysis")
print("------------------")
print("Dry spells (5+ days):", len(dry_spells))

print("\nLongest dry spells:")
print(
    dry_spells
    .sort_values("duration_days", ascending=False)
    .head(10)
    .to_string(index=False)
)
