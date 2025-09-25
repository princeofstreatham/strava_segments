CREATE SCHEMA IF NOT EXISTS dev;

CREATE TABLE IF NOT EXISTS dev.bounding_boxes (
    id SERIAL PRIMARY KEY,
    sw_latitude FLOAT,
    sw_longitude FLOAT,
    ne_latitude FLOAT,
    ne_longitude FLOAT,
    status TEXT
);