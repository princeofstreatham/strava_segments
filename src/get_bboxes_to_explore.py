import os
import sys
import json
import time
import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Dict, Any, List

import psycopg2
from psycopg2 import sql
from dotenv import load_dotenv
from google.cloud import pubsub_v1
import colorlog
from pythonjsonlogger import jsonlogger

import utils
import api_secrets

logger_name = os.path.basename(__file__)
logger = logging.getLogger(logger_name)
logger.setLevel(logging.INFO)

# Console logging
stdout_handler = colorlog.StreamHandler(stream=sys.stdout)
stdout_fmt = colorlog.ColoredFormatter(
    "%(name)s: %(white)s%(asctime)s%(reset)s | "
    "%(log_color)s%(levelname)s%(reset)s | "
    "%(blue)s%(filename)s:%(lineno)s%(reset)s | "
    "%(process)d >>> %(log_color)s%(message)s%(reset)s"
)
stdout_handler.setFormatter(stdout_fmt)
logger.addHandler(stdout_handler)

# File logging
file_handler = TimedRotatingFileHandler(f"{logger_name}_logs.txt", backupCount=5, when="midnight")
json_fmt = jsonlogger.JsonFormatter(
    "%(name)s %(asctime)s %(levelname)s %(filename)s %(lineno)s %(process)d %(message)s",
    rename_fields={"levelname": "severity", "asctime": "timestamp"},
    datefmt="%Y-%m-%dT%H:%M:%SZ",
)
file_handler.setFormatter(json_fmt)
logger.addHandler(file_handler)

ENV = "dev"
REPO_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
ENV_PATH = os.path.join(REPO_ROOT, f".env.{ENV}")
TF_OUTPUTS_PATH = os.path.join(REPO_ROOT, "terraform", f"terraform_outputs_{ENV}.json")
MAX_PUBSUB_RETRIES = 3
HTTP_BACKOFF_FACTOR = 4

def load_tf_outputs(path: str) -> Dict[str, Any]:
    logger.debug(f"Loading Terraform outputs from {path}")
    with open(path) as f:
        outputs = json.load(f)
    logger.info(f"Loaded Terraform outputs with keys: {list(outputs.keys())}")
    return outputs

def load_config() -> Dict[str, Any]:
    logger.info("Loading environment variables and configuration...")
    load_dotenv(ENV_PATH)
    tf_outputs = load_tf_outputs(TF_OUTPUTS_PATH)
    gcp_project_id = os.getenv("GCP_PROJECT_ID")
    logger.info(f"GCP project ID: {gcp_project_id}")

    db_params = {
        "host": tf_outputs["db_host"]["value"],
        "dbname": os.getenv("PG_DATABASE", "postgres"),
        "user": tf_outputs["db_service_account_name"]["value"],
        "password": utils.get_secret(gcp_project_id, f"postgres-service-account-pwd--{ENV}"),
        "port": os.getenv("PG_PORT", "5432"),
    }
    logger.debug(f"Database params: host={db_params['host']}, dbname={db_params['dbname']}")
    return {"tf_outputs": tf_outputs, "db_params": db_params, "gcp_project_id": gcp_project_id}

def refresh_strava_token(gcp_project_id: str) -> Dict[str, Any]:
    logger.info("Checking Strava access token...")
    token = json.loads(utils.get_secret(gcp_project_id, f"strava-access-token--{ENV}"))
    if token.get("expires_at", 0) < time.time():
        logger.info(f"Strava token expired at {token.get('expires_at')}. Refreshing...")
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
            logger.info(f"Updated secret: {name}")
    else:
        logger.info("Strava token is still valid.")
    return token

def fetch_pending_bboxes(db_params: Dict[str, Any], schema="public", table="bounding_boxes") -> List[Dict[str, Any]]:
    logger.info(f"Fetching pending bounding boxes from {schema}.{table}...")
    query = sql.SQL("SELECT * FROM {schema}.{table} WHERE status = %s").format(
        schema=sql.Identifier(schema), table=sql.Identifier(table)
    )
    with psycopg2.connect(**db_params) as conn:
        with conn.cursor() as cur:
            cur.execute(query, ("pending",))
            rows = cur.fetchall()
            columns = [desc[0] for desc in cur.description]
            bbox_list = [dict(zip(columns, row)) for row in rows]
    logger.info(f"Fetched {len(bbox_list)} pending bounding boxes")
    return bbox_list

def publish_message_with_retry(publisher, topic_path: str, message_bytes: bytes, attributes: Dict[str, str]):
    for attempt in range(1, MAX_PUBSUB_RETRIES + 1):
        try:
            future = publisher.publish(topic_path, message_bytes, **attributes)
            message_id = future.result()
            logger.info(f"Published message ID: {message_id} (trace_id={attributes.get('trace_id')})")
            return message_id
        except Exception as e:
            wait_time = HTTP_BACKOFF_FACTOR ** (attempt - 1)
            logger.warning(f"Pub/Sub publish attempt {attempt} failed: {e}. Retrying in {wait_time}s.")
            time.sleep(wait_time)
    raise RuntimeError("Failed to publish message to Pub/Sub after retries.")

def publish_bboxes_to_pubsub(gcp_project_id: str, tf_outputs: Dict[str, Any], bboxes: List[Dict[str, Any]]):
    logger.info(f"Publishing {len(bboxes)} bounding boxes to Pub/Sub...")
    publisher = pubsub_v1.PublisherClient()
    topic_path = publisher.topic_path(gcp_project_id, tf_outputs['pubsub_topic_path']['value'])
    for bbox in bboxes:
        trace_id = f"{bbox.get('id', 'unknown')}-{int(time.time())}"
        try:
            message_bytes = json.dumps(bbox).encode("utf-8")
            attributes = {"env": ENV, "trace_id": trace_id}
            publish_message_with_retry(publisher, topic_path, message_bytes, attributes)
            logger.info(f"[{trace_id}] Successfully published bbox ID {bbox.get('id')}")
        except Exception as e:
            logger.exception(f"[{trace_id}] Failed to publish bbox ID {bbox.get('id')} to Pub/Sub: {e}")

def main():
    logger.info("Starting main execution...")
    try:
        config = load_config()
        tf_outputs = config["tf_outputs"]
        db_params = config["db_params"]
        gcp_project_id = config["gcp_project_id"]

        refresh_strava_token(gcp_project_id)

        pending_bboxes = fetch_pending_bboxes(db_params)
        # if pending_bboxes:
        #     publish_bboxes_to_pubsub(gcp_project_id, tf_outputs, pending_bboxes)
        # else:
        #     logger.info("No pending bounding boxes to publish.")

    except Exception as e:
        logger.exception(f"Fatal error in main execution: {e}")
    finally:
        logger.info("Main execution finished.")

if __name__ == "__main__":
    main()