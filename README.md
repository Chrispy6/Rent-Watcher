# Rent Watcher

A rental comparison project for Golden, Colorado. The interface displays addresses,
monthly asking rent, bedrooms, bathrooms, and square footage, with minimum/maximum
rent filters and a reset control.

## Current behavior

- The local frontend requests listings from FastAPI, which queries PostgreSQL.
- Rent filtering currently runs in the browser after the records are loaded.
- The GitHub Pages demo loads the saved JSON snapshot directly. It does not require
  a visitor to run the local backend.
- Both versions use saved RentCast data. Automatic refreshes, historical tracking,
  and price scoring are not implemented. The snapshot contains 99 listings; it is
  not a claim about current availability.

Demo: https://chrispy6.github.io/Rent-Watcher/

## Requirements

- Python and pip (the development environment currently uses Python 3.15)
- PostgreSQL (the local setup uses PostgreSQL 18 on port 5432)
- PowerShell for the commands below

## Install Python dependencies

Run commands from the project root:

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r backend/requirements.txt
```

If `.venv` already exists, skip creating it again. No activation is required when
using its Python executable directly.

## Create the database and table

With PostgreSQL running, open its command-line client (adjust the version/path if
needed):

```powershell
& "C:\Program Files\PostgreSQL\18\bin\psql.exe" -h 127.0.0.1 -p 5432 -U postgres -d postgres
```

In psql, for a new setup:

```sql
CREATE DATABASE rent_watcher;
\connect rent_watcher
\i backend/schema.sql
```

Skip creation steps for an existing database/table. `backend/schema.sql` is the
schema definition, not a migration that should be rerun against an existing table.

## Import the saved records

In PowerShell:

```powershell
.\.venv\Scripts\python.exe backend/import_listings.py
```

Enter the PostgreSQL password when prompted. The importer reads
`Golden_Listings.json` without calling RentCast. Existing IDs are updated rather
than duplicated. Missing or nonpositive square footage becomes SQL NULL.
If an import fails, its transaction is rolled back.

In psql, check the result:

```sql
SELECT COUNT(*) FROM listings;
```

For the supplied snapshot, expect 99 records.

## Run the local application

In the first PowerShell terminal, supply the database password as a process
environment variable. Enter the actual password at the prompt, not in source code:

```powershell
$env:RENT_WATCHER_DB_PASSWORD = [System.Net.NetworkCredential]::new("", (Read-Host "PostgreSQL password" -AsSecureString)).Password
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

The variable name in Python stays `RENT_WATCHER_DB_PASSWORD`. Set the variable
again if you open a new terminal. The local backend currently connects as the
`postgres` administrator; use a dedicated application role before production use.

In a second PowerShell terminal at the project root:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Open http://127.0.0.1:5500/ and keep both terminals running. Press Ctrl+C in a
terminal to stop its server. PostgreSQL must also remain running.

Endpoints:

- `http://127.0.0.1:8000/alive`: verifies the backend responds; does not check the database.
- `http://127.0.0.1:8000/listings`: queries PostgreSQL and returns listing records.
- `http://127.0.0.1:8000/docs`: interactive API documentation.

## Manual checks

- Empty inputs: 99 listings for the supplied snapshot.
- Minimum 800 and maximum 2000: 56 listings.
- Reset: all listings restored and inputs cleared.
- Minimum 9000 with no maximum: zero listings.
- Negative rent or minimum above maximum: validation message.
- Equal minimum and maximum: listings priced at exactly that amount.

## Project structure

- `index.html`: page structure and filter controls.
- `style.css`: responsive grid and card styling.
- `script.js`: loading, rendering, input validation, and browser-side filtering.
- `Golden_Listings.json`: saved rental snapshot obtained from RentCast.
- `backend/main.py`: FastAPI endpoints, local CORS configuration, and database query.
- `backend/schema.sql`: PostgreSQL table definition.
- `backend/import_listings.py`: manual JSON-to-PostgreSQL importer.
- `backend/requirements.txt`: Python dependencies.

## Deployment status

GitHub Pages hosts the snapshot-based frontend demo. The FastAPI backend and
PostgreSQL database are local. A public backend deployment will need a public API
URL, configured database connection settings, and its frontend origin allowed by CORS.

## License

MIT. The repository's code license does not replace the data provider's terms.
