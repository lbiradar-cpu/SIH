import os
import cv2
import numpy as np
from paddleocr import PaddleOCR
from crop import warp_region

test_folder = "test_images"
MAX_IMAGES = None  # <-- set a number to limit, or None to process all in test_images
CONFIDENCE_THRESHOLD = 0.5

ocr = PaddleOCR(
    lang="en",
    use_textline_orientation=True,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)

os.makedirs("output", exist_ok=True)
os.makedirs("output/cropped_regions", exist_ok=True)

all_files = sorted([
    f for f in os.listdir(test_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
])
if MAX_IMAGES is not None:
    all_files = all_files[:MAX_IMAGES]

print(f"Processing {len(all_files)} image(s).")

for filename in all_files:
    image_path = os.path.join(test_folder, filename)
    image = cv2.imread(image_path)
    if image is None:
        print(f"Skipping {filename} (couldn't read)")
        continue

    name = os.path.splitext(filename)[0]
    annotated_image = image.copy()
    result = ocr.predict(image_path)

    found_any = False
    for res in result:
        boxes = res["rec_polys"]
        texts = res["rec_texts"]
        scores = res["rec_scores"]

        for i, (box, text, score) in enumerate(zip(boxes, texts, scores)):
            if score < CONFIDENCE_THRESHOLD:
                continue
            found_any = True
            points = [(int(p[0]), int(p[1])) for p in box]

            for j in range(4):
                cv2.line(annotated_image, points[j], points[(j + 1) % 4], (0, 255, 0), 2)
            label = f"{text[:15]} ({score:.2f})"
            x, y = points[0]
            cv2.putText(annotated_image, label, (x, max(y - 5, 0)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, (0, 0, 255), 1)

            warped = warp_region(image, box)
            cv2.imwrite(f"output/cropped_regions/{name}_region_{i}.jpg", warped)
            print(f"{filename}: '{text}' (confidence: {score:.2f})")

    if not found_any:
        print(f"{filename}: No text regions above threshold detected.")

    cv2.imwrite(f"output/{name}_detection.jpg", annotated_image)

print("\nAll done!")