"""
This script sends every image in the /dataset folder to your running API,
one at a time, and prints the result. This is how you "connect the dataset
to the API" -- it's just a loop that reads files and sends them over HTTP.

Before running this:
  1. Make sure app.py is already running (python app.py) in another terminal.
  2. Put some product label photos inside the dataset/ folder.

Run with: python test_with_dataset.py
"""

import os
import requests

API_URL = "http://localhost:5000/scan"
DATASET_FOLDER = "dataset"

# Get list of image files in the dataset folder
image_files = [
    f for f in os.listdir(DATASET_FOLDER)
    if f.lower().endswith(('.jpg', '.jpeg', '.png'))
]

if not image_files:
    print(f"No images found in '{DATASET_FOLDER}/'. Add some product label photos first.")
else:
    print(f"Found {len(image_files)} image(s). Sending each to the API...\n")

    for filename in image_files:
        filepath = os.path.join(DATASET_FOLDER, filename)
        with open(filepath, 'rb') as img:
            response = requests.post(API_URL, files={'image': img})

        print(f"--- {filename} ---")
        if response.status_code == 200:
            result = response.json()
            print("Status:", result["overall_status"])
            print("Checks:", result["checks"])
        else:
            print("Error:", response.text)
        print()

    print("Done. Check 'GET /history' on the API to see everything saved so far.")
