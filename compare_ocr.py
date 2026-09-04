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

test_folder = "test_images"
crop_output_root = "output/cropped_regions_by_image"
results_csv = "comparison_results.csv"
CONFIDENCE_THRESHOLD = 0.5
MAX_IMAGES = None  # <-- set a number to limit, or None to process all in test_images

os.makedirs(crop_output_root, exist_ok=True)


def run_ocr_and_get_scores(image_path):
    result = ocr.predict(image_path)
    scores, texts = [], []
    for res in result:
        scores.extend(res["rec_scores"])
        texts.extend(res["rec_texts"])
    return texts, scores


def main():
    all_files = sorted([
        f for f in os.listdir(test_folder)
        if f.lower().endswith((".jpg", ".jpeg", ".png"))
    ])
    if MAX_IMAGES is not None:
        all_files = all_files[:MAX_IMAGES]

    print(f"Processing {len(all_files)} image(s).")
    rows = []

    for filename in all_files:
        image_path = os.path.join(test_folder, filename)
        image = cv2.imread(image_path)
        if image is None:
            print(f"Skipping {filename} (couldn't read)")
            continue

        name = os.path.splitext(filename)[0]
        print(f"\n--- {filename} ---")

        full_texts, full_scores = run_ocr_and_get_scores(image_path)
        full_avg = sum(full_scores) / len(full_scores) if full_scores else 0.0
        print(f"Full image      -> {len(full_scores)} detections, avg confidence: {full_avg:.4f}")

        image_crop_folder = os.path.join(crop_output_root, name)
        os.makedirs(image_crop_folder, exist_ok=True)

        result = ocr.predict(image_path)
        crop_scores, crop_texts = [], []

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
                crop_texts.extend(texts)
                crop_scores.extend(scores_)

        crop_avg = sum(crop_scores) / len(crop_scores) if crop_scores else 0.0
        print(f"Cropped regions -> {len(crop_scores)} detections, avg confidence: {crop_avg:.4f}")

        winner = "cropped" if crop_avg > full_avg else ("full" if full_avg > crop_avg else "tie")
        print(f"Winner: {winner}")

        rows.append({
            "filename": filename,
            "full_image_avg_confidence": round(full_avg, 4),
            "full_image_detections": len(full_scores),
            "cropped_regions_avg_confidence": round(crop_avg, 4),
            "cropped_regions_detections": len(crop_scores),
            "winner": winner
        })

    with open(results_csv, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=[
            "filename", "full_image_avg_confidence", "full_image_detections",
            "cropped_regions_avg_confidence", "cropped_regions_detections", "winner"
        ])
        writer.writeheader()
        writer.writerows(rows)

    print(f"\nDone! Comparison saved to {results_csv}")
    full_wins = sum(1 for r in rows if r["winner"] == "full")
    crop_wins = sum(1 for r in rows if r["winner"] == "cropped")
    ties = sum(1 for r in rows if r["winner"] == "tie")
    print(f"\nSummary: Full image won {full_wins}/{len(rows)}, Cropped won {crop_wins}/{len(rows)}, Ties: {ties}")


if __name__ == "__main__":
    main()