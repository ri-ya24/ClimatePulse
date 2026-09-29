from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)

with engine.begin() as connection:
    connection.execute(
        text("""
            DELETE FROM temperature_forecast
            WHERE id <> (
                SELECT id
                FROM temperature_forecast
                WHERE forecast_date = :forecast_date
                ORDER BY created_at DESC
                LIMIT 1
            )
        """),
        {"forecast_date": "2026-09-29"}
    )

print("Duplicate forecast rows deleted successfully!")