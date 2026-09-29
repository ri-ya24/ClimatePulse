import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

sys.path.append(str(Path(__file__).resolve().parents[1]))

DATABASE_URL = "postgresql+psycopg2://postgres:2417@localhost:5432/climatepulse"

engine = create_engine(DATABASE_URL)

query = """
SELECT *
FROM live_air_quality
ORDER BY time DESC
LIMIT 1;
"""

df = pd.read_sql(query, engine)

print("\nLatest Air Quality")
print("------------------")
print(df.to_string(index=False))