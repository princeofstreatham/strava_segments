import os
import sys
import base64
import json
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any, List

import requests
import psycopg2
from psycopg2 import sql
import colorlog
from pythonjsonlogger import jsonlogger
from dotenv import load_dotenv
from google.cloud import pubsub_v1

import utils
import api_secrets
import uuid

logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

stdout = colorlog.StreamHandler(stream=sys.stdout)
fmt = colorlog.ColoredFormatter(
    "%(name)s: %(white)s%(asctime)s%(reset)s | "
    "%(log_color)s%(levelname)s%(reset)s | "
    "%(blue)s%(filename)s:%(lineno)s%(reset)s | "
    "%(process)d >>> %(log_color)s%(message)s%(reset)s"
)
stdout.setFormatter(fmt)
logger.addHandler(stdout)

file_handler = TimedRotatingFileHandler(f"{__name__}_logs.txt", backupCount=5, when="midnight")
jsonFmt = jsonlogger.JsonFormatter(
    "%(name)s %(asctime)s %(levelname)s %(filename)s %(lineno)s %(process)d %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
file_handler.setFormatter(jsonFmt)
logger.addHandler(file_handler)

ENV = "dev"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(REPO_ROOT, f".env.{ENV}")
TF_OUTPUTS_PATH = os.path.join(REPO_ROOT, "terraform", f"terraform_outputs_{ENV}.json")
MAX_REQUEST_RETRIES = 6
BACKOFF_FACTOR = 4

metrics = {
    "messages_processed": 0,
    "messages_failed": 0,
    "requests_success": 0,
    "requests_failed": 0,
}

def load_tf_outputs(path: str) -> Dict[str, Any]:
    logger.debug(f"Loading Terraform outputs from {path}")
    with open(path) as f:
        return json.load(f)

def load_config() -> Dict[str, Any]:
    logger.info("Loading environment variables and Terraform outputs...")
    load_dotenv(ENV_PATH)
    tf_outputs = load_tf_outputs(TF_OUTPUTS_PATH)
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    logger.info(f"GCP Project ID: {gcp_project_id}")

    db_params = {
        "host": tf_outputs["db_host"]["value"],
        "dbname": os.getenv("PG_DATABASE", "postgres"),
        "user": tf_outputs["db_service_account_name"]["value"],
        "password": utils.get_secret(gcp_project_id, f"postgres-service-account-pwd--{ENV}"),
        "port": os.getenv("PG_PORT", "5432"),
    }

    logger.debug(f"Database parameters loaded: host={db_params['host']}, db={db_params['dbname']}")
    return {"tf_outputs": tf_outputs, "db_params": db_params, "gcp_project_id": gcp_project_id}

def refresh_strava_token(gcp_project_id: str) -> Dict[str, Any]:
    token = json.loads(utils.get_secret(gcp_project_id, f"strava-access-token--{ENV}"))
    expires_at = token.get("expires_at", 0)
    trace_id = f"strava-token-{int(time.time())}"

    if expires_at < time.time():
        logger.info(f"[{trace_id}] Token expired at {expires_at}, refreshing...")
        token = api_secrets.refresh_access_token(
            utils.get_secret(gcp_project_id, f"strava-client-id--{ENV}"),
            utils.get_secret(gcp_project_id, f"strava-client-secret--{ENV}"),
            utils.get_secret(gcp_project_id, f"strava-refresh-token--{ENV}")
        )
        refresh_token = token.pop("refresh_token")
        for name, value in {
            f"strava-access-token--{ENV}": json.dumps(token),
            f"strava-refresh-token--{ENV}": refresh_token,
        }.items():
            utils.put_secret(gcp_project_id, name, value)
            logger.info(f"[{trace_id}] Updated secret: {name}")
    else:
        logger.info(f"[{trace_id}] Token is still valid.")

    return token

def fetch_pubsub_messages(project_id: str, subscription_id: str, max_messages: int = 50):
    trace_id = f"pubsub-fetch-{int(time.time())}"
    logger.info(f"[{trace_id}] Fetching up to {max_messages} messages from subscription {subscription_id}")
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    
    try:
        response = subscriber.pull(request={"subscription": subscription_path, "max_messages": max_messages})
        messages = response.received_messages
        logger.info(f"[{trace_id}] Fetched {len(messages)} messages")
        return subscriber, subscription_path, messages
    except Exception as e:
        logger.exception(f"[{trace_id}] Failed to fetch messages: {e}")
        raise

def requests_get_with_retry(url: str, headers: Dict[str, str], params: Dict[str, Any], trace_id: str) -> Dict[str, Any]:
    for attempt in range(1, MAX_REQUEST_RETRIES + 1):
        try:
            logger.debug(f"[{trace_id}] Attempt {attempt} GET {url} with params {params}")
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            metrics["requests_success"] += 1
            return response.json()
        except requests.RequestException as e:
            wait_time = BACKOFF_FACTOR ** (attempt - 1)
            logger.warning(f"[{trace_id}] GET request attempt {attempt} failed: {e}. Retrying in {wait_time}s")
            metrics["requests_failed"] += 1
            time.sleep(wait_time)
    raise RuntimeError(f"[{trace_id}] Failed to fetch {url} after {MAX_REQUEST_RETRIES} attempts.")

def fetch_segments_from_strava(coordinates: List[float], access_token: str, trace_id: str) -> Dict[str, Any]:
    url = "https://www.strava.com/api/v3/segments/explore"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    bounds = ",".join(str(coord) for coord in coordinates)
    params = {"bounds": bounds, "activity_type": "riding"}
    
    logger.info(f"[{trace_id}] Fetching Strava segments for bounds {bounds}")
    segment_data = requests_get_with_retry(url, headers, params, trace_id)
    segment_data["time_fetched"] = int(time.time())
    logger.info(f"[{trace_id}] Fetched {len(segment_data.get('segments', []))} segments")
    return segment_data

def update_bounding_box_status(db_params: Dict[str, Any], bbox_id: int, status: str = "fetched", trace_id: str = None):
    trace_id = trace_id or f"bbox-update-{bbox_id}-{int(time.time())}"
    logger.info(f"[{trace_id}] Updating bounding box {bbox_id} status to {status}")
    query = sql.SQL("UPDATE {schema}.{table} SET status = %s WHERE id = %s").format(
        schema=sql.Identifier("public"), table=sql.Identifier("bounding_boxes")
    )
    try:
        with psycopg2.connect(**db_params) as conn:
            with conn.cursor() as cur:
                cur.execute(query, (status, bbox_id))
                conn.commit()
        logger.info(f"[{trace_id}] Successfully updated bounding box {bbox_id}")
    except Exception as e:
        logger.exception(f"[{trace_id}] Failed to update bounding box {bbox_id}: {e}")
        raise


def handle_message(message_data: Dict[str, Any], trace_id: str):
    config = load_config()
    tf_outputs = config["tf_outputs"]
    db_params = config["db_params"]
    gcp_project_id = config["gcp_project_id"]

    strava_token = refresh_strava_token(gcp_project_id)
    access_token = strava_token["access_token"]

    coordinates = [message_data[key] for key in ["sw_latitude", "sw_longitude", "ne_latitude", "ne_longitude"]]
    logger.debug(f"[{trace_id}] Coordinates: {coordinates}")

    segment_data = fetch_segments_from_strava(coordinates, access_token, trace_id)

    file_name = f"[{','.join(map(str, coordinates))}]__{segment_data['time_fetched']}.json"
    utils.upload_blob_from_string(tf_outputs["bucket_name"]["value"], json.dumps(segment_data), file_name)
    logger.info(f"[{trace_id}] Uploaded segment data to {file_name}")

    update_bounding_box_status(db_params, message_data["id"], "fetched", trace_id)
    logger.info(f"[{trace_id}] Successfully processed bounding box {message_data['id']}")



def process_pubsub_event(event, context):
    """Entry point for Google Cloud Function (Pub/Sub trigger)."""
    logger.info("Pub/Sub event received")
    try:
        message_data = json.loads(base64.b64decode(event["data"]).decode("utf-8"))
        trace_id = message_data.get("id") or str(uuid.uuid4())
        handle_message(message_data, trace_id)
        logger.info(f"[{trace_id}] Pub/Sub message processed successfully")
    except Exception as e:
        logger.exception(f"Failed to process Pub/Sub message: {e}")
        raise
