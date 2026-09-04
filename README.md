# Legal Metrology Compliance Checker — Starter Project

This is the simplest possible working version of the system: upload a product
label photo → it reads the text → checks it against basic rules → saves the
result. Build everything else (dashboard, more rules, font-size checks) on
top of this once it runs.

## Folder structure

```
lm_compliance_starter/
├── app.py                  <- the API (run this first)
├── test_with_dataset.py    <- sends your dataset images to the API
├── requirements.txt        <- list of Python packages needed
├── dataset/                <- PUT YOUR PRODUCT LABEL PHOTOS HERE
├── uploads/                <- images you send via the API get saved here automatically
└── compliance.db           <- created automatically; stores every scan result
```

## Step 1 — Install the requirements

```bash
pip install -r requirements.txt
```

## Step 2 — Start the API

```bash
python app.py
```

Leave this running. The first time you run it, EasyOCR will download its
language model (takes a minute or two) — you'll see "OCR model ready."
when it's done. The API is now live at http://localhost:5000

## Step 3 — Add some images to test with

Drop a few photos of real product labels into the `dataset/` folder
(biscuit packets, shampoo bottles, soap boxes — anything with an MRP,
net quantity, and manufacturing date printed on it).

## Step 4 — Send the dataset to the API

Open a SECOND terminal (keep app.py running in the first one) and run:

```bash
python test_with_dataset.py
```

This loops through every image in `dataset/`, sends it to the API, and
prints whether it was found COMPLIANT or NON_COMPLIANT, plus which
declarations were found or missing.

## Step 5 — Check the history / dashboard data

Visit this in your browser or Postman:

```
GET http://localhost:5000/history
```

This returns every scan you've ever done — this is the data your
dashboard/repository feature (from the problem statement) would display.

## What each rule check currently does (very basic — improve these!)

| Function | What it looks for | Rule |
|---|---|---|
| `check_mrp` | "MRP" or "Maximum Retail Price" followed by a number | Rule 6(1)(e) |
| `check_net_quantity` | A number followed by g/kg/ml/l | Rule 6(1)(c) |
| `check_manufacturing_date` | A month name + year | Rule 6(1)(d) |
| `check_consumer_care` | Keywords like "customer care", "toll free" | Rule 6(2) |
| `check_misleading_words` | Banned words like "approximately", "about" | Rule 12(6) |

These are simple regex/keyword checks — good enough to demo, but you should
improve them as you test with real images (OCR text is often messy, e.g.
"NIRP" instead of "MRP", so you'll want to handle typos/variants).

## Where to go next (in order of difficulty)

1. Improve the regex patterns above once you see what real OCR output looks like.
2. Add more checks: manufacturer name/address, consumer care email format, country of origin.
3. Add font-size measurement (needs a reference object of known size in the photo).
4. Build a simple frontend (or use Postman/curl for now) to upload images visually.
5. Add login / role-based access for different officer roles.
6. Add PDF report generation for each scan result.

## Common issues

- **"No module named easyocr"** → run `pip install -r requirements.txt` again.
- **OCR is slow the first time** → normal, it's downloading the language model. Subsequent runs are fast.
- **OCR misses text or reads it wrong** → try a clearer, well-lit, straight-on photo. Blurry/angled photos give poor OCR results.
- **Port 5000 already in use** → change `port=5000` to `port=5001` in `app.py`, and update `API_URL` in `test_with_dataset.py` to match.
