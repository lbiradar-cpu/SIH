import re
import json


class LabelExtractor:

    def __init__(self, ocr_text):
        self.original_text = ocr_text
        self.text = self.clean_text(ocr_text)

        self.lines = [
            line.strip()
            for line in self.text.split("\n")
            if line.strip()
        ]

    # =========================================================
    # 1. CLEAN OCR TEXT
    # =========================================================

    def clean_text(self, text):
        """
        Clean common OCR formatting problems.
        """

        if not text:
            return ""

        text = text.replace("\xa0", " ")

        # Normalize rupee / Rs
        text = text.replace("₹", "Rs ")
        text = re.sub(r"Rs\s*\.", "Rs", text, flags=re.IGNORECASE)

        # Normalize multiple spaces
        text = re.sub(r"[ \t]+", " ", text)

        # Normalize excessive newlines
        text = re.sub(r"\n+", "\n", text)

        return text.strip()

    # =========================================================
    # 2. MRP
    # =========================================================

    def extract_mrp(self):

        patterns = [

            # MRP: Rs 50
            r"(?:M\.?\s*R\.?\s*P\.?|MAXIMUM\s+RETAIL\s+PRICE)"
            r"\s*[:\-]?\s*"
            r"(?:Rs\.?|INR)?\s*"
            r"(\d+(?:\.\d{1,2})?)",

            # Rs 50 / Rs. 50
            r"\bRs\.?\s*(\d+(?:\.\d{1,2})?)\b"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                self.text,
                re.IGNORECASE
            )

            if match:

                return {
                    "value": match.group(1),
                    "currency": "INR",
                    "found": True,
                    "confidence": 0.95,
                    "evidence": match.group(0)
                }

        return {
            "value": None,
            "currency": "INR",
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 3. NET QUANTITY / WEIGHT
    # =========================================================

    def extract_net_quantity(self):

        pattern = (
            r"(?:NET\s*(?:QUANTITY|QTY|WEIGHT|WT|CONTENT))"
            r"\s*[:\-]?\s*"
            r"(\d+(?:\.\d+)?)"
            r"\s*"
            r"(kg|kgs|g|gm|gram|grams|mg|l|lt|ltr|litre|litres|ml|"
            r"pcs|pieces|piece|units?)?"
        )

        match = re.search(
            pattern,
            self.text,
            re.IGNORECASE
        )

        if match:

            number = match.group(1)
            unit = match.group(2)

            if unit:
                value = f"{number} {unit}"
            else:
                value = number

            return {
                "value": value,
                "found": True,
                "confidence": 0.93,
                "evidence": match.group(0)
            }

        # Try common standalone pattern such as:
        # 456 g
        # Net Weight: 456 g

        pattern2 = (
            r"(?:NET\s*WEIGHT|NET\s*QTY|NET\s*QUANTITY)"
            r".{0,20}?"
            r"(\d+(?:\.\d+)?)\s*"
            r"(kg|kgs|g|gm|mg|l|ml)"
        )

        match = re.search(
            pattern2,
            self.text,
            re.IGNORECASE
        )

        if match:

            return {
                "value": f"{match.group(1)} {match.group(2)}",
                "found": True,
                "confidence": 0.90,
                "evidence": match.group(0)
            }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 4. MANUFACTURER
    # =========================================================

    def extract_manufacturer(self):

        manufacturer_keywords = [
            "manufactured by",
            "manufactured & packed by",
            "manufactured and packed by",
            "manufactured & marketed by",
            "manufactured and marketed by",
            "mfd by",
            "mfd. by",
            "mfg by",
            "manufactured for",
            "packed by",
            "marketed by"
        ]

        for i, line in enumerate(self.lines):

            lower_line = line.lower()

            for keyword in manufacturer_keywords:

                if keyword in lower_line:

                    parts = re.split(
                        re.escape(keyword),
                        line,
                        flags=re.IGNORECASE
                    )

                    # Example:
                    # MFD. BY: FERRERO INDIA PVT. LTD.

                    if len(parts) > 1:

                        value = parts[1].strip(" :-")

                        if value:

                            return {
                                "value": value,
                                "found": True,
                                "confidence": 0.90,
                                "evidence": line
                            }

                    # Example:
                    # Manufactured by:
                    # ABC Foods Pvt Ltd

                    if i + 1 < len(self.lines):

                        next_line = self.lines[i + 1]

                        return {
                            "value": next_line,
                            "found": True,
                            "confidence": 0.85,
                            "evidence": f"{line} {next_line}"
                        }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 5. MANUFACTURER ADDRESS
    # =========================================================

    def extract_manufacturer_address(self):

        address_keywords = [
            "regd. off",
            "regd off",
            "registered office",
            "factory",
            "address",
            "plot no",
            "road",
            "district",
            "mfd. by"
        ]

        for i, line in enumerate(self.lines):

            lower_line = line.lower()

            if any(keyword in lower_line for keyword in address_keywords):

                # Look for address-like content
                if re.search(
                    r"\b(?:plot|road|street|dist|district|"
                    r"pune|delhi|mumbai|bangalore|maharashtra|"
                    r"india|pin|[0-9]{6})\b",
                    line,
                    re.IGNORECASE
                ):

                    return {
                        "value": line,
                        "found": True,
                        "confidence": 0.80,
                        "evidence": line
                    }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 6. MANUFACTURING / PACKING DATE
    # =========================================================

    def extract_date(self):

        date_keywords = [
            "mfg",
            "mfd",
            "manufactured",
            "manufacturing",
            "packed",
            "packing",
            "pack",
            "date of manufacture",
            "date of packing"
        ]

        date_patterns = [

            # 08/2026
            r"\b\d{1,2}[/-]\d{4}\b",

            # 08/08/2026
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{4}\b",

            # 08-Aug-2026
            r"\b\d{1,2}[-\s](?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*[-\s]\d{4}\b",

            # Aug 2026
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*"
            r"\s+\d{4}\b"
        ]

        for line in self.lines:

            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in date_keywords
            ):

                for pattern in date_patterns:

                    match = re.search(
                        pattern,
                        line,
                        re.IGNORECASE
                    )

                    if match:

                        return {
                            "value": match.group(0),
                            "found": True,
                            "confidence": 0.90,
                            "evidence": line
                        }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 7. EXPIRY / USE BY DATE
    # =========================================================

    def extract_expiry(self):

        expiry_keywords = [
            "expiry",
            "expires",
            "exp",
            "use by",
            "best before",
            "best by"
        ]

        date_pattern = (
            r"\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b"
            r"|"
            r"\b\d{1,2}[/-]\d{4}\b"
            r"|"
            r"\b(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)"
            r"[a-z]*[-\s]\d{4}\b"
        )

        for line in self.lines:

            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in expiry_keywords
            ):

                match = re.search(
                    date_pattern,
                    line,
                    re.IGNORECASE
                )

                if match:

                    return {
                        "value": match.group(0),
                        "found": True,
                        "confidence": 0.90,
                        "evidence": line
                    }

                # Sometimes OCR separates the date
                # onto the next line.

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 8. BATCH / LOT NUMBER
    # =========================================================

    def extract_batch_number(self):

        patterns = [

            r"(?:BATCH\s*(?:NO|NUMBER)?|BATCH\s*CODE)"
            r"\s*[:\-]?\s*([A-Z0-9\/\-.]+)",

            r"(?:LOT\s*(?:NO|NUMBER)?)"
            r"\s*[:\-]?\s*([A-Z0-9\/\-.]+)"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                self.text,
                re.IGNORECASE
            )

            if match:

                return {
                    "value": match.group(1),
                    "found": True,
                    "confidence": 0.90,
                    "evidence": match.group(0)
                }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 9. FSSAI LICENSE
    # =========================================================

    def extract_fssai(self):

        patterns = [

            r"(?:FSSAI|FSSAI\s*LIC\.?|LIC\.?\s*NO\.?)"
            r".{0,30}?"
            r"(\d{10,14})"
        ]

        for pattern in patterns:

            match = re.search(
                pattern,
                self.text,
                re.IGNORECASE
            )

            if match:

                return {
                    "value": match.group(1),
                    "found": True,
                    "confidence": 0.90,
                    "evidence": match.group(0)
                }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 10. INGREDIENTS
    # =========================================================

    def extract_ingredients(self):

        for i, line in enumerate(self.lines):

            if re.search(
                r"\bingredients?\b",
                line,
                re.IGNORECASE
            ):

                # If ingredients are on same line
                parts = re.split(
                    r"ingredients?\s*:?",
                    line,
                    maxsplit=1,
                    flags=re.IGNORECASE
                )

                if len(parts) > 1:

                    value = parts[1].strip(" :-")

                    if value:

                        return {
                            "value": value,
                            "found": True,
                            "confidence": 0.90,
                            "evidence": line
                        }

                # Otherwise next line
                if i + 1 < len(self.lines):

                    return {
                        "value": self.lines[i + 1],
                        "found": True,
                        "confidence": 0.80,
                        "evidence": f"{line} {self.lines[i + 1]}"
                    }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 11. NUTRITIONAL INFORMATION
    # =========================================================

    def extract_nutrition(self):

        keywords = [
            "nutritional information",
            "nutrition information",
            "nutrition facts",
            "energy",
            "protein",
            "carbohydrates",
            "total fat",
            "saturated fat"
        ]

        for line in self.lines:

            if any(
                keyword in line.lower()
                for keyword in keywords
            ):

                return {
                    "value": line,
                    "found": True,
                    "confidence": 0.90,
                    "evidence": line
                }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 12. CUSTOMER CARE
    # =========================================================

    def extract_consumer_care(self):

        keywords = [
            "consumer care",
            "customer care",
            "helpline",
            "toll free",
            "contact us",
            "contact consumer",
            "contact"
        ]

        phone_pattern = (
            r"(?:\+91[\s-]?)?"
            r"(?:[6-9]\d{9}|"
            r"\d{4}[\s-]?\d{3}[\s-]?\d{3})"
        )

        email_pattern = (
            r"\b[A-Za-z0-9._%+-]+"
            r"@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
        )

        for i, line in enumerate(self.lines):

            lower_line = line.lower()

            if any(
                keyword in lower_line
                for keyword in keywords
            ):

                phone = re.search(
                    phone_pattern,
                    line
                )

                email = re.search(
                    email_pattern,
                    line
                )

                if phone:

                    return {
                        "value": phone.group(0),
                        "found": True,
                        "confidence": 0.90,
                        "evidence": line
                    }

                if email:

                    return {
                        "value": email.group(0),
                        "found": True,
                        "confidence": 0.90,
                        "evidence": line
                    }

                # Check next line

                if i + 1 < len(self.lines):

                    next_line = self.lines[i + 1]

                    phone = re.search(
                        phone_pattern,
                        next_line
                    )

                    email = re.search(
                        email_pattern,
                        next_line
                    )

                    if phone:

                        return {
                            "value": phone.group(0),
                            "found": True,
                            "confidence": 0.85,
                            "evidence": f"{line} {next_line}"
                        }

                    if email:

                        return {
                            "value": email.group(0),
                            "found": True,
                            "confidence": 0.85,
                            "evidence": f"{line} {next_line}"
                        }

        return {
            "value": None,
            "found": False,
            "confidence": 0.0,
            "evidence": None
        }

    # =========================================================
    # 13. EXTRACT EVERYTHING
    # =========================================================

    def extract_all(self):

        return {

            "manufacturer": self.extract_manufacturer(),

            "manufacturer_address":
                self.extract_manufacturer_address(),

            "net_quantity":
                self.extract_net_quantity(),

            "mrp":
                self.extract_mrp(),

            "batch_number":
                self.extract_batch_number(),

            "fssai_license":
                self.extract_fssai(),

            "manufacturing_or_packing_date":
                self.extract_date(),

            "expiry_or_use_by_date":
                self.extract_expiry(),

            "ingredients":
                self.extract_ingredients(),

            "nutritional_information":
                self.extract_nutrition(),

            "consumer_care":
                self.extract_consumer_care()
        }


# =============================================================
# TEST
# =============================================================

if __name__ == "__main__":

    ocr_text = """
    Kinder
    RICH IN MILK SOLIDS
    MILKY CREAMY & CRUNCHY

    PROPRIETARY FOOD - COCOA SPREADS WITH EXTRUDED RICE

    NUTRITIONAL INFORMATION

    INGREDIENTS: SUGAR, SKIMMED COW MILK POWDER (22%),
    PALMOLEIN, PALM OIL, EXTRUDED RICE (7.7%),
    LOW FAT COCOA POWDER (2.6%),
    EMULSIFIER (LECITHIN - INS 322),
    POWDERED BARLEY MALT EXTRACT.

    MFD. BY: FERRERO INDIA PVT. LTD.
    Regd. Off. & Factory: Plot No. F-13,
    MIDC, Baramati, District Pune 413133,
    Maharashtra, India.

    Contact Consumer Executive:
    1800-209-1200
    customercare.india@ferrero.com

    NET WEIGHT:
    456 g

    Lic. No. 10013022002

    MRP: Rs 500

    Batch No: ABC123

    Mfg: 08/2026

    Best Before: 12/2026
    """

    extractor = LabelExtractor(ocr_text)

    result = extractor.extract_all()

    print("\n========== STRUCTURED LABEL DATA ==========\n")

    print(
        json.dumps(
            result,
            indent=4,
            ensure_ascii=False
        )
    )