import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

print("Connecting to PostgreSQL...")

engine = create_engine(DATABASE_URL)

query = """
SELECT date, temperature_mean
FROM historical_weather
ORDER BY date;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])

# Extract year
df["year"] = df["date"].dt.year

# Calculate annual average temperature
annual_temperature = (
    df.groupby("year")["temperature_mean"]
    .mean()
    .reset_index()
    .rename(columns={
        "temperature_mean": "annual_mean_temperature"
    })
)

print("\nAnnual Climate Trend")
print("--------------------")
print("Years:", len(annual_temperature))
print(
    "Start year:",
    annual_temperature["year"].min()
)
print(
    "End year:",
    annual_temperature["year"].max()
)

print("\nFirst 5 years:")
print(annual_temperature.head())

print("\nLast 5 years:")
print(annual_temperature.tail())
from sklearn.linear_model import LinearRegression

# Prepare data for trend calculation
X = annual_temperature[["year"]]
y = annual_temperature["annual_mean_temperature"]

model = LinearRegression()
model.fit(X, y)

trend_slope = model.coef_[0]
trend_per_decade = trend_slope * 10

print("\nTemperature Trend")
print("-----------------")
print("Trend:", round(trend_slope, 4), "°C per year")
print("Trend:", round(trend_per_decade, 4), "°C per decade")
import matplotlib.pyplot as plt

plt.figure(figsize=(10, 5))

plt.plot(
    annual_temperature["year"],
    annual_temperature["annual_mean_temperature"],
    marker="o",
    label="Annual mean temperature"
)

# Trend line
trend_values = model.predict(X)

plt.plot(
    annual_temperature["year"],
    trend_values,
    linestyle="--",
    label="Linear trend"
)

plt.xlabel("Year")
plt.ylabel("Temperature (°C)")
plt.title("Lucknow Annual Mean Temperature Trend (1990–2025)")
plt.legend()
plt.grid(True)

plt.tight_layout()
plt.show()
