import json
import os
import time
import webbrowser
from typing import Any, Dict

import requests
from google.cloud.logging_v2.handlers import CloudLoggingHandler

import utils
from logging_config import get_logger

logger = get_logger(__name__)

ENV = os.getenv("ENV")
GCP_PROJECT_ID = os.getenv("GCP_PROJECT_ID", "segment-hunter-472920")

if not ENV:
    logger.error("Environment Variable 'env' must be set")
    raise EnvironmentError("Environment Variable 'env' must be set")


def get_auth_code(client_id: str, redirect_uri: str, auth_code_scope: str) -> str:
    """Obtains an authorisation code from Strava

    Args:
        client_id (str): Strava API Client ID
        redirect_uri (str): Callback URL of your Strava API App
        auth_code_scope (str): Authorisation Code Scopes

    Returns:
        str: Authorisation Code
    """

    auth_url = (
        requests.Request(
            "GET",
            "http://www.strava.com/oauth/authorize",
            params={
                "client_id": client_id,
                "response_type": "code",
                "redirect_uri": redirect_uri,
                "approval_prompt": "auto",
                "scope": auth_code_scope,
            },
        )
        .prepare()
        .url()
    )

    print("Authenticate with Strava in Browser")
    webbrowser.open(auth_url)

    auth_code = input(
        "After logging in, paste the 'code' from the redirected URL here: "
    ).strip()

    return auth_code


def get_access_token(client_id: str, client_secret: str, auth_code: str) -> dict:
    """Swaps an auth code to return an access and refresh token from the Strava API

    Args:
        client_id (str): Strava API Client ID
        client_secret (str): Strava API Client Secret
        auth_code (str): Strava API Authorisation Code

    Returns:
        dict: Dictionary containing keys "access_token" and "refresh_token"
    """
    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "code": auth_code,
        "grant_type": "authorization_code",
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Request failed: {e}")

    data = response.json()
    return data


def refresh_access_token(client_id: str, client_secret: str, refresh_token: str) -> str:
    """Refreshes an access token for the Strava API

    Args:
        client_id (str): Strava API Client ID
        client_secret (str): Strava API Client Secret
        refresh_token (str): Strava API Refresh Token

    Returns:
        str: Authorisation Code
    """
    token_url = "https://www.strava.com/api/v3/oauth/token"
    payload = {
        "client_id": client_id,
        "client_secret": client_secret,
        "grant_type": "refresh_token",
        "refresh_token": refresh_token,
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        logger.error(f"Request failed: {e}")

    data = response.json()
    return data


def refresh_strava_token(gcp_project_id: str) -> Dict[str, Any]:
    token = json.loads(utils.get_secret(gcp_project_id, f"strava-access-token--{ENV}"))
    expires_at = token.get("expires_at", 0)

    if expires_at < time.time():
        logger.info(f"Token expired at {expires_at}, refreshing...")
        token = refresh_access_token(
            utils.get_secret(gcp_project_id, f"strava-client-id--{ENV}"),
            utils.get_secret(gcp_project_id, f"strava-client-secret--{ENV}"),
            utils.get_secret(gcp_project_id, f"strava-refresh-token--{ENV}"),
        )
        refresh_token = token.pop("refresh_token")
        for name, value in {
            f"strava-access-token--{ENV}": json.dumps(token),
            f"strava-refresh-token--{ENV}": refresh_token,
        }.items():
            utils.put_secret(gcp_project_id, name, value)
            logger.info(f"Updated secret: {name}")
    else:
        logger.info(f"Token is still valid.")

    return token


if __name__ == "__main__":
    try:
        access_token = refresh_strava_token(GCP_PROJECT_ID)
        logger.info("Token refresh check completed successfully.")
    except Exception as e:
        logger.error(f"Uncaught exception raised: {e}")
        raise

    for handler in logger.handlers:
        if isinstance(handler, CloudLoggingHandler):
            handler.flush()
            handler.close()
