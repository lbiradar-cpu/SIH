# SIH26034 - Legal Metrology Compliance Backend

Full backend: auth, image upload, mock OCR interface, compliance engine,
scoring, evidence, PostgreSQL persistence, and PDF report generation.
Every endpoint below has been tested end-to-end (register -> login ->
inspect -> compliance result -> PDF report).

## 1. Set up the virtual environment

```bash
cd backend
python -m venv venv

# activate it:
# macOS/Linux:
source venv/bin/activate
# Windows (PowerShell):
venv\Scripts\Activate.ps1
```

You'll know it worked because your terminal prompt shows `(venv)` at the start.

## 2. Install dependencies

```bash
pip install -r requirements.txt
```

## 3. Set up PostgreSQL and environment variables

```bash
cp .env.example .env
```

Create the database (adjust to how Postgres is set up on your machine):
```bash
createdb legal_metrology
# or: psql -U postgres -c "CREATE DATABASE legal_metrology;"
```

Edit `DATABASE_URL` in `.env` if your Postgres user/password/host differ
from the default. Tables are created automatically (and the 6 mandatory-
declaration rules seeded) the first time you start the server - no manual
migration step needed for this MVP.

Don't have Postgres installed yet? For a quick local test you can instead
set `DATABASE_URL=sqlite:///./dev.db` in `.env` - everything works the
same, just swap it back to Postgres before the real demo/integration.

## 4. Run the server

```bash
uvicorn app.main:app --reload
```

- `app.main:app` = "look inside `app/main.py`, find the variable named `app`"
- `--reload` = auto-restart the server whenever you save a file (dev only)

You should see something like:
```
Uvicorn running on http://127.0.0.1:8000
```

## 5. Test it

- Open **http://127.0.0.1:8000/docs** in your browser - this is Swagger UI.
- Expand `GET /api/health`, click **Try it out**, click **Execute**.
  You should get a `200` response with a JSON body.
- Expand `POST /api/inspect`, click **Try it out**, choose an image file
  under the `image` field, click **Execute**. You get back the full
  compliance result: declarations, violations, score, status.
- Check the `uploads/` folder - your image should now be sitting there
  under a new UUID filename.
- Try `POST /api/auth/register` then `POST /api/auth/login` to get a JWT,
  then `GET /api/auth/me` (Swagger's "Authorize" button lets you paste the
  token in once and reuse it for every protected call).
- Try `GET /api/inspection/{id}`, `GET /api/inspections`, `GET /api/rules`,
  `GET /api/products`, `GET /api/dashboard`.
- Try `POST /api/inspection/{id}/report` then `GET
  /api/inspection/{id}/report/download` to generate and fetch the PDF.

## Running the tests

```bash
pytest tests/ -v
```

## Project structure

```
backend/
  app/
    main.py                    <- creates the app, wires all routers, runs init_db() on startup
    api/
      health.py                <- GET /api/health
      auth.py                  <- POST /api/auth/register, /login, GET /me
      inspection.py            <- POST /api/inspect, GET /api/inspection/{id}, GET /api/inspections
      rules.py                 <- GET /api/rules
      products.py              <- GET /api/products
      dashboard.py             <- GET /api/dashboard
      reports.py                <- POST/GET /api/inspection/{id}/report
    models/                     <- SQLAlchemy tables: user, inspection, declaration, rule, violation, evidence
    schemas/                    <- Pydantic request/response shapes
    services/
      ocr_service.py            <- OCR contract + MOCK implementation (swap in real OCR here)
      compliance_engine.py      <- checks declarations against active rules, generates violations
      scoring_service.py        <- turns violations into a 0-100 score
      evidence_service.py       <- links declarations to evidence rows for reports
      report_service.py         <- generates the PDF compliance report
    database/
      base.py, connection.py    <- SQLAlchemy engine/session + init_db() (creates tables, seeds rules)
    core/
      config.py                 <- typed Settings from .env
      security.py                <- password hashing + JWT
  uploads/                       <- stored package images
  reports/                       <- generated PDF reports
  tests/test_api.py              <- pytest suite covering all endpoints
  requirements.txt
  .env.example
```

## What's still a placeholder (by design)

**`services/ocr_service.py`** returns a fixed mock response (see the file)
instead of calling a real OCR/AI model. This is intentional - it lets the
rest of the pipeline (compliance engine, DB, reports) be built and tested
without waiting on the OCR teammate. To wire in the real model, replace the
body of `extract_declarations()` with a call to it, keeping the same
return shape (see the `fields` contract at the top of that file).

Auth is built (`/api/auth/*`) but **not enforced** on the other endpoints
yet - `/api/inspect`, `/api/rules`, etc. are public for easy testing during
the hackathon. To require login on a route, add `current_user: User =
Depends(get_current_user)` to that route's function signature (see
`app/core/security.py`).

## Common errors & how to debug them

**`ModuleNotFoundError: No module named 'fastapi'`**
Your virtual environment isn't activated, or dependencies weren't installed
inside it. Re-run steps 1-2, and confirm `(venv)` is in your prompt.

**`uvicorn: command not found`**
Same cause as above - `uvicorn` was installed inside `venv`, but you're not
in that environment. Activate it.

**Swagger shows the endpoint but `Execute` gives a connection error**
The server isn't actually running, or is running on a different port than
the browser tab is pointing at. Check the terminal for the "Uvicorn running
on ..." line and make sure it matches your browser URL.

**`POST /api/inspect` returns 400 "Unsupported file type"**
You uploaded something that isn't a `.jpg`/`.jpeg`/`.png`, or your OS/browser
tagged the file with an unexpected MIME type. Try a plain `.jpg` first.

**Port already in use (`Address already in use`)**
Another uvicorn instance (maybe from a previous run) is still holding port
8000. Either stop it, or run this one on a different port:
`uvicorn app.main:app --reload --port 8001`

**Changes to code don't show up**
Make sure you started uvicorn with `--reload`, and that you saved the file.
If it still doesn't pick up, stop the server (Ctrl+C) and restart it.

**`sqlalchemy.exc.OperationalError: could not connect to server`**
Postgres isn't running, or `DATABASE_URL` in `.env` points to the wrong
host/port/credentials. Confirm Postgres is running (`pg_isready`) and that
the database from step 3 actually exists.

**`ValueError: password cannot be longer than 72 bytes` on register/login**
This is a known version-compatibility issue between `passlib` and newer
`bcrypt` releases (5.x). `requirements.txt` pins `bcrypt==4.0.1` to avoid
it - if you still hit this, run `pip install "bcrypt==4.0.1"` inside your
venv to force the compatible version.

**Report generation returns 500, image doesn't embed**
The PDF still generates (with a placeholder line instead of the image) if
the stored file isn't a real, decodable image - useful to know if you're
testing with a fake/corrupted file. Use a real `.jpg`/`.png` to confirm
image embedding.
