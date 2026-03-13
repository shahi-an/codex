# MaidConnect (Maid / Househelp Listing App)

MaidConnect is a simple Flask web application where:

- Users can browse available maids/househelp in their area.
- Users can view each maid's details:
  - Name
  - Age
  - Experience
  - Current address
  - Phone number
  - ID verification status
- Users can send a **call request** to a maid.
- Maids can register themselves on the platform.
- Maids can log in and view how many call requests they have received.

## Prerequisites

- Python 3.10+
- Pip
- (Optional) A database URL if you don't want SQLite

By default, the app uses **SQLite** (`maids.db`) and creates tables automatically.
So **no separate DB setup is required** for local usage.

If you want PostgreSQL/MySQL, set `DATABASE_URL` before running the app.

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open: `http://localhost:5000`

## Environment variables

- `SECRET_KEY` (optional): Flask session secret
- `DATABASE_URL` (optional): SQLAlchemy DB URL (default: `sqlite:///maids.db`)
