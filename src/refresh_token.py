import requests
import os
import utils
from dotenv import load_dotenv, set_key
from google.cloud import secretmanager

SPOTIFY_TOKEN_URL = "https://accounts.spotify.com/api/token"

def get_access_token(refresh_token, client_id, client_secret):
    payload = {"grant_type": "refresh_token", "refresh_token": refresh_token}
    auth = (client_id, client_secret)
    response = requests.post(SPOTIFY_TOKEN_URL, data=payload, auth=auth)
    response.raise_for_status()
    return response.json()["access_token"]

# Stage 1: Setup
if __name__ == "__main__":

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    env_file = os.path.join(repo_root, ".env")

    load_dotenv(env_file)
    project_id = os.getenv("GCP_PROJECT_ID")
    if not project_id:
        raise EnvironmentError("GCP_PROJECT_ID not set in environment")

    spotify_secrets = {
        "spotify_client_id":"spotify-client-id",
        "spotify_client_secret":"spotify-client-secret",
        "spotify_refresh_token":"spotify-refresh-token"
    }

    # Step 2: Retrieve Spotify Secrets
    for key, secret_name in spotify_secrets.items():
        spotify_secrets[key] = utils.get_secret(project_id, secret_name)


    # Step 3: Retrieve Token
    try:
        access_token = get_access_token(
            spotify_secrets['spotify_refresh_token'],
            spotify_secrets['spotify_client_id'],
            spotify_secrets['spotify_client_secret']
        )
        print(access_token)
        os.environ['SPOTIFY_ACCESS_TOKEN'] = access_token
        set_key(env_file,"SPOTIFY_ACCESS_TOKEN", access_token)
    except requests.RequestException as e:
        print(f"HTTP/Network Error occurred whilst retrieving access token: {e}")