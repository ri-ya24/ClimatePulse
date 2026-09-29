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

# Load historical temperature data
query = """
SELECT date, temperature_mean
FROM historical_weather
ORDER BY date;
"""

df = pd.read_sql(query, engine)

df["date"] = pd.to_datetime(df["date"])

print("\nHistorical Temperature Data")
print("---------------------------")
print("Rows:", len(df))
print("Start date:", df["date"].min().date())
print("End date:", df["date"].max().date())


# --------------------------------------------------
# CREATE FEATURES
# --------------------------------------------------

# Previous day's temperature
df["temperature_lag_1"] = (
    df["temperature_mean"].shift(1)
)

# Temperature two days ago
df["temperature_lag_2"] = (
    df["temperature_mean"].shift(2)
)

# Temperature seven days ago
df["temperature_lag_7"] = (
    df["temperature_mean"].shift(7)
)

# 7-day rolling average
df["temperature_rolling_7"] = (
    df["temperature_mean"]
    .shift(1)
    .rolling(7)
    .mean()
)

# 30-day rolling average
df["temperature_rolling_30"] = (
    df["temperature_mean"]
    .shift(1)
    .rolling(30)
    .mean()
)


# --------------------------------------------------
# TARGET
# --------------------------------------------------

# Target = next day's temperature

df["target_temperature"] = (
    df["temperature_mean"].shift(-1)
)


# Remove rows with missing feature/target values
model_df = df.dropna().copy()


# --------------------------------------------------
# DISPLAY FEATURES
# --------------------------------------------------

print("\nModel Dataset")
print("-------------")
print("Rows:", len(model_df))

print("\nFeatures:")
print([
    "temperature_lag_1",
    "temperature_lag_2",
    "temperature_lag_7",
    "temperature_rolling_7",
    "temperature_rolling_30"
])

print("\nTarget:")
print("target_temperature")


print("\nSample:")
print(
    model_df[
        [
            "date",
            "temperature_lag_1",
            "temperature_lag_2",
            "temperature_lag_7",
            "temperature_rolling_7",
            "temperature_rolling_30",
            "target_temperature"
        ]
    ].head(10)
)


print("\nMissing values:")
print(
    model_df[
        [
            "temperature_lag_1",
            "temperature_lag_2",
            "temperature_lag_7",
            "temperature_rolling_7",
            "temperature_rolling_30",
            "target_temperature"
        ]
    ].isna().sum()
)
# --------------------------------------------------
# TIME-BASED TRAIN / TEST SPLIT
# --------------------------------------------------

features = [
    "temperature_lag_1",
    "temperature_lag_2",
    "temperature_lag_7",
    "temperature_rolling_7",
    "temperature_rolling_30"
]

target = "target_temperature"

X = model_df[features]
y = model_df[target]

# Use the first 80% for training
# and the last 20% for testing.
split_index = int(len(model_df) * 0.80)

X_train = X.iloc[:split_index]
X_test = X.iloc[split_index:]

y_train = y.iloc[:split_index]
y_test = y.iloc[split_index:]

print("\nTime-Based Train/Test Split")
print("---------------------------")

print("Training rows:", len(X_train))
print("Testing rows:", len(X_test))

print(
    "Training period:",
    model_df["date"].iloc[0].date(),
    "to",
    model_df["date"].iloc[split_index - 1].date()
)

print(
    "Testing period:",
    model_df["date"].iloc[split_index].date(),
    "to",
    model_df["date"].iloc[-1].date()
)
# --------------------------------------------------
# TRAIN XGBOOST MODEL
# --------------------------------------------------

from xgboost import XGBRegressor

print("\nTraining XGBoost model...")
print("-------------------------")

model = XGBRegressor(
    n_estimators=500,
    learning_rate=0.05,
    max_depth=6,
    subsample=0.8,
    colsample_bytree=0.8,
    objective="reg:squarederror",
    random_state=42
)

model.fit(
    X_train,
    y_train
)

print("XGBoost model trained successfully!")
# --------------------------------------------------
# MODEL PREDICTIONS
# --------------------------------------------------

print("\nGenerating predictions...")
print("-------------------------")

y_pred = model.predict(X_test)

print("Predictions generated!")


# --------------------------------------------------
# MODEL EVALUATION
# --------------------------------------------------

from sklearn.metrics import (
    mean_absolute_error,
    mean_squared_error,
    r2_score
)
import numpy as np

mae = mean_absolute_error(
    y_test,
    y_pred
)

rmse = np.sqrt(
    mean_squared_error(
        y_test,
        y_pred
    )
)

r2 = r2_score(
    y_test,
    y_pred
)


print("\nXGBoost Model Performance")
print("-------------------------")

print("MAE :", round(mae, 3), "Â°C")
print("RMSE:", round(rmse, 3), "Â°C")
print("RÂ²  :", round(r2, 3))
# --------------------------------------------------
# NAIVE BASELINE
# --------------------------------------------------

print("\nNaive Baseline Evaluation")
print("-------------------------")

# Predict tomorrow's temperature
# using today's temperature
naive_predictions = X_test["temperature_lag_1"]

naive_mae = mean_absolute_error(
    y_test,
    naive_predictions
)

naive_rmse = np.sqrt(
    mean_squared_error(
        y_test,
        naive_predictions
    )
)

naive_r2 = r2_score(
    y_test,
    naive_predictions
)

print("Naive Baseline MAE :", round(naive_mae, 3), "Â°C")
print("Naive Baseline RMSE:", round(naive_rmse, 3), "Â°C")
print("Naive Baseline RÂ²  :", round(naive_r2, 3))


# --------------------------------------------------
# COMPARISON
# --------------------------------------------------

print("\nModel Comparison")
print("----------------")

print(
    "XGBoost MAE :",
    round(mae, 3),
    "Â°C"
)

print(
    "Naive MAE   :",
    round(naive_mae, 3),
    "Â°C"
)

improvement = (
    (naive_mae - mae)
    / naive_mae
) * 100

print(
    "MAE Improvement:",
    round(improvement, 2),
    "%"
)
# --------------------------------------------------
# NEXT-DAY TEMPERATURE FORECAST
# --------------------------------------------------

print("\nNext-Day Temperature Forecast")
print("-----------------------------")

latest_features = model_df[features].iloc[[-1]]

next_day_prediction = model.predict(
    latest_features
)[0]

latest_date = model_df["date"].iloc[-1]

print(
    "Last historical date:",
    latest_date.date()
)

print(
    "Predicted next-day temperature:",
    round(next_day_prediction, 2),
    "Â°C"
)
# --------------------------------------------------
# SAVE TRAINED MODEL
# --------------------------------------------------

import joblib

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "temperature_xgboost_model.pkl"
)

joblib.dump(
    model,
    MODEL_PATH
)

print("\nModel saved successfully!")
print("Model path:", MODEL_PATH)
