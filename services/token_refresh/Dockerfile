FROM python:3.12-slim

# Prevent Python from writing .pyc files and buffering stdout
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

ARG ENV
ARG GCP_PROJECT_ID
ENV ENV=${ENV}
ENV GCP_PROJECT_ID=${GCP_PROJECT_ID}

CMD ["python","main.py" ]