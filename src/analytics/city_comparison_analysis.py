import sys
from pathlib import Path

sys.path.append(str(Path(__file__).resolve().parents[1]))

from ingestion.city_comparison_api import get_city_comparison


def calculate_air_quality_score(city):
    pm25_score = min(city["pm2_5"] / 75 * 100, 100)
    pm10_score = min(city["pm10"] / 150 * 100, 100)
    no2_score = min(city["nitrogen_dioxide"] / 80 * 100, 100)
    so2_score = min(city["sulphur_dioxide"] / 80 * 100, 100)
    ozone_score = min(city["ozone"] / 180 * 100, 100)

    score = (
        pm25_score * 0.40
        + pm10_score * 0.20
        + no2_score * 0.15
        + so2_score * 0.10
        + ozone_score * 0.15
    )

    return round(score, 2)


def calculate_temperature_impact(city):
    reference_temperature = 25.0

    temperature_difference = (
        city["temperature"] - reference_temperature
    )

    score = max(
        0,
        min(
            (temperature_difference + 5) / 15 * 100,
            100
        )
    )

    return round(score, 2)


def calculate_overall_city_impact(air_quality_score, temperature_score):
    score = (
        air_quality_score * 0.60
        + temperature_score * 0.40
    )

    return round(score, 2)


if __name__ == "__main__":

    cities = get_city_comparison()

    print("\nCity Comparison Analysis")
    print("------------------------")

    for city in cities:

        air_quality_score = calculate_air_quality_score(city)

        temperature_score = calculate_temperature_impact(city)

        overall_score = calculate_overall_city_impact(
            air_quality_score,
            temperature_score
        )

        print(
            city["city"],
            "->",
            "Air Quality:",
            air_quality_score,
            "/ 100 |",
            "Temperature:",
            temperature_score,
            "/ 100 |",
            "Overall Impact:",
            overall_score,
            "/ 100"
        )