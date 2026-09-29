import pandas as pd
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression


DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

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

historical["date"] = pd.to_datetime(
    historical["date"]
)

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
    temperature_mean
FROM climate_projection
ORDER BY date;
"""

future = pd.read_sql(
    future_query,
    engine
)

future["date"] = pd.to_datetime(
    future["date"]
)

future["year"] = future["date"].dt.year


future_annual = (
    future
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
# COMBINE
# --------------------------------------------------

historical_annual["period"] = "Historical"
future_annual["period"] = "Projected"

comparison = pd.concat(
    [
        historical_annual,
        future_annual
    ],
    ignore_index=True
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

historical_trend = (
    hist_model.coef_[0] * 10
)


# --------------------------------------------------
# FUTURE TREND
# --------------------------------------------------

X_future = future_annual[["year"]]
y_future = future_annual["mean_temperature"]

future_model = LinearRegression()

future_model.fit(
    X_future,
    y_future
)

future_trend = (
    future_model.coef_[0] * 10
)


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


print("\nHistorical average temperature:")
print(
    round(historical_average, 2),
    "°C"
)

print("\nProjected average temperature:")
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

print("\nProjected trend:")
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


print("\nProjected temperature range:")
print(
    round(
        future_annual["mean_temperature"].min(),
        2
    ),
    "to",
    round(
        future_annual["mean_temperature"].max(),
        2
    ),
    "°C"
)