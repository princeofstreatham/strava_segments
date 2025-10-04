from google.cloud import storage
import json
from logging_config import set_trace_id, get_logger

logger = get_logger(__name__)

def upload_blob_from_string(bucket_name: str, string_blob: str, destination_blob_name: str) -> None:
    """Uploads a string as a blob to a Google Cloud Storage bucket."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(string_blob, content_type="application/json")
    logger.info(f"Uploaded string blob to bucket '{bucket_name}' as '{destination_blob_name}'")

def download_json_blob(bucket_name: str, source_blob_name: str) -> dict:
    """Downloads a JSON blob from GCP and converts it to a dictionary."""
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(source_blob_name)

    try:
        json_text = blob.download_as_text()
    except Exception as e:
        logger.error(f"Failed to download {source_blob_name} from {bucket_name}: {e}")
        raise

    try:
        data = json.loads(json_text)
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse JSON from blob '{source_blob_name}'")
        raise

    logger.info(f"Downloaded '{source_blob_name}' from bucket '{bucket_name}' and converted to JSON")
    return data
