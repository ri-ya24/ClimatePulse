import os
import pandas as pd
from sqlalchemy import create_engine

from dotenv import load_dotenv
from sklearn.linear_model import LinearRegression


load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# HISTORICAL DATA
# --------------------------------------------------

historical_query = """
SELECT
    date,
    temperature_mean
FROM historical_weather
ORDER BY date;
"""

historical = pd.read_sql(
    historical_query,
    engine
)

historical["date"] = pd.to_datetime(historical["date"])
historical["year"] = historical["date"].dt.year


historical_annual = (
    historical
    .groupby("year")["temperature_mean"]
    .mean()
    .reset_index()
    .rename(
        columns={
            "temperature_mean": "mean_temperature"
        }
    )
)


# --------------------------------------------------
# FUTURE PROJECTION DATA
# --------------------------------------------------

future_query = """
SELECT
    date,
    model,
    temperature_mean
FROM climate_projection
ORDER BY date, model;
"""

future = pd.read_sql(
    future_query,
    engine
)

future["date"] = pd.to_datetime(future["date"])
future["year"] = future["date"].dt.year


# --------------------------------------------------
# MODEL-LEVEL YEARLY AGGREGATION
# --------------------------------------------------

future_model_annual = (
    future
    .groupby(["year", "model"])["temperature_mean"]
    .mean()
    .reset_index()
)


# --------------------------------------------------
# MULTI-MODEL ENSEMBLE
# --------------------------------------------------

future_annual = (
    future_model_annual
    .groupby("year")
    .agg(
        mean_temperature=("temperature_mean", "mean"),
        min_temperature=("temperature_mean", "min"),
        max_temperature=("temperature_mean", "max")
    )
    .reset_index()
)


future_annual["temperature_range"] = (
    future_annual["max_temperature"]
    - future_annual["min_temperature"]
)


# --------------------------------------------------
# HISTORICAL TREND
# --------------------------------------------------

X_hist = historical_annual[["year"]]
y_hist = historical_annual["mean_temperature"]

hist_model = LinearRegression()

hist_model.fit(
    X_hist,
    y_hist
)

historical_trend = hist_model.coef_[0] * 10


# --------------------------------------------------
# FUTURE ENSEMBLE TREND
# --------------------------------------------------

X_future = future_annual[["year"]]
y_future = future_annual["mean_temperature"]

future_model = LinearRegression()

future_model.fit(
    X_future,
    y_future
)

future_trend = future_model.coef_[0] * 10


# --------------------------------------------------
# TEMPERATURE CHANGE
# --------------------------------------------------

historical_average = (
    historical_annual["mean_temperature"]
    .mean()
)

future_average = (
    future_annual["mean_temperature"]
    .mean()
)

average_difference = (
    future_average - historical_average
)


# --------------------------------------------------
# MODEL UNCERTAINTY
# --------------------------------------------------

average_model_range = (
    future_annual["temperature_range"]
    .mean()
)

maximum_model_range = (
    future_annual["temperature_range"]
    .max()
)


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

print("\nHistorical vs Future Climate")
print("----------------------------")

print(
    "Historical period:",
    historical_annual["year"].min(),
    "to",
    historical_annual["year"].max()
)

print(
    "Projected period:",
    future_annual["year"].min(),
    "to",
    future_annual["year"].max()
)

print(
    "Climate models:",
    future["model"].nunique()
)


print("\nHistorical average temperature:")
print(
    round(historical_average, 2),
    "°C"
)


print("\nProjected ensemble average temperature:")
print(
    round(future_average, 2),
    "°C"
)


print("\nAverage difference:")
print(
    round(average_difference, 2),
    "°C"
)


print("\nHistorical trend:")
print(
    round(historical_trend, 4),
    "°C per decade"
)


print("\nProjected ensemble trend:")
print(
    round(future_trend, 4),
    "°C per decade"
)


print("\nHistorical temperature range:")
print(
    round(
        historical_annual["mean_temperature"].min(),
        2
    ),
    "to",
    round(
        historical_annual["mean_temperature"].max(),
        2
    ),
    "°C"
)


print("\nProjected ensemble temperature range:")
print(
    round(
        future_annual["min_temperature"].min(),
        2
    ),
    "to",
    round(
        future_annual["max_temperature"].max(),
        2
    ),
    "°C"
)


print("\nModel Uncertainty:")
print(
    "Average annual model range:",
    round(average_model_range, 2),
    "°C"
)

print(
    "Maximum annual model range:",
    round(maximum_model_range, 2),
    "°C"
)


print("\nFirst 5 projected years:")
print(
    future_annual.head().to_string(index=False)
)


print("\nLast 5 projected years:")
print(
    future_annual.tail().to_string(index=False)
)