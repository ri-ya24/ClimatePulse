import requests


LATITUDE = 26.8467
LONGITUDE = 80.9462


def get_current_weather():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "wind_speed_10m,"
            "weather_code"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    return response.json()


def clean_weather_data(weather_data):
    current = weather_data["current"]

    return {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "time": current["time"],
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "apparent_temperature": current["apparent_temperature"],
        "precipitation": current["precipitation"],
        "wind_speed": current["wind_speed_10m"],
        "weather_code": current["weather_code"],
    }
def get_next_day_forecast():
    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": LATITUDE,
        "longitude": LONGITUDE,
        "daily": (
            "temperature_2m_mean,"
            "temperature_2m_max,"
            "temperature_2m_min"
        ),
        "forecast_days": 2,
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(url, params=params, timeout=10)
    response.raise_for_status()

    data = response.json()
    daily = data["daily"]

    tomorrow_index = 1

    return {
        "date": daily["time"][tomorrow_index],
        "temperature_mean": daily["temperature_2m_mean"][tomorrow_index],
        "temperature_max": daily["temperature_2m_max"][tomorrow_index],
        "temperature_min": daily["temperature_2m_min"][tomorrow_index],
    }


if __name__ == "__main__":
    weather_data = get_current_weather()

    clean_data = clean_weather_data(weather_data)

    print("\nClean Weather Data")
    print("------------------")
    print(clean_data)
