import os
import sys
import json
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any, List

import requests
import psycopg2
import colorlog
from pythonjsonlogger import jsonlogger
from psycopg2 import sql
from dotenv import load_dotenv
from google.cloud import pubsub_v1

import utils
import api_secrets



logger = logging.getLogger(__file__)
logger.setLevel(logging.INFO)

# Stdout
stdout = colorlog.StreamHandler(stream=sys.stdout)
fmt = colorlog.ColoredFormatter(
    "%(name)s: %(white)s%(asctime)s%(reset)s | "
    "%(log_color)s%(levelname)s%(reset)s | "
    "%(blue)s%(filename)s:%(lineno)s%(reset)s | "
    "%(process)d >>> %(log_color)s%(message)s%(reset)s"
)

stdout.setFormatter(fmt)
logger.addHandler(stdout)

# File
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


def load_tf_outputs(path: str) -> Dict[str, Any]:
    with open(path) as f:
        return json.load(f)


def load_config() -> Dict[str, Any]:
    """Load environment variables and Terraform outputs."""
    load_dotenv(ENV_PATH)
    tf_outputs = load_tf_outputs(TF_OUTPUTS_PATH)
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    
    db_params = {
        "host": tf_outputs["db_host"]["value"],
        "dbname": os.getenv("PG_DATABASE", "postgres"),
        "user": tf_outputs["db_service_account_name"]["value"],
        "password": utils.get_secret(
            gcp_project_id, f"postgres-service-account-pwd--{ENV}"
        ),
        "port": os.getenv("PG_PORT", "5432"),
    }
    
    return {
        "tf_outputs": tf_outputs,
        "db_params": db_params,
        "gcp_project_id": gcp_project_id,
    }


def refresh_strava_token(gcp_project_id: str) -> Dict[str, Any]:
    """Refresh Strava access token if expired."""
    token = json.loads(utils.get_secret(gcp_project_id, f"strava-access-token--{ENV}"))
    expires_at = token.get("expires_at", 0)
    
    if expires_at < time.time():
        logger.info("Strava token expired. Refreshing...")
        token = api_secrets.refresh_access_token(
            utils.get_secret(gcp_project_id, "strava-client-id"),
            utils.get_secret(gcp_project_id, f"strava-client-secret--{ENV}"),
            utils.get_secret(gcp_project_id, f"strava-refresh-token--{ENV}")
        )
        
        # Update GCP secrets
        refresh_token = token.pop("refresh_token")
        secrets_to_update = {
        f"strava-access-token--{ENV}": json.dumps(token),
        f"strava-refresh-token--{ENV}": refresh_token,
    }
        for name, value in secrets_to_update.items():
            try:
                utils.put_secret(gcp_project_id, name, value)
                logger.info(f"Secret {name} updated successfully.")
            except Exception as e:
                logger.error(f"Failed to update secret {name}: {e}")
                raise
    
    return token


def fetch_pubsub_messages(project_id: str, subscription_id: str, max_messages: int = 50):
    subscriber = pubsub_v1.SubscriberClient()
    subscription_path = subscriber.subscription_path(project_id, subscription_id)
    
    response = subscriber.pull(
        request={
            "subscription": subscription_path,
            "max_messages": max_messages,
        }
    )
    
    return subscriber, subscription_path, response.received_messages


def requests_get_with_retry(url: str, headers: Dict[str, str], params: Dict[str, Any]) -> Dict[str, Any]:
    for attempt in range(1, MAX_REQUEST_RETRIES + 1):
        try:
            response = requests.get(url, headers=headers, params=params)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            wait_time = BACKOFF_FACTOR ** (attempt - 1)
            logger.warning(f"Request attempt {attempt} failed: {e}. Retrying in {wait_time}s.")
            time.sleep(wait_time)
    raise RuntimeError(f"Failed to fetch {url} after {MAX_REQUEST_RETRIES} attempts.")


def fetch_segments_from_strava(coordinates: List[float], access_token: str) -> Dict[str, Any]:
    url = "https://www.strava.com/api/v3/segments/explore"
    headers = {
        "accept": "application/json",
        "authorization": f"Bearer {access_token}",
    }
    bounds = ",".join(str(coord) for coord in coordinates)
    params = {"bounds": bounds, "activity_type": "riding"}
    
    segment_data = requests_get_with_retry(url, headers, params)
    segment_data["time_fetched"] = int(time.time())
    return segment_data


def update_bounding_box_status(db_params: Dict[str, Any], bbox_id: int, status: str = "fetched"):
    query = sql.SQL("""
        UPDATE {schema}.{table}
        SET status = %s
        WHERE id = %s
    """).format(schema=sql.Identifier("public"), table=sql.Identifier("bounding_boxes"))
    
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, (status, bbox_id))
            conn.commit()
    logger.info(f"Updated bounding box {bbox_id} status to {status}.")


def main():
    config = load_config()
    tf_outputs = config["tf_outputs"]
    db_params = config["db_params"]
    gcp_project_id = config["gcp_project_id"]
    
    strava_token = refresh_strava_token(gcp_project_id)
    access_token = strava_token["access_token"]
    
    subscription_id = tf_outputs['pubsub_topic_sub']['value']
    subscriber, subscription_path, messages = fetch_pubsub_messages(gcp_project_id, subscription_id)
    
    if not messages:
        logger.info("No messages available.")
        return
    
    for msg in messages:
        try:
            message_data = json.loads(msg.message.data.decode('utf-8'))
            coordinates = [
                message_data[key] for key in ['sw_latitude','sw_longitude','ne_latitude','ne_longitude']
            ]
            
            segment_data = fetch_segments_from_strava(coordinates, access_token)
            file_name = f"[{','.join(map(str, coordinates))}]__{segment_data['time_fetched']}.json"
            
            utils.upload_blob_from_string(tf_outputs["bucket_name"]["value"], json.dumps(segment_data), file_name)
            update_bounding_box_status(db_params, message_data['id'])
            
            # Acknowledge the message
            subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": [msg.ack_id],
                }
            )
            logger.info(f"Acknowledged message for bounding box {message_data['id']}.")
        
        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch Strava segments: {e}")
        except Exception as e:
            logger.exception(f"Unexpected error processing message {msg.message.message_id}: {e}")


if __name__ == "__main__":
    main()