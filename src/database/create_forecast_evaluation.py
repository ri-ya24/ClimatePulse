from sqlalchemy import create_engine, text

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
engine = create_engine(DATABASE_URL)

create_table_query = """
CREATE TABLE IF NOT EXISTS forecast_evaluation (
    id SERIAL PRIMARY KEY,
    forecast_date DATE NOT NULL,
    predicted_temperature DOUBLE PRECISION NOT NULL,
    actual_temperature DOUBLE PRECISION,
    prediction_error DOUBLE PRECISION,
    absolute_error DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
"""

with engine.begin() as connection:
    connection.execute(
        text(create_table_query)
    )

print("Forecast evaluation table created successfully!")
