#!/usr/bin/env bash

# Set your variables
set -o allexport
source .env
set +o allexport


# Build the URL
AUTH_URL="http://www.strava.com/oauth/authorize?client_id=${CLIENT_ID}&response_type=code&redirect_uri=http://localhost:8080&approval_prompt=auto&scope=${TOKEN_SCOPES}"

# Open in Browser
open "$AUTH_URL"

read -p "After logging in, paste the 'code' from the redirected URL here: " AUTH_CODE

TOKEN_RESPONSE=$(curl -X POST https://www.strava.com/api/v3/oauth/token \
  -d client_id=$CLIENT_ID \
  -d client_secret=$CLIENT_SECRET \
  -d code=$AUTH_CODE \
  -d grant_type=authorization_code)
  
# Extract access token (requires jq)
ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')
REFRESH_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.refresh_token')

echo "Access Token: $ACCESS_TOKEN"
echo "Refresh Token: $REFRESH_TOKEN"