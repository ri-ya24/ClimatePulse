import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression

sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# LOAD CLIMATE PROJECTIONS
# --------------------------------------------------

query = """
SELECT
    date,
    model,
    temperature_mean,
    temperature_max,
    temperature_min,
    precipitation
FROM climate_projection
ORDER BY date, model;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])


# --------------------------------------------------
# YEARLY MODEL-LEVEL AGGREGATION
# --------------------------------------------------

df["year"] = df["date"].dt.year

annual_model_projection = (
    df.groupby(["year", "model"])
    .agg(
        mean_temperature=("temperature_mean", "mean"),
        max_temperature=("temperature_max", "mean"),
        min_temperature=("temperature_min", "mean"),
        annual_precipitation=("precipitation", "sum")
    )
    .reset_index()
)


# --------------------------------------------------
# MULTI-MODEL ENSEMBLE
# --------------------------------------------------

annual_projection = (
    annual_model_projection
    .groupby("year")
    .agg(
        mean_temperature=("mean_temperature", "mean"),
        min_temperature=("mean_temperature", "min"),
        max_temperature=("mean_temperature", "max"),
        annual_precipitation=("annual_precipitation", "mean"),
        min_precipitation=("annual_precipitation", "min"),
        max_precipitation=("annual_precipitation", "max")
    )
    .reset_index()
)


# --------------------------------------------------
# MODEL UNCERTAINTY / SPREAD
# --------------------------------------------------

annual_projection["temperature_range"] = (
    annual_projection["max_temperature"]
    - annual_projection["min_temperature"]
)

annual_projection["precipitation_range"] = (
    annual_projection["max_precipitation"]
    - annual_projection["min_precipitation"]
)


# --------------------------------------------------
# TEMPERATURE TREND
# --------------------------------------------------

X = annual_projection[["year"]]

y = annual_projection["mean_temperature"]

model = LinearRegression()

model.fit(X, y)

trend_per_year = model.coef_[0]

trend_per_decade = trend_per_year * 10


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

print("\nFuture Climate Projection")
print("-------------------------")

print(
    "Projection period:",
    annual_projection["year"].min(),
    "to",
    annual_projection["year"].max()
)

print(
    "Projection years:",
    len(annual_projection)
)

print(
    "Climate models:",
    df["model"].nunique()
)

print("\nModels:")
print(
    df["model"]
    .drop_duplicates()
    .sort_values()
    .to_string(index=False)
)


print("\nFirst 5 years:")
print(
    annual_projection.head()
    .to_string(index=False)
)

print("\nLast 5 years:")
print(
    annual_projection.tail()
    .to_string(index=False)
)


# --------------------------------------------------
# UNCERTAINTY SUMMARY
# --------------------------------------------------

print("\nModel Uncertainty")
print("-----------------")

print(
    "Average annual temperature range:",
    round(
        annual_projection["temperature_range"].mean(),
        2
    ),
    "°C"
)

print(
    "Maximum annual temperature range:",
    round(
        annual_projection["temperature_range"].max(),
        2
    ),
    "°C"
)

print(
    "Average annual precipitation range:",
    round(
        annual_projection["precipitation_range"].mean(),
        2
    ),
    "mm"
)


# --------------------------------------------------
# PROJECTED TEMPERATURE TREND
# --------------------------------------------------

print("\nProjected Temperature Trend")
print("---------------------------")

print(
    "Trend:",
    round(trend_per_year, 4),
    "°C per year"
)

print(
    "Trend:",
    round(trend_per_decade, 4),
    "°C per decade"
)