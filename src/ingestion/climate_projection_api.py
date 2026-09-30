import requests
import pandas as pd

LATITUDE = 26.8467
LONGITUDE = 80.9462


CLIMATE_MODELS = [
    "CMCC_CM2_VHR4",
    "FGOALS_f3_H",
    "HiRAM_SIT_HR",
    "MRI_AGCM3_2_S",
    "EC_Earth3P_HR",
    "MPI_ESM1_2_XR",
    "NICAM16_8S",
]


def get_climate_projection():
    url = "https://climate-api.open-meteo.com/v1/climate"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "start_date": "2026-01-01",
        "end_date": "2049-12-31",
        "models": ",".join(CLIMATE_MODELS),
        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min,"
            "precipitation_sum"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=120)
    response.raise_for_status()

    return response.json()


def clean_climate_projection(climate_data):
    daily = climate_data["daily"]

    dates = pd.to_datetime(daily["time"])

    records = []

    for model in CLIMATE_MODELS:

        mean_key = f"temperature_2m_mean_{model}"
        max_key = f"temperature_2m_max_{model}"
        min_key = f"temperature_2m_min_{model}"
        precip_key = f"precipitation_sum_{model}"

        for i, date in enumerate(dates):

            records.append({
                "date": date,
                "model": model,
                "temperature_mean": daily[mean_key][i],
                "temperature_max": daily[max_key][i],
                "temperature_min": daily[min_key][i],
                "precipitation": daily[precip_key][i],
            })

    df = pd.DataFrame(records)

    return df


if __name__ == "__main__":
    print("Fetching future climate projection...")
    print("Models:", ", ".join(CLIMATE_MODELS))

    climate_data = get_climate_projection()

    df = clean_climate_projection(climate_data)

    print("\nFuture Climate Projection")
    print("-------------------------")
    print("Rows:", len(df))
    print("Models:", df["model"].nunique())
    print("Start date:", df["date"].min().date())
    print("End date:", df["date"].max().date())

    print("\nRows per model:")
    print(df["model"].value_counts())

    print("\nFirst 10 rows:")
    print(df.head(10))

    print("\nLast 10 rows:")
    print(df.tail(10))