import os
import cv2
import csv
from paddleocr import PaddleOCR
from crop import warp_region

ocr = PaddleOCR(
    lang="en",
    use_textline_orientation=True,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)

source_folder = "ocr_images"
crop_output_root = "output/final_crops"
results_csv = "final_ocr_results.csv"
CONFIDENCE_THRESHOLD = 0.5
MAX_IMAGES = 15  # <-- change this number, or set to None to process ALL images

os.makedirs(crop_output_root, exist_ok=True)


def run_ocr_and_get_scores(image_path):
    result = ocr.predict(image_path)
    scores, texts = [], []
    for res in result:
        scores.extend(res["rec_scores"])
        texts.extend(res["rec_texts"])
    return texts, scores


def process_image(image_path, name):
    image = cv2.imread(image_path)
    if image is None:
        return None, 0.0, 0

    image_crop_folder = os.path.join(crop_output_root, name)
    os.makedirs(image_crop_folder, exist_ok=True)

    result = ocr.predict(image_path)
    all_texts, all_scores = [], []

    for res in result:
        boxes = res["rec_polys"]
        scores = res["rec_scores"]
        for i, (box, score) in enumerate(zip(boxes, scores)):
            if score < CONFIDENCE_THRESHOLD:
                continue
            warped = warp_region(image, box)
            crop_path = os.path.join(image_crop_folder, f"region_{i}.jpg")
            cv2.imwrite(crop_path, warped)
            texts, scores_ = run_ocr_and_get_scores(crop_path)
            all_texts.extend(texts)
            all_scores.extend(scores_)

    combined_text = " ".join(all_texts)
    avg_confidence = sum(all_scores) / len(all_scores) if all_scores else 0.0
    return combined_text, avg_confidence, len(all_scores)


def main():
    all_files = sorted([
        f for f in os.listdir(source_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])
    if MAX_IMAGES is not None:
        all_files = all_files[:MAX_IMAGES]

    total = len(all_files)
    print(f"Processing {total} image(s).\n")

    rows = []
    for idx, filename in enumerate(all_files, start=1):
        image_path = os.path.join(source_folder, filename)
        name = os.path.splitext(filename)[0]

        try:
            text, avg_conf, num_regions = process_image(image_path, name)
            if text is None:
                print(f"[{idx}/{total}] Skipping {filename} (couldn't read image)")
                continue

            rows.append({
                "filename": filename,
                "extracted_text": text,
                "avg_confidence": round(avg_conf, 4),
                "num_regions": num_regions
            })
            print(f"[{idx}/{total}] {filename} -> {num_regions} regions, avg confidence: {avg_conf:.4f}")

        except Exception as e:
            print(f"[{idx}/{total}] ERROR processing {filename}: {e}")
            continue

        if idx % 20 == 0:
            with open(results_csv, "w", newline="", encoding="utf-8") as f:
                writer = csv.DictWriter(f, fieldnames=["filename", "extracted_text", "avg_confidence", "num_regions"])
                writer.writeheader()
                writer.writerows(rows)
            print(f"   (progress saved: {len(rows)} images so far)")

    with open(results_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=["filename", "extracted_text", "avg_confidence", "num_regions"])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Processed {len(rows)}/{total} images. Results saved to {results_csv}")


if __name__ == "__main__":
    main()