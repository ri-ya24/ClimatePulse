import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from sklearn.linear_model import LinearRegression

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# LOAD CLIMATE PROJECTIONS
# --------------------------------------------------

query = """
SELECT
    date,
    temperature_mean,
    temperature_max,
    temperature_min,
    precipitation
FROM climate_projection
ORDER BY date;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])


# --------------------------------------------------
# YEARLY AGGREGATION
# --------------------------------------------------

df["year"] = df["date"].dt.year

annual_projection = (
    df.groupby("year")
    .agg(
        mean_temperature=("temperature_mean", "mean"),
        max_temperature=("temperature_max", "mean"),
        min_temperature=("temperature_min", "mean"),
        annual_precipitation=("precipitation", "sum")
    )
    .reset_index()
)


# --------------------------------------------------
# TEMPERATURE TREND
# --------------------------------------------------

X = annual_projection[["year"]]

y = annual_projection[
    "mean_temperature"
]

model = LinearRegression()

model.fit(X, y)

trend_per_year = model.coef_[0]

trend_per_decade = (
    trend_per_year * 10
)


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