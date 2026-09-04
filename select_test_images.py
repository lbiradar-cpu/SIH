import os
import shutil
import random

source_folder = "ocr_images"
dest_folder = "test_images"
MAX_IMAGES = 10  # <-- change this number, or set to None to copy all

os.makedirs(dest_folder, exist_ok=True)

for f in os.listdir(dest_folder):
    file_path = os.path.join(dest_folder, f)
    if os.path.isfile(file_path):
        os.remove(file_path)

all_images = [
    f for f in os.listdir(source_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]

if MAX_IMAGES is None or len(all_images) <= MAX_IMAGES:
    selected = all_images
else:
    selected = random.sample(all_images, MAX_IMAGES)

for filename in selected:
    shutil.copy2(os.path.join(source_folder, filename), os.path.join(dest_folder, filename))
    print(f"Copied: {filename}")

print(f"\nDone! {len(selected)} images copied to '{dest_folder}'.")