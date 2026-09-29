from sqlalchemy import create_engine, text

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

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