import os
from logging_config import get_logger, set_trace_id
import api_secrets

logger = get_logger(__name__)

def run():
    set_trace_id("token-refresh")
    try:
        token = api_secrets.refresh_strava_token(os.getenv("GCP_PROJECT_ID", "segment-hunter-472920"))
        logger.info(f"Refreshed Strava token successfully.")
    except Exception as e:
        logger.exception(f"Unhandled Exception: Failed to refresh Strava token: {e}")
        raise

if __name__ == "__main__":
    run()