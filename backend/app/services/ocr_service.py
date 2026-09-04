"""
services/ocr_service.py

Contract (must be kept stable for the OCR/AI teammate to build against):

    extract_declarations(image_path: str) -> dict

    Returns:
    {
        "fields": [
            {"name": str, "value": str, "confidence": float, "bounding_box": [x1,y1,x2,y2]},
            ...
        ]
    }

STAGE: MOCK implementation. Returns a fixed, clearly-labeled sample response
so the rest of the pipeline (compliance engine, scoring, DB, reports) can be
built and tested without waiting on the real OCR model.

To integrate the real OCR/AI module: replace the body of extract_declarations
with a call to that model/service, keeping the same return shape.
"""

MOCK_RESPONSE = {
    "fields": [
        {"name": "manufacturer", "value": "ABC Foods Pvt Ltd, Hyderabad", "confidence": 0.96,
         "bounding_box": [100, 200, 300, 250]},
        {"name": "common_name", "value": "Wheat Flour", "confidence": 0.93,
         "bounding_box": [100, 260, 280, 300]},
        {"name": "mrp", "value": "₹120", "confidence": 0.98,
         "bounding_box": [100, 300, 200, 350]},
        {"name": "net_quantity", "value": "500 g", "confidence": 0.94,
         "bounding_box": [100, 400, 250, 450]},
        # mfg_date and consumer_care intentionally omitted in the mock
        # to demonstrate the compliance engine flagging missing fields.
    ]
}


def extract_declarations(image_path: str) -> dict:
    # TODO: replace with a real call to the OCR/AI module.
    return MOCK_RESPONSE
