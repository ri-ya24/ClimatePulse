import pandas as pd
import requests
import time
from pathlib import Path

CITIES = {
    "Lucknow": (26.8467, 80.9462),
    "Delhi": (28.6139, 77.2090),
    "Mumbai": (19.0760, 72.8777),
    "Bengaluru": (12.9716, 77.5946),
    "Kolkata": (22.5726, 88.3639),
    "Chennai": (13.0827, 80.2707),
    "Hyderabad": (17.3850, 78.4867),
    "Jaipur": (26.9124, 75.7873),
    "Ahmedabad": (23.0225, 72.5714),
    "Pune": (18.5204, 73.8567),
}

ROOT = Path(__file__).resolve().parent

HIST_FILE = ROOT / "historical_weather_all_cities.csv"
FUTURE_FILE = ROOT / "climate_projection_all_cities.csv"


def download_with_retry(url, city, dataset_name):
    for attempt in range(6):
        try:
            response = requests.get(url, timeout=120)

            if response.status_code == 429:
                wait_time = 30 * (attempt + 1)
                print(
                    f"{city} {dataset_name}: "
                    f"Rate limit reached. Waiting {wait_time} seconds..."
                )
                time.sleep(wait_time)
                continue

            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            if attempt == 5:
                raise

            wait_time = 20 * (attempt + 1)
            print(
                f"{city} {dataset_name}: request failed. "
                f"Retrying in {wait_time} seconds..."
            )
            time.sleep(wait_time)

    return None


# --------------------------------------------------
# Load already completed data
# --------------------------------------------------

if HIST_FILE.exists():
    historical_df = pd.read_csv(HIST_FILE)
    completed_hist = set(historical_df["City"].unique())
else:
    historical_df = pd.DataFrame()
    completed_hist = set()


if FUTURE_FILE.exists():
    future_df = pd.read_csv(FUTURE_FILE)
    completed_future = set(future_df["City"].unique())
else:
    future_df = pd.DataFrame()
    completed_future = set()


# --------------------------------------------------
# Download city by city
# --------------------------------------------------

for city, (lat, lon) in CITIES.items():

    print(f"\n==============================")
    print(f"Processing {city}")
    print(f"==============================")

    # ----------------------------------------------
    # Historical
    # ----------------------------------------------

    if city not in completed_hist:

        print(f"Downloading {city} historical data...")

        historical_url = (
            "https://archive-api.open-meteo.com/v1/archive"
            f"?latitude={lat}"
            f"&longitude={lon}"
            "&start_date=1990-01-01"
            "&end_date=2025-12-31"
            "&daily=temperature_2m_max,temperature_2m_min,"
            "temperature_2m_mean,precipitation_sum,windspeed_10m_max"
            "&timezone=auto"
        )

        data = download_with_retry(
            historical_url,
            city,
            "historical"
        )["daily"]

        hist = pd.DataFrame(data)
        hist["City"] = city

        hist = hist.rename(columns={
            "time": "date",
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "temperature_2m_mean": "temp_mean",
            "windspeed_10m_max": "wind_max",
            "precipitation_sum": "precipitation",
        })

        hist = hist[
            [
                "City",
                "date",
                "temp_max",
                "temp_min",
                "temp_mean",
                "precipitation",
                "wind_max",
            ]
        ]

        historical_df = pd.concat(
            [historical_df, hist],
            ignore_index=True
        )

        historical_df.to_csv(
            HIST_FILE,
            index=False
        )

        print(
            f"{city} historical saved: "
            f"{len(hist)} rows"
        )

        time.sleep(15)

    else:
        print(f"{city} historical already exists. Skipping.")


    # ----------------------------------------------
    # Future Climate Projection
    # ----------------------------------------------

    if city not in completed_future:

        print(f"Downloading {city} future data...")

        future_url = (
            "https://climate-api.open-meteo.com/v1/climate"
            f"?latitude={lat}"
            f"&longitude={lon}"
            "&start_date=2026-01-01"
            "&end_date=2049-12-31"
            "&models=EC_Earth3P_HR"
            "&daily=temperature_2m_mean,temperature_2m_max,"
            "temperature_2m_min,precipitation_sum"
        )

        data = download_with_retry(
            future_url,
            city,
            "future"
        )["daily"]

        fut = pd.DataFrame(data)
        fut["City"] = city

        fut = fut.rename(columns={
            "time": "date",
            "temperature_2m_mean": "temp_mean",
            "temperature_2m_max": "temp_max",
            "temperature_2m_min": "temp_min",
            "precipitation_sum": "precipitation",
        })

        fut = fut[
            [
                "City",
                "date",
                "temp_mean",
                "temp_max",
                "temp_min",
                "precipitation",
            ]
        ]

        future_df = pd.concat(
            [future_df, fut],
            ignore_index=True
        )

        future_df.to_csv(
            FUTURE_FILE,
            index=False
        )

        print(
            f"{city} future saved: "
            f"{len(fut)} rows"
        )

        time.sleep(15)

    else:
        print(f"{city} future already exists. Skipping.")


print("\n================================")
print("ALL CITY DATA EXPORT COMPLETE")
print("================================")
print("Historical:", historical_df.shape)
print("Future:", future_df.shape)
print("Historical file:", HIST_FILE)
print("Future file:", FUTURE_FILE)