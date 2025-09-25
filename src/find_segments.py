import os
import utils
import requests
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

if __name__ == "__main__":

    """Step 1: Setup"""
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__),".."))
    env_path = os.path.join(repo_root, ".env.dev")

    load_dotenv(env_path)

    db_params = {
    "host": os.getenv("PG_HOST"),
    "dbname": os.getenv("PG_DATABASE"),
    "user": os.getenv("PG_USER"),
    "password": os.getenv("PG_PASSWORD"),
    "port": os.getenv("PG_PORT")
    }

    schema = "dev"
    db_table = "bounding_boxes"

    """Step 2: Get Bboxes from DB"""
    fetch_pending_bboxes_query = sql.SQL(
        "SELECT * FROM {schema}.{table} WHERE status = %s").format(
            schema=sql.Identifier(schema),
            table=sql.Identifier(db_table)
        )
    
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_pending_bboxes_query, ("pending",))
            bboxes = cur.fetchall()

    """Step 3: Make API Call"""
    segments = {}
    url = "https://www.strava.com/api/v3/segments/explore"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {os.getenv("ACCESS_TOKEN")}"}
    
    for bbox in bboxes:

        coordinates = list(bbox)[1:5]
        coordinates = ", ".join(coordinates)

        params = {
            "bounds": coordinates,
            "activity_type": "riding"}
        response = requests.request("GET", url, headers=headers)
        segments[bounds] = response.text


    

    



segments = {}
url = "https://www.strava.com/api/v3/segments/explore"
headers = {
    "accept": "application/json",
    "authorization":}

for bbx in a:
    bounds = ",".join(str(v) for v in bbx)
    params = {
        "bounds": bounds,
        "activity_type": "riding"
    }
    response = requests.request("GET", url, headers=headers)
    segments[bounds] = response.text


responses = [val for val in segments.values()]
