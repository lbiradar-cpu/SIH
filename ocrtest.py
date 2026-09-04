import os
import json
from paddleocr import PaddleOCR

ocr = PaddleOCR(
    lang="en",
    use_doc_orientation_classify=False,
    use_doc_unwarping=False,
    use_textline_orientation=False,
    enable_mkldnn=False,
)

script_dir = os.path.dirname(os.path.abspath(__file__))
image_path = os.path.join(script_dir, "images", "1.jpeg")

result = ocr.predict(image_path)

structured_data = []

for res in result:
    texts = res["rec_texts"]
    scores = res["rec_scores"]
    boxes = res["rec_polys"]  # list of 4-point polygons per detected text line

    for text, score, box in zip(texts, scores, boxes):
        structured_data.append({
            "text": text,
            "confidence": round(float(score), 4),
            "box": [[float(x), float(y)] for x, y in box]
        })

# Save structured output to JSON
output_path = os.path.join(script_dir, "output.json")
with open(output_path, "w", encoding="utf-8") as f:
    json.dump(structured_data, f, indent=2, ensure_ascii=False)

print(f"Extracted {len(structured_data)} text lines. Saved to {output_path}")

# Also print a clean readable summary
for item in structured_data:
    print(f"[{item['confidence']:.2f}] {item['text']}")