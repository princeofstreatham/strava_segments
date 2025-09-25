"""Module used to generate a CSV of bounding box coordinates"""

import os
import numpy as np
import pandas as pd
import utils


def split_bbox(
    lat_min: float,
    lon_min: float,
    lat_max: float,
    lon_max: float,
    n_lat: int,
    n_lon: int,
):
    """Splits a bounding box into n_lat*n_lon sub-boxes

    Args:
        lat_min (float): SW Latitude (bottom corner) of bounding box
        lon_min (float): SW Longitude (bottom corner) of bounding box
        lat_max (float): NE Latitude (top corner) of bounding box
        lon_max (float): NE Longitude (top corner) of bounding box
        n_lat (int):
        n_lon (int):

    Returns:
        list: List of bouning box coordinates
    """
    lats = np.linspace(lat_min, lat_max, n_lat + 1)
    lons = np.linspace(lon_min, lon_max, n_lon + 1)

    bounding_boxes = []
    for i in range(n_lat):
        for j in range(n_lon):
            bounding_boxes.append([lons[j], lats[i], lons[j + 1], lats[i + 1]])
    return bounding_boxes


if __name__ == "__main__":

    """Step 1: Setup"""

    repo_root = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
    data_dir = os.path.join(repo_root, "data")

    coordinates = {
        "sw_latitude": 51.45,
        "sw_longitude": -1.15,
        "ne_latitude": 51.75,
        "ne_longitude": -0.85,
    }

    """Step 2: Obtain BBOX Coordinates"""
    bbox_coordinates = split_bbox(
        coordinates["sw_latitude"],
        coordinates["sw_longitude"],
        coordinates["ne_latitude"],
        coordinates["ne_longitude"],
        30,
        30,
    )

    coordinates_df = pd.DataFrame(bbox_coordinates, columns=coordinates.keys())

    coordinates_df["status"] = "pending"

    """Step 3: Output"""
    file_name = "bounding_boxes.csv"
    file_path = os.path.join(data_dir, file_name)

    coordinates_df.to_csv(file_path, index=False)

    gcp_resources = utils.load_json(
        os.path.join(repo_root, "terraform", "terraform_outputs.json")
    )
    gcp_bucket_name = gcp_resources["bucket_name"]["value"]

    utils.upload_blob(gcp_bucket_name, file_path, file_name)
