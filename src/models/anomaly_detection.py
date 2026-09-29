import os
import sys
from pathlib import Path

import pandas as pd
from sqlalchemy import create_engine
from dotenv import load_dotenv
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
# SELECT FEATURES
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
# TRAIN ISOLATION FOREST
# --------------------------------------------------

model = IsolationForest(
    n_estimators=200,
    contamination=0.02,
    random_state=42
)

model.fit(
    model_df[features]
)


# --------------------------------------------------
# DETECT ANOMALIES
# --------------------------------------------------

model_df["anomaly_prediction"] = model.predict(
    model_df[features]
)

model_df["anomaly_score"] = model.decision_function(
    model_df[features]
)

model_df["is_anomaly"] = (
    model_df["anomaly_prediction"] == -1
)


# --------------------------------------------------
# RESULTS
# --------------------------------------------------

anomalies = model_df[
    model_df["is_anomaly"]
].copy()


print("\nClimatePulse Anomaly Detection")
print("------------------------------")

print(
    "Total observations:",
    len(model_df)
)

print(
    "Detected anomalies:",
    len(anomalies)
)

print(
    "Anomaly percentage:",
    round(
        len(anomalies) / len(model_df) * 100,
        2
    ),
    "%"
)


# --------------------------------------------------
# TOP ANOMALIES
# --------------------------------------------------

print("\nTop Anomalous Observations")
print("--------------------------")

print(
    anomalies
    .sort_values("anomaly_score")
    [
        [
            "date",
            "temperature_mean",
            "precipitation",
            "wind_speed_max",
            "anomaly_score"
        ]
    ]
    .head(10)
    .to_string(index=False)
)
