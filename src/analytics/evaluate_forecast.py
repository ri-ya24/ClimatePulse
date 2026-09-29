import pandas as pd
import requests
from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
LATITUDE = 26.8467
LONGITUDE = 80.9462

engine = create_engine(DATABASE_URL)


# --------------------------------------------------
# GET SAVED PREDICTION
# --------------------------------------------------

query = """
SELECT forecast_date, predicted_temperature
FROM temperature_forecast
ORDER BY created_at DESC
LIMIT 1;
"""

forecast = pd.read_sql(query, engine)

forecast_date = forecast["forecast_date"].iloc[0]
predicted_temperature = forecast["predicted_temperature"].iloc[0]


# --------------------------------------------------
# FETCH ACTUAL OBSERVED TEMPERATURE
# --------------------------------------------------

url = "https://archive-api.open-meteo.com/v1/archive"

params = {
    "latitude": LATITUDE,
    "longitude": LONGITUDE,
    "start_date": forecast_date.strftime("%Y-%m-%d"),
    "end_date": forecast_date.strftime("%Y-%m-%d"),
    "daily": "temperature_2m_mean",
    "timezone": "Asia/Kolkata",
}

response = requests.get(
    url,
    params=params,
    timeout=60
)

response.raise_for_status()

weather_data = response.json()

actual_temperature = (
    weather_data["daily"]["temperature_2m_mean"][0]
)


# --------------------------------------------------
# CALCULATE ERROR
# --------------------------------------------------

prediction_error = (
    predicted_temperature - actual_temperature
)

absolute_error = abs(prediction_error)


print("\nForecast Evaluation")
print("-------------------")

print(
    "Forecast date:",
    forecast_date
)

print(
    "Predicted temperature:",
    round(predicted_temperature, 2),
    "Â°C"
)

print(
    "Actual temperature:",
    round(actual_temperature, 2),
    "Â°C"
)

print(
    "Prediction error:",
    round(prediction_error, 2),
    "Â°C"
)

print(
    "Absolute error:",
    round(absolute_error, 2),
    "Â°C"
)


# --------------------------------------------------
# SAVE EVALUATION
# --------------------------------------------------

insert_query = """
INSERT INTO forecast_evaluation (
    forecast_date,
    predicted_temperature,
    actual_temperature,
    prediction_error,
    absolute_error
)
VALUES (
    :forecast_date,
    :predicted_temperature,
    :actual_temperature,
    :prediction_error,
    :absolute_error
);
"""

with engine.begin() as connection:
    connection.execute(
        text(insert_query),
        {
            "forecast_date": forecast_date,
            "predicted_temperature": float(
                predicted_temperature
            ),
            "actual_temperature": float(
                actual_temperature
            ),
            "prediction_error": float(
                prediction_error
            ),
            "absolute_error": float(
                absolute_error
            )
        }
    )

print("\nEvaluation saved to PostgreSQL successfully!")
