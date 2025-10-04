from google.cloud import pubsub_v1
import json

project_id = "segment-hunter-472920"
topic_name = "segment-explorer-ndjsonconvert--dev"

publisher = pubsub_v1.PublisherClient()
topic_path = publisher.topic_path(project_id, topic_name)

# Example payload
message = {
    "blob_name": "[51.45,-0.8599999999999999,51.46,-0.85]__1759170409.json",
    "bucket_name": "segment_hunter__dev"
}

# Publish
future = publisher.publish(topic_path, json.dumps(message).encode("utf-8"))
print(f"Published message ID: {future.result()}")