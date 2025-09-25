import os
import json
import webbrowser
import requests
import utils
from dotenv import load_dotenv
from google.cloud import secretmanager

def get_auth_code(client_id: str,
                  redirect_uri: str,
                  auth_code_scope: str) -> str:
    """Obtains an authorisation code from Strava

    Args:
        client_id (str): Strava API Client ID
        redirect_uri (str): Callback URL of your Strava API App
        auth_code_scope (str): Authorisation Code Scopes

    Returns:
        str: Authorisation Code
    """
     
    auth_url = requests.Request(
        "GET",
        "http://www.strava.com/oauth/authorize",
        params = {
            "client_id": client_id,
            "response_type": "code",
            "redirect_uri": redirect_uri,
            "approval_prompt": "auto",
            "scope": auth_code_scope
        }
    ).prepare().url()

    print("Authenticate with Strava in Browser")
    webbrowser.open(auth_url)

    auth_code = input(
        "After logging in, paste the 'code' from the redirected URL here: ").strip()
    
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
        print(f"Request failed: {e}")

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
        "refresh_token": refresh_token
    }

    try:
        response = requests.post(token_url, data=payload)
        response.raise_for_status()
    except requests.exceptions.HTTPError as e:
        print(f"Request failed: {e}")

    data = response.json()
    return data

    
if __name__ == "__main__":

    """Step 1: Setup"""
    repo_root = os.path.abspath(
        os.path.join(os.path.dirname(__file__), ".."))
    env_file = os.path.join(repo_root, ".env.dev")

    load_dotenv(env_file)

    """Step 2: Refresh Token"""
    access_token = refresh_access_token(
        os.getenv("CLIENT_ID"),
        os.getenv("CLIENT_SECRET"),
        os.getenv("REFRESH_TOKEN")
    )

    refresh_token = access_token.pop("refresh_token")

    """Step 3: Push to Secret Manager"""
    utils.put_secret(
        os.getenv('GCP_PROJECT_ID'),
        "strava-access-token", 
        json.dumps(access_token))
    
    utils.put_secret(
        os.getenv('GCP_PROJECT_ID'),
        "strava-refresh-token", refresh_token)
    
