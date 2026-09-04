import cv2
import os

input_folder = "images"
output_folder = "output"

os.makedirs(output_folder, exist_ok=True)

for filename in os.listdir(input_folder):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    path = os.path.join(input_folder, filename)
    image = cv2.imread(path)

    if image is None:
        print(f"Skipping {filename} (couldn't read)")
        continue

    name = os.path.splitext(filename)[0]  # e.g. "product (24)"

    # Resize once — everything downstream builds on this
    resized = cv2.resize(image, (1200, 900))

    # 1. Original (resized)
    cv2.imwrite(f"{output_folder}/{name}_original.jpg", resized)

    # 2. Grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(f"{output_folder}/{name}_gray.jpg", gray)

    # 3. Enhanced (contrast, via CLAHE)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    enhanced = clahe.apply(gray)
    cv2.imwrite(f"{output_folder}/{name}_enhanced.jpg", enhanced)

    # 4. Threshold (denoise first, then threshold — denoised itself isn't saved)
    denoised = cv2.GaussianBlur(enhanced, (3, 3), 0)
    thresholded = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        11, 2
    )
    cv2.imwrite(f"{output_folder}/{name}_threshold.jpg", thresholded)

    print(f"Processed {filename}")

print("All done!")