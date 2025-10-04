#!/bin/bash
#Fail Fast
set -e

if [ $# -lt 2 ]; then
  echo "Usage: $0 <GCP_PROJECT_ID> <ENV>"
  exit 1
fi

GCP_PROJECT_ID=$1
ENV=$2

docker build \
  --build-arg GCP_PROJECT_ID="$GCP_PROJECT_ID" \
  --build-arg ENV="$ENV" \
  -t segment_hunter/token_refresh:latest \
  -t segment_hunter/token_refresh:$(git rev-parse --short HEAD) \
  .