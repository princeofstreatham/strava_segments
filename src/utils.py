from google.cloud import secretmanager, storage
import json


def get_secret(project_id: str, secret_name: str):
    """Returns latest version of a secret stored in Google Secret MAnager

    Args:
        project_id (str): ID of your GCP project
        secret_name (str): Name of your secret

    Returns:
        str: secret
    """
    client = secretmanager.SecretManagerServiceClient()
    secret_url = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=secret_url)
    return response.payload.data.decode("UTF-8")


def put_secret(project_id: str, secret_name: str, secret_value: str):
    """Creates a new version of a secret stored in Google Secret Manager

    Args:
        project_id (str): GCP Project ID
        secret_name (str): Name of secret to upversion
        secret_value (str): Value to upversion secret to

    Returns:
        None
    """

    client = secretmanager.SecretManagerServiceClient()
    parent = client.secret_path(project_id, secret_name)
    payload = secret_value.encode("UTF-8")
    response = client.add_secret_version(
        request={"parent": parent, "payload": {"data": payload}}
    )
    print(f"Added secret version: {response.name}")


def upload_blob_from_path(bucket_name: str, source_file_path: str, destination_blob_name: str):
    """Uploads a file to a Google Cloud Storage bucket given a file path

    Args:
        bucket_name (str): GCS bucket name
        source_file_path (str): Path to your file
        destination_blob_name (str): Name of the blob to save in GCS

    Returns:
        None
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_filename(source_file_path)


def upload_blob_from_string(bucket_name: str, string_blob: str, destination_blob_name: str):
    """Uploads a file to a Google Cloud Storage bucket given a string

    Args:
        bucket_name (str): GCS bucket name
        string_blob (str): String representation of your blob
        destination_blob_name (str): Name of the blob to save in GCS

    Returns:
        None
    """
    storage_client = storage.Client()
    bucket = storage_client.bucket(bucket_name)
    blob = bucket.blob(destination_blob_name)
    blob.upload_from_string(string_blob, content_type="application/json")


def load_json(file_path: str):
    """Load a JSON file as a dictionary

    Args:
        file_path (str): Path to JSON file

    Returns:
        dict: JSON object serialized as Python dict
    """
    with open(file_path) as f:
        outputs = json.load(f)
    return outputs
