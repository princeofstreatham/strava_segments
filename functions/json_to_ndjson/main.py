import os
import json
import base64
from typing import Optional

import utils
from logging_config import set_trace_id, get_logger


# ============================================================
# ===============   Setup, Vars and Constants   ==============
# ============================================================
logger = get_logger(__name__)

# ============================================================
# ===============   Functions   ==============
# ============================================================

def convert_json_to_ndjson(data: dict) -> Optional[str]:
    """Converts JSON object with a list of items into NDJSON string

    Args:
        data (dict): JSON object serialised as a dict

    Returns:
        Optional[str]: NDJSON string, or None if no segments
    """
    segments = data.get("segments",[])
    if not segments:
        logger.warning(
            f"No segments found - skipping"
        )
        return None
    time_fetched = data.get("time_fetched")

    ndjson_lines = []
    for seg in segments:
        seg_with_meta = seg.copy()
        if time_fetched is not None:
            seg_with_meta["time_fetched"] = time_fetched
        ndjson_lines.append(
            json.dumps(seg_with_meta, separators=(",",":")))
    
    ndjson = "\n".join(ndjson_lines)
    logger.info(f"{len(segments)} segments converted to NDJSON")
    return ndjson

# ============================================================
# ===============   Main Logic  ==============
# ============================================================
def main(event, context):
    """Cloud Function triggered by Pub/Sub event"""
    try:
        pubsub_message = event.get("data")
        if not pubsub_message:
            logger.error("No data in Pub/Sub message")
            return
            
        decoded_bytes = base64.b64decode(pubsub_message)
        message_dict = json.loads(decoded_bytes.decode("utf-8"))
        blob_name = message_dict.get("blob_name")
        bucket_name = message_dict.get("bucket_name") or os.getenv("BUCKET_NAME", "segment_hunter__dev")

        if not blob_name or not bucket_name:
            logger.error("Missing bucket_name or blob_name in message")
            return
        
        set_trace_id(blob_name)

        json_blob = utils.download_json_blob(bucket_name, blob_name)
        nd_json = convert_json_to_ndjson(json_blob)
        if nd_json is not None:
            utils.upload_blob_from_string(bucket_name, nd_json, os.path.join(
                "explored_segments_ndjson", blob_name))

    except Exception as e:
            logger.exception(f"Unhandled error in Cloud Function: {e}")
            raise
    

