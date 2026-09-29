import requests


CITIES = {
    "Lucknow": {
        "latitude": 26.8467,
        "longitude": 80.9462
    },
    "Delhi": {
        "latitude": 28.6139,
        "longitude": 77.2090
    },
    "Mumbai": {
        "latitude": 19.0760,
        "longitude": 72.8777
    },
    "Bengaluru": {
        "latitude": 12.9716,
        "longitude": 77.5946
    },
    "Kolkata": {
        "latitude": 22.5726,
        "longitude": 88.3639
    },
    "Chennai": {
        "latitude": 13.0827,
        "longitude": 80.2707
    },
    "Hyderabad": {
        "latitude": 17.3850,
        "longitude": 78.4867
    },
    "Jaipur": {
        "latitude": 26.9124,
        "longitude": 75.7873
    },
    "Ahmedabad": {
        "latitude": 23.0225,
        "longitude": 72.5714
    },
    "Pune": {
        "latitude": 18.5204,
        "longitude": 73.8567
    }
}


def get_city_weather(city_name, coordinates):

    url = "https://api.open-meteo.com/v1/forecast"

    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "current": (
            "temperature_2m,"
            "relative_humidity_2m,"
            "apparent_temperature,"
            "precipitation,"
            "wind_speed_10m"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]

    return {
        "city": city_name,
        "time": current["time"],
        "temperature": current["temperature_2m"],
        "humidity": current["relative_humidity_2m"],
        "apparent_temperature": current["apparent_temperature"],
        "precipitation": current["precipitation"],
        "wind_speed": current["wind_speed_10m"],
    }


def get_city_air_quality(city_name, coordinates):

    url = "https://air-quality-api.open-meteo.com/v1/air-quality"

    params = {
        "latitude": coordinates["latitude"],
        "longitude": coordinates["longitude"],
        "current": (
            "pm10,"
            "pm2_5,"
            "nitrogen_dioxide,"
            "sulphur_dioxide,"
            "ozone"
        ),
        "timezone": "Asia/Kolkata",
    }

    response = requests.get(
        url,
        params=params,
        timeout=30
    )

    response.raise_for_status()

    data = response.json()

    current = data["current"]

    return {
        "city": city_name,
        "time": current["time"],
        "pm10": current["pm10"],
        "pm2_5": current["pm2_5"],
        "nitrogen_dioxide": current["nitrogen_dioxide"],
        "sulphur_dioxide": current["sulphur_dioxide"],
        "ozone": current["ozone"],
    }


def get_city_comparison():

    comparison = []

    for city_name, coordinates in CITIES.items():

        weather = get_city_weather(
            city_name,
            coordinates
        )

        air = get_city_air_quality(
            city_name,
            coordinates
        )

        comparison.append({
            "city": city_name,

            "weather_time": weather["time"],
            "temperature": weather["temperature"],
            "humidity": weather["humidity"],
            "apparent_temperature": weather["apparent_temperature"],
            "precipitation": weather["precipitation"],
            "wind_speed": weather["wind_speed"],

            "air_quality_time": air["time"],
            "pm10": air["pm10"],
            "pm2_5": air["pm2_5"],
            "nitrogen_dioxide": air["nitrogen_dioxide"],
            "sulphur_dioxide": air["sulphur_dioxide"],
            "ozone": air["ozone"],
        })

    return comparison


if __name__ == "__main__":

    comparison_data = get_city_comparison()

    print("\nCity Comparison")
    print("----------------")

    for city in comparison_data:
        print(city)