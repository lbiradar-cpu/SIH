from paddleocr import PaddleOCR
import os
import csv

output_folder = "output"
results_csv = "ocr_results.csv"
MAX_IMAGES = 20  # <-- change this to 15 if you want fewer

ocr = PaddleOCR(
    lang="en",
    use_textline_orientation=True,
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
)

rows = []

# Get all valid image filenames first, then slice to the limit
all_files = [
    f for f in os.listdir(output_folder)
    if f.lower().endswith((".jpg", ".jpeg", ".png"))
]
files_to_process = all_files[:MAX_IMAGES]

print(f"Found {len(all_files)} images total. Processing {len(files_to_process)}.")

for filename in files_to_process:
    # figure out which "version" this file is, based on your naming pattern
    if "_original" in filename:
        version = "original"
    elif "_gray" in filename:
        version = "gray"
    elif "_enhanced" in filename:
        version = "enhanced"
    elif "_threshold" in filename:
        version = "threshold"
    else:
        version = "unknown"

    path = os.path.join(output_folder, filename)
    result = ocr.predict(path)

    texts = []
    confidences = []

    for res in result:
        texts.extend(res["rec_texts"])
        confidences.extend(res["rec_scores"])

    full_text = " ".join(texts)
    avg_confidence = sum(confidences) / len(confidences) if confidences else 0.0

    rows.append({
        "filename": filename,
        "version": version,
        "extracted_text": full_text,
        "confidence": round(avg_confidence, 4)
    })

    print(f"Processed {filename} — confidence: {avg_confidence:.2f}")

# write everything to CSV
with open(results_csv, "w", newline="", encoding="utf-8") as f:
    writer = csv.DictWriter(f, fieldnames=["filename", "version", "extracted_text", "confidence"])
    writer.writeheader()
    writer.writerows(rows)

print(f"Done! Results saved to {results_csv}")