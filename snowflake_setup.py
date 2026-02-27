import os
import snowflake.connector
from dotenv import load_dotenv

load_dotenv("config.env")

ACCOUNT    = os.getenv("SNOWFLAKE_ACCOUNT")
USER       = os.getenv("SNOWFLAKE_USER")
PASSWORD   = os.getenv("SNOWFLAKE_PASSWORD")
DATABASE   = os.getenv("SNOWFLAKE_DATABASE")
SCHEMA     = os.getenv("SNOWFLAKE_SCHEMA")
WAREHOUSE  = os.getenv("SNOWFLAKE_WAREHOUSE")
KAFKA_USER = os.getenv("SNOWFLAKE_KAFKA_USER")
KAFKA_ROLE = os.getenv("SNOWFLAKE_KAFKA_ROLE")

with open("keys/rsa_key.pub", "r") as f:
    pub_key = f.read()
pub_key_clean = (
    pub_key
    .replace("-----BEGIN PUBLIC KEY-----", "")
    .replace("-----END PUBLIC KEY-----", "")
    .replace("\n", "")
    .strip()
)

conn = snowflake.connector.connect(
    account=ACCOUNT,
    user=USER,
    password=PASSWORD,
    role="ACCOUNTADMIN"
)
cur = conn.cursor()

statements = [
    f"CREATE DATABASE IF NOT EXISTS {DATABASE}",
    f"CREATE SCHEMA IF NOT EXISTS {DATABASE}.{SCHEMA}",
    f"CREATE ROLE IF NOT EXISTS {KAFKA_ROLE}",
    f"""CREATE WAREHOUSE IF NOT EXISTS {WAREHOUSE}
        WAREHOUSE_SIZE = 'XSMALL'
        AUTO_SUSPEND = 60
        AUTO_RESUME = TRUE""",
    f"""CREATE USER IF NOT EXISTS {KAFKA_USER}
        RSA_PUBLIC_KEY = '{pub_key_clean}'
        DEFAULT_ROLE = {KAFKA_ROLE}
        MUST_CHANGE_PASSWORD = FALSE""",
    f"GRANT ROLE {KAFKA_ROLE} TO USER {KAFKA_USER}",
    f"GRANT USAGE ON WAREHOUSE {WAREHOUSE} TO ROLE {KAFKA_ROLE}",
    f"GRANT ALL ON DATABASE {DATABASE} TO ROLE {KAFKA_ROLE}",
    f"GRANT ALL ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {KAFKA_ROLE}",
    f"GRANT CREATE TABLE ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {KAFKA_ROLE}",
    f"GRANT CREATE STAGE ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {KAFKA_ROLE}",
    f"GRANT CREATE PIPE ON SCHEMA {DATABASE}.{SCHEMA} TO ROLE {KAFKA_ROLE}",
    f"GRANT SELECT ON ALL TABLES IN SCHEMA {DATABASE}.{SCHEMA} TO ROLE ACCOUNTADMIN",
]

for stmt in statements:
    label = stmt.strip().split("\n")[0][:70]
    cur.execute(stmt)
    print(f"[OK] {label}")

cur.close()
conn.close()
print("\nSnowflake setup complete.")
