import os
import sys
import json
import utils, api_secrets
import requests
import time
import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv

if __name__ == "__main__":

    """Step 1: Setup"""
    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_path = os.path.join(repo_root, ".env.dev")
    tf_outputs_path = os.path.join(repo_root, "terraform", "terraform_outputs.json")

    with open(tf_outputs_path) as file:
        tf_outputs = json.load(file)
    load_dotenv(env_path)
    gcp_project_id = os.getenv("GCP_PROJECT_ID")

    db_params = {
        "host": tf_outputs["db_host"]["value"]["dev"],
        "dbname": os.getenv("PG_DATABASE", "postgres"),
        "user": tf_outputs["db_service_account_name"]["value"],
        "password": utils.get_secret(gcp_project_id, "postgres-service-account-pwd"),
        "port": os.getenv("PG_PORT", "5432"),
    }

    strava_bearer_token = json.loads(
        utils.get_secret(gcp_project_id, "strava-access-token")
    )

    if strava_bearer_token["expires_at"] < time.time():
        print("Token Expired")

        access_token = api_secrets.refresh_access_token(
            utils.get_secret(gcp_project_id, "strava-client-id"),
            utils.get_secret(gcp_project_id, "strava-client-secret"),
            utils.get_secret(gcp_project_id, "strava-refresh-token"),
        )
        refresh_token = access_token.pop("refresh_token")

        secrets_to_update = {
            "strava-access-token": json.dumps(access_token),
            "strava-refresh-token": refresh_token,
        }

        for name, value in secrets_to_update.items():
            utils.put_secret(gcp_project_id, name, value)

    """Step 2: Get Bboxes from DB"""
    schema = "dev"
    db_table = "bounding_boxes"

    fetch_pending_bboxes_query = sql.SQL(
        "SELECT * FROM {schema}.{table} WHERE status = %s LIMIT 1"
    ).format(schema=sql.Identifier(schema), table=sql.Identifier(db_table))

    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(fetch_pending_bboxes_query, ("pending",))
            bbox = cur.fetchall()
            column_names = [desc[0] for desc in cur.description]

    if len(bbox) == 0:
        print("No Bboxes to fetch segments for")
        sys.exit(1)

    """Step 3: Make API Call"""
    column_indexes = {key: idx for idx, key in enumerate(column_names)}

    segments = {}
    url = "https://www.strava.com/api/v3/segments/explore"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {strava_bearer_token['access_token']}",
    }

    bbox = list(bbox[0])
    pk_id = bbox[column_indexes["id"]]
    request_safe_coordinates = [
        bbox[column_indexes["sw_latitude"]],
        bbox[column_indexes["sw_longitude"]],
        bbox[column_indexes["ne_latitude"]],
        bbox[column_indexes["ne_longitude"]],
    ]
    request_safe_coordinates = ",".join(
        str(point) for point in request_safe_coordinates
    )

    params = {"bounds": request_safe_coordinates, "activity_type": "riding"}

    try:
        time_fetched = int(time.time())
        response = requests.request("GET", url, headers=headers, params=params)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Request failed: {e}")

    """Step 4: Upload to GCP Blob"""
    segment_data = json.loads(response.text)
    segment_data["time_fetched"] = time_fetched

    file_name = f"[{request_safe_coordinates}]__{time_fetched}.json"
    temp_output_path = os.path.join(repo_root, "data", file_name)
    with open(temp_output_path, "w", encoding="utf-8") as f:
        json.dump(segment_data, f)

    utils.upload_blob(tf_outputs["bucket_name"]["value"], temp_output_path, file_name)

    os.remove(temp_output_path)

    update_fetched_bboxes_query = sql.SQL(
        """
    UPDATE {schema}.{table}
    SET status = %s
    WHERE id = %s
    """
    ).format(schema=sql.Identifier(schema), table=sql.Identifier(db_table))

    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(update_fetched_bboxes_query, ("fetched", pk_id))
