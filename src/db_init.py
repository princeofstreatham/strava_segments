import os
import utils
import psycopg2
from dotenv import load_dotenv


def read_sql_file(path):
    with open(path, "r") as f:
        return f.read()


if __name__ == "__main__":

    """Step 1: Setup"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(repo_root, ".env.dev")

    load_dotenv(env_path)

    db_params = {
        "host": os.getenv("PG_HOST"),
        "dbname": os.getenv("PG_DATABASE"),
        "user": os.getenv("PG_USER"),
        "password": os.getenv("PG_PASSWORD"),
        "port": os.getenv("PG_PORT"),
    }

    db_table = "dev.bounding_boxes"
    csv_path = os.path.join(repo_root, "data", "bounding_boxes.csv")

    """Step 2: Initialise DB"""
    create_table_sql = read_sql_file(
        os.path.join(repo_root, "src", "sql", "create_bounding_boxes.sql")
    )

    copy_sql = f"""
    COPY {db_table} (sw_longitude, sw_latitude, ne_longitude,  ne_latitude, status)
    FROM STDIN WITH CSV HEADER;
    """

    with psycopg2.connect(**db_params) as conn:  # connection is a context manager
        with conn.cursor() as cur:

            cur.execute(create_table_sql)

            cur.execute(f"SELECT COUNT(*) FROM {db_table}")
            if cur.fetchone()[0] == 0:
                with open(csv_path, "r") as f:
                    cur.copy_expert(copy_sql, f)
                print(f"{csv_path} uploaded to {db_table}")
            else:
                print(f"Table {db_table} not empty, skipping upload.")
