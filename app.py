"""
Legal Metrology Compliance Checker - Starter API
--------------------------------------------------
This is the simplest possible working version:
  1. Accepts an uploaded product label image
  2. Runs OCR to extract text
  3. Checks the text against basic Legal Metrology rules
  4. Saves the result to a database
  5. Lets you view past results (for the dashboard/history feature)

Run with:  python app.py
Then test with:  python test_with_dataset.py
"""

import os
import re
import sqlite3
import json
from flask import Flask, request, jsonify
import easyocr

app = Flask(__name__)

UPLOAD_FOLDER = "uploads"
DB_FILE = "compliance.db"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# Load OCR reader once at startup (English + Hindi, per Rule 9(4))
print("Loading OCR model... (first run may take a minute to download)")
reader = None
print("OCR model ready.")


# ---------------------------------------------------------
# 1. DATABASE SETUP  (this is the "repository" requirement)
# ---------------------------------------------------------
def init_db():
    conn = sqlite3.connect(DB_FILE)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS scans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            filename TEXT,
            extracted_text TEXT,
            checks_result TEXT,
            overall_status TEXT
        )
    """)
    conn.commit()
    conn.close()


def save_scan(filename, extracted_text, checks_result, overall_status):
    conn = sqlite3.connect(DB_FILE)
    conn.execute(
        "INSERT INTO scans (filename, extracted_text, checks_result, overall_status) VALUES (?, ?, ?, ?)",
        (filename, json.dumps(extracted_text), json.dumps(checks_result), overall_status)
    )
    conn.commit()
    conn.close()


# ---------------------------------------------------------
# 2. RULE CHECKS  (this is where Legal Metrology logic lives)
#    Each function looks at the OCR text list and returns
#    whether that declaration was found.
# ---------------------------------------------------------
def check_mrp(text_list):
    full_text = " ".join(text_list).upper()
    # Looks for MRP or "Maximum Retail Price" followed by a number
    pattern = r"(MRP|MAXIMUM RETAIL PRICE)[^\d]{0,15}(\d+)"
    match = re.search(pattern, full_text)
    if match:
        return {"found": True, "value": match.group(2), "rule": "Rule 6(1)(e)"}
    return {"found": False, "value": None, "rule": "Rule 6(1)(e)"}


def check_net_quantity(text_list):
    full_text = " ".join(text_list).upper()
    # Looks for a number followed by g, kg, ml, l (common units)
    pattern = r"(\d+\.?\d*)\s*(G|GM|GRAM|KG|ML|L|LITRE|LITER)\b"
    match = re.search(pattern, full_text)
    if match:
        return {"found": True, "value": match.group(0), "rule": "Rule 6(1)(c)"}
    return {"found": False, "value": None, "rule": "Rule 6(1)(c)"}


def check_manufacturing_date(text_list):
    full_text = " ".join(text_list).upper()
    # Looks for month names or MM/YYYY style dates
    pattern = r"(JAN|FEB|MAR|APR|MAY|JUN|JUL|AUG|SEP|OCT|NOV|DEC)[A-Z]*\.?\s*\d{2,4}"
    match = re.search(pattern, full_text)
    if match:
        return {"found": True, "value": match.group(0), "rule": "Rule 6(1)(d)"}
    return {"found": False, "value": None, "rule": "Rule 6(1)(d)"}


def check_consumer_care(text_list):
    full_text = " ".join(text_list).upper()
    # Looks for keywords that usually appear near consumer care info
    keywords = ["CUSTOMER CARE", "CONSUMER CARE", "TOLL FREE", "EMAIL", "WWW."]
    found = any(k in full_text for k in keywords)
    return {"found": found, "value": None, "rule": "Rule 6(2)"}


def check_misleading_words(text_list):
    full_text = " ".join(text_list).upper()
    # Rule 12(6): these words are NOT allowed near quantity declarations
    banned_words = ["MINIMUM", "NOT LESS THAN", "AVERAGE", "ABOUT", "APPROXIMATELY"]
    hits = [w for w in banned_words if w in full_text]
    return {"violation": len(hits) > 0, "words_found": hits, "rule": "Rule 12(6)"}


def run_all_checks(text_list):
    """Runs every rule check and returns one combined result."""
    results = {
        "mrp": check_mrp(text_list),
        "net_quantity": check_net_quantity(text_list),
        "manufacturing_date": check_manufacturing_date(text_list),
        "consumer_care": check_consumer_care(text_list),
        "misleading_words": check_misleading_words(text_list),
    }

    # Decide overall pass/fail: all mandatory fields must be found,
    # and there must be no misleading words.
    mandatory_ok = (
        results["mrp"]["found"]
        and results["net_quantity"]["found"]
        and results["manufacturing_date"]["found"]
        and results["consumer_care"]["found"]
    )
    no_violations = not results["misleading_words"]["violation"]

    overall_status = "COMPLIANT" if (mandatory_ok and no_violations) else "NON_COMPLIANT"
    return results, overall_status


# ---------------------------------------------------------
# 3. API ENDPOINTS
# ---------------------------------------------------------
@app.route('/scan', methods=['POST'])
def scan_label():
    """
    Upload an image, get OCR text + compliance check result back.
    Usage (from Postman or curl):
        POST http://localhost:5000/scan
        form-data: image = <your file>
    """
    if 'image' not in request.files:
        return jsonify({"error": "No image uploaded. Use form field name 'image'."}), 400

    image_file = request.files['image']
    save_path = os.path.join(UPLOAD_FOLDER, image_file.filename)
    image_file.save(save_path)

    # Run OCR
    ocr_result = reader.readtext(save_path)
    extracted_text = [text for (bbox, text, confidence) in ocr_result]

    # Run rule checks
    checks_result, overall_status = run_all_checks(extracted_text)

    # Save to database (this builds your "repository / history" feature)
    save_scan(image_file.filename, extracted_text, checks_result, overall_status)

    return jsonify({
        "filename": image_file.filename,
        "extracted_text": extracted_text,
        "checks": checks_result,
        "overall_status": overall_status
    })


@app.route('/history', methods=['GET'])
def get_history():
    """Returns every past scan - this feeds your dashboard."""
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    rows = conn.execute("SELECT * FROM scans ORDER BY id DESC").fetchall()
    conn.close()

    history = []
    for row in rows:
        history.append({
            "id": row["id"],
            "filename": row["filename"],
            "extracted_text": json.loads(row["extracted_text"]),
            "checks": json.loads(row["checks_result"]),
            "overall_status": row["overall_status"],
        })
    return jsonify(history)


@app.route('/', methods=['GET'])
def home():
    return jsonify({
        "message": "Legal Metrology Compliance Checker API is running.",
        "endpoints": {
            "POST /scan": "Upload an image to scan (form field: 'image')",
            "GET /history": "View all past scan results"
        }
    })


if __name__ == '__main__':
    init_db()
    app.run(debug=True, port=5000)
