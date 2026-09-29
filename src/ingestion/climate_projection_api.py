import requests
import pandas as pd

LATITUDE = 26.8467
LONGITUDE = 80.9462


def get_climate_projection():
    url = "https://climate-api.open-meteo.com/v1/climate"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": "2026-01-01",
        "end_date": "2049-12-31",
        "models": "EC_Earth3P_HR",
        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=60)
    response.raise_for_status()

    return response.json()


def clean_climate_projection(climate_data):
    daily = climate_data["daily"]

    df = pd.DataFrame({
        "date": daily["time"],
        "temperature_mean": daily["temperature_2m_mean"],
        "temperature_max": daily["temperature_2m_max"],
        "temperature_min": daily["temperature_2m_min"],
        "precipitation": daily["precipitation_sum"],
    })

    df["date"] = pd.to_datetime(df["date"])

    return df


if __name__ == "__main__":
    print("Fetching future climate projection...")

    climate_data = get_climate_projection()

    df = clean_climate_projection(climate_data)

    print("\nFuture Climate Projection")
    print("-------------------------")
    print("Rows:", len(df))
    print("Start date:", df["date"].min().date())
    print("End date:", df["date"].max().date())

    print("\nFirst 5 rows:")
    print(df.head())

    print("\nLast 5 rows:")
    print(df.tail())
