import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine, text
from sklearn.ensemble import IsolationForest

sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# LOAD HISTORICAL DATA
# --------------------------------------------------

query = """
SELECT
    date,
    temperature_mean,
    precipitation,
    wind_speed_max
FROM historical_weather
ORDER BY date;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])


# --------------------------------------------------
# FEATURES
# --------------------------------------------------

features = [
    "temperature_mean",
    "precipitation",
    "wind_speed_max"
]

model_df = df.dropna(
    subset=features
).copy()


# --------------------------------------------------
# ISOLATION FOREST
# --------------------------------------------------

model = IsolationForest(
    n_estimators=200,
    contamination=0.02,
    random_state=42
)

model.fit(model_df[features])

model_df["anomaly_score"] = model.decision_function(
    model_df[features]
)

model_df["is_anomaly"] = (
    model.predict(model_df[features]) == -1
)


# --------------------------------------------------
# SELECT ANOMALIES
# --------------------------------------------------

anomalies = model_df[
    model_df["is_anomaly"]
].copy()


# --------------------------------------------------
# CREATE TABLE
# --------------------------------------------------

create_table_query = """
CREATE TABLE IF NOT EXISTS climate_anomalies (
    id SERIAL PRIMARY KEY,
    date DATE NOT NULL,
    temperature_mean DOUBLE PRECISION,
    precipitation DOUBLE PRECISION,
    wind_speed_max DOUBLE PRECISION,
    anomaly_score DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as connection:
    connection.execute(
        text(create_table_query)
    )


# --------------------------------------------------
# CLEAR OLD RESULTS
# --------------------------------------------------

with engine.begin() as connection:
    connection.execute(
        text("DELETE FROM climate_anomalies")
    )


# --------------------------------------------------
# SAVE ANOMALIES
# --------------------------------------------------

anomalies[
    [
        "date",
        "temperature_mean",
        "precipitation",
        "wind_speed_max",
        "anomaly_score"
    ]
].to_sql(
    "climate_anomalies",
    engine,
    if_exists="append",
    index=False
)


print("\nClimate Anomalies Saved")
print("----------------------")
print(
    "Anomalies saved:",
    len(anomalies)
)
