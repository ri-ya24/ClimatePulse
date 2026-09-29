from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
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
