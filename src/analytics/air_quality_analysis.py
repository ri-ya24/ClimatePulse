import os
import sys
from pathlib import Path
import pandas as pd
from sqlalchemy import create_engine

from dotenv import load_dotenv
sys.path.append(str(Path(__file__).resolve().parents[1]))

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise ValueError("DATABASE_URL is not set in the environment.")
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
