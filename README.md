# Vulnerability Tracker MVP

This project is a lightweight web app to:

- Import vulnerability reports from Excel (`.xlsx`)
- Store all imported rows in a database (SQLite by default)
- Auto-assign vulnerabilities to individuals/teams using vulnerability-type rules
- Update status (`Open`, `Work in Progress`, `Closed`, `Awaiting Further Information`)
- Click a vulnerability record to view all stored details

## Run locally

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Then open `http://localhost:5000`.

## Suggested Excel columns

The importer attempts to map common header names. These are recommended:

- `id`
- `server_name`
- `vulnerability_type`
- `severity`
- `description`
- `status` (optional)

Alternative names like `server`, `hostname`, `type`, `category`, `risk`, and `details` are also recognized.
