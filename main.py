import cv2
import os

input_folder = "ocr_images"
output_folder = "output"

os.makedirs(output_folder, exist_ok=True)

TARGET_WIDTH = 1200  # only width is fixed; height scales to preserve aspect ratio

for filename in os.listdir(input_folder):
    if not filename.lower().endswith((".jpg", ".jpeg", ".png")):
        continue

    path = os.path.join(input_folder, filename)
    image = cv2.imread(path)

    if image is None:
        print(f"Skipping {filename} (couldn't read)")
        continue

    name = os.path.splitext(filename)[0]

    # Resize while preserving aspect ratio — avoids stretching text
    h, w = image.shape[:2]
    scale = TARGET_WIDTH / w
    resized = cv2.resize(image, (TARGET_WIDTH, int(h * scale)), interpolation=cv2.INTER_CUBIC)

    # 1. Original (resized, aspect-preserved)
    cv2.imwrite(f"{output_folder}/{name}_original.jpg", resized)

    # 2. Grayscale
    gray = cv2.cvtColor(resized, cv2.COLOR_BGR2GRAY)
    cv2.imwrite(f"{output_folder}/{name}_gray.jpg", gray)

    # 3. Enhanced — CLAHE for local contrast + mild unsharp mask for text edge crispness
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    contrast_boosted = clahe.apply(gray)

    blur = cv2.GaussianBlur(contrast_boosted, (0, 0), sigmaX=3)
    enhanced = cv2.addWeighted(contrast_boosted, 1.5, blur, -0.5, 0)  # unsharp mask
    cv2.imwrite(f"{output_folder}/{name}_enhanced.jpg", enhanced)

    # 4. Threshold — bilateral filter preserves edges better than Gaussian blur,
    #    larger block size + gentler C avoids destroying thin text strokes
    denoised = cv2.bilateralFilter(enhanced, d=9, sigmaColor=75, sigmaSpace=75)
    thresholded = cv2.adaptiveThreshold(
        denoised, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=25,   # larger block = smoother local threshold, less speckling
        C=10            # higher C = less aggressive binarization, keeps faint strokes
    )
    cv2.imwrite(f"{output_folder}/{name}_threshold.jpg", thresholded)

    print(f"Processed {filename}")

print("All done!")