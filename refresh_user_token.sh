#!/usr/bin/env bash

# Set your variables
set -o allexport
source .env
set +o allexport

TOKEN_RESPONSE=$(curl -X POST https://www.strava.com/api/v3/oauth/token \
  -d client_id=$CLIENT_ID \
  -d client_secret=$CLIENT_SECRET \
  -d grant_type=refresh_token \
  -d refresh_token=$REFRESH_TOKEN)

ACCESS_TOKEN=$(echo "$TOKEN_RESPONSE" | jq -r '.access_token')

echo "Access Token: $ACCESS_TOKEN"


