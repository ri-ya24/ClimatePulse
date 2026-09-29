import requests

LATITUDE = 26.8467
LONGITUDE = 80.9462


def get_air_quality():
    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": (
            "pm10,"
            "pm2_5,"
            "carbon_monoxide,"
            "nitrogen_dioxide,"
            "sulphur_dioxide,"
            "ozone"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=30)
    response.raise_for_status()

    return response.json()


def clean_air_quality_data(air_data):
    current = air_data["current"]

    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "time": current["time"],
        "pm10": current["pm10"],
        "pm2_5": current["pm2_5"],
        "carbon_monoxide": current["carbon_monoxide"],
        "nitrogen_dioxide": current["nitrogen_dioxide"],
        "sulphur_dioxide": current["sulphur_dioxide"],
        "ozone": current["ozone"],
    }


if __name__ == "__main__":
    print("Fetching live air quality data...")

    air_data = get_air_quality()
    clean_data = clean_air_quality_data(air_data)

    print("\nLive Air Quality")
    print("----------------")
    print(clean_data)