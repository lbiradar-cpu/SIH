import os
import json
from paddleocr import PaddleOCR
from label_extractor import LabelExtractor


# -----------------------------
# 1. Start PaddleOCR
# -----------------------------

ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False,
)


# -----------------------------
# 2. Find image
# -----------------------------

script_dir = os.path.dirname(os.path.abspath(__file__))

image_path = os.path.join(
    script_dir,
    "ocr_images",
    "1.jpeg"
)


# -----------------------------
# 3. Run OCR
# -----------------------------

result = ocr.predict(image_path)


# -----------------------------
# 4. Get OCR text
# -----------------------------

ocr_lines = []

for res in result:
    texts = res["rec_texts"]

    for text in texts:
        ocr_lines.append(text)


# Convert OCR lines into one text block
ocr_text = "\n".join(ocr_lines)


print("\n========== RAW OCR TEXT ==========\n")
print(ocr_text)


# -----------------------------
# 5. Send OCR text to extractor
# -----------------------------

extractor = LabelExtractor(ocr_text)

structured_data = extractor.extract_all()


# -----------------------------
# 6. Print structured data
# -----------------------------

print("\n========== STRUCTURED DATA ==========\n")

print(
    json.dumps(
        structured_data,
        indent=4,
        ensure_ascii=False
    )
)


# -----------------------------
# 7. Save JSON
# -----------------------------

output_path = os.path.join(
    script_dir,
    "structured_output.json"
)

with open(
    output_path,
    "w",
    encoding="utf-8"
) as f:

    json.dump(
        structured_data,
        f,
        indent=4,
        ensure_ascii=False
    )


print(
    f"\nStructured data saved to: {output_path}"
)