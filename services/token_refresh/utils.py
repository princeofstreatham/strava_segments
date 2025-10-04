import logging

from google.cloud import secretmanager

logger = logging.getLogger(__name__)


def get_secret(project_id: str, secret_name: str) -> str:
    """Returns latest version of a secret stored in Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    secret_url = f"projects/{project_id}/secrets/{secret_name}/versions/latest"
    response = client.access_secret_version(name=secret_url)
    secret = response.payload.data.decode("UTF-8")
    logger.info(f"Retrieved secret '{secret_name}' from project '{project_id}'")
    return secret


def put_secret(project_id: str, secret_name: str, secret_value: str) -> None:
    """Creates a new version of a secret stored in Google Secret Manager."""
    client = secretmanager.SecretManagerServiceClient()
    parent = client.secret_path(project_id, secret_name)
    payload = secret_value.encode("UTF-8")
    response = client.add_secret_version(
        request={"parent": parent, "payload": {"data": payload}}
    )
    logger.info(f"Added secret version: {response.name}")
