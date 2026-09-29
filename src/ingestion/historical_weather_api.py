import requests
import pandas as pd

LATITUDE = 26.8467
LONGITUDE = 80.9462


def get_historical_weather(start_date, end_date):
    url = "https://archive-api.open-meteo.com/v1/archive"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": start_date,
        "end_date": end_date,
        "daily": (
            "temperature_2m_max,"
            "temperature_2m_min,"
            "temperature_2m_mean,"
            "precipitation_sum,"
            "rain_sum,"
            "wind_speed_10m_max"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    return response.json()


def clean_historical_weather(weather_data):
    daily = weather_data["daily"]

    df = pd.DataFrame({
        "date": daily["time"],
        "temperature_max": daily["temperature_2m_max"],
        "temperature_min": daily["temperature_2m_min"],
        "temperature_mean": daily["temperature_2m_mean"],
        "precipitation": daily["precipitation_sum"],
        "rain": daily["rain_sum"],
        "wind_speed_max": daily["wind_speed_10m_max"],
    })

    df["date"] = pd.to_datetime(df["date"])

    return df


if __name__ == "__main__":

    print("Fetching historical weather data...")

    weather_data = get_historical_weather(
        "1990-01-01",
        "2025-12-31"
    )

    df = clean_historical_weather(weather_data)

    print("\nHistorical Weather Dataset")
    print("--------------------------")
    print("Rows:", len(df))
    print("Columns:", list(df.columns))
    print("Start date:", df["date"].min().date())
    print("End date:", df["date"].max().date())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nLast 5 rows:")
    print(df.tail())

    print("\nMissing values:")
    print(df.isna().sum())