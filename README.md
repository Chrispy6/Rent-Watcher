# Rent Watcher

A full-stack rental search application for Golden, Colorado. Browse rental
listings and filter by monthly rent, with automated data refreshes and a saved
snapshot that keeps the public site usable while the backend starts.

[Live website](https://chrispy6.github.io/Rent-Watcher/) ·
[API documentation](https://rent-watcher.onrender.com/docs)

## Features

- Listing cards with address, monthly rent, bedrooms, bathrooms, and square footage.
- Minimum and maximum rent filters, input validation, and a reset control.
- FastAPI endpoints backed by PostgreSQL hosted on Neon.
- Daily RentCast ingestion through GitHub Actions, with response validation and
  transactional inserts, updates, and removal of old Golden listings.
- A saved JSON snapshot displayed before the public backend responds. Current
  filter inputs are reapplied when database records arrive; the snapshot remains
  available if the backend request fails.
- A persistent request budget shared across updater runs.

## Architecture

| Component | Technology / hosting | Responsibility |
| --- | --- | --- |
| Frontend | HTML, CSS, JavaScript / GitHub Pages | Render listings and handle visitor interactions |
| Backend | Python, FastAPI, Uvicorn / Render | Validate API query parameters and query PostgreSQL |
| Database | PostgreSQL / Neon | Store the latest imported listings and request-attempt ledger |
| Data refresh | Python / GitHub Actions | Fetch RentCast records, synchronize Neon, and publish the snapshot |

On the public site, the browser first loads `Golden_Listings.json`, then requests
`/listings` from FastAPI on Render. FastAPI reads Neon and returns JSON; browser
JavaScript renders the response. The free backend can take time to wake after
inactivity, so displaying the snapshot avoids waiting for it before showing listings.

**Filtering differs by environment:** the public frontend filters its loaded data
in JavaScript. Locally, Apply Filter sends `min_rent` and `max_rent` to FastAPI,
which applies the bounds in a parameterized SQL query. Reset reloads all records
locally and restores the loaded records on the public site.

Visitor requests and filter clicks do not call RentCast. Only the updater fetches
external rental data. Database records and the snapshot reflect the last successful
refresh; they are not guaranteed to represent every available rental in Golden.

## Run locally

Use Python 3.13, as specified in `.python-version`, and a PostgreSQL database
(Neon or a local instance). The following commands use Windows PowerShell and
should be run from the project root.

### 1. Install dependencies

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend/requirements.txt
```

Skip virtual environment creation if `.venv` already exists. Activation is not
required when using its Python executable directly.

### 2. Initialize a new database

Run `backend/schema.sql` in the database's SQL editor to create `listings`.
For a new setup, also create the updater's request ledger:

```sql
CREATE TABLE rentcast_request_attempts (
    id BIGINT GENERATED ALWAYS AS IDENTITY PRIMARY KEY,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);
```

(These are initialization steps, not migrations to rerun against existing tables.)

To seed the database from the committed snapshot without calling RentCast:

```powershell
.\.venv\Scripts\python.exe backend/import_listings.py
```

Enter a raw Neon connection string when prompted. Leave it blank to use the
importer's local PostgreSQL defaults and enter the local password instead.
This importer inserts or updates IDs; it does not remove records absent from the
snapshot. Nonpositive square footage is stored as SQL `NULL`.

### 3. Start the backend

In the first terminal, set the connection string and start Uvicorn:

```powershell
$env:DATABASE_URL = [System.Net.NetworkCredential]::new("", (Read-Host "Paste PostgreSQL connection string" -AsSecureString)).Password
.\.venv\Scripts\python.exe -m uvicorn backend.main:app --reload
```

Paste the raw connection URL, beginning with `postgresql://`, with the actual
password and without surrounding quotes or a `psql` command. This environment
variable belongs to that terminal session and must be set again in a new session.
The application does not automatically load a `.env` file.

### 4. Start the frontend

In a second terminal at the project root:

```powershell
.\.venv\Scripts\python.exe -m http.server 5500 --bind 127.0.0.1
```

Open [the local website](http://127.0.0.1:5500/). Keep both terminals running;
press Ctrl+C in each to stop its server. A local PostgreSQL instance must also be
running if used instead of Neon. The published website runs independently of these
local servers and does not require your computer to stay on.

## API

| Endpoint | Behavior |
| --- | --- |
| `GET /alive` | Application health response; does not check database connectivity |
| `GET /listings` | Database records, optionally filtered by `min_rent` and `max_rent` |
| `GET /docs` | Interactive FastAPI documentation |

Example: `http://127.0.0.1:8000/listings?min_rent=800&max_rent=2000`.
Bounds are inclusive, must be finite and nonnegative, and the minimum cannot
exceed the maximum. Results are ordered by rent, then listing ID. CORS allows
the local frontend origins and `https://chrispy6.github.io`.

## Automated refresh and deployment

`.github/workflows/refresh-listings.yml` runs on `main`:

| Trigger | Refresh RentCast data | Publish website |
| --- | --- | --- |
| Push to `main` | No | Yes |
| Daily schedule (`17 8 * * *`, 08:17 UTC) | Yes | Yes, after successful preceding steps |
| Manual workflow run | Only when the `refresh` checkbox is selected | Yes |

Configure GitHub Pages to use **GitHub Actions** as its publishing source. Add
these **repository secrets** under Settings → Secrets and variables → Actions:

- `DATABASE_URL`: the Neon PostgreSQL connection string.
- `RENTCAST_API_KEY`: the RentCast API key.

Render also needs `DATABASE_URL`. Its build command is
`pip install -r backend/requirements.txt`; its start command is
`python -m uvicorn backend.main:app --host 0.0.0.0 --port $PORT`.
Keep credential values out of source code and committed files.

Each refresh:

1. Commits an attempt reservation in Neon before sending a RentCast request.
2. Requests active Golden, CO listings, up to 500 records, and checks the total
   count to reject incomplete results rather than automatically fetching more pages.
3. Validates nonempty results, unique IDs, addresses, location, and active status,
   then writes `Golden_Listings.pending.json`.
4. Imports that file into Neon in one transaction, inserting or updating records
   and removing Golden, CO records absent from the response.
5. Copies the validated response to `Golden_Listings.json`, commits changes if
   needed, and deploys the four public frontend files to GitHub Pages.

The updater permits **40 attempts in a rolling 35-day window**. A database lock
serializes budget checks and reservations. Database failures stop the request;
failed HTTP requests still consume a reservation. There is no automatic HTTP retry.
Manual RentCast calls outside this script are not counted, so this is an application
guardrail, not a provider-enforced account spending cap.

GitHub schedules can be delayed and public-repository schedules disable after
60 days without repository activity. Check Actions for refresh failures. Database
updates and website publishing are separate operations: if publishing fails after
a database update, the public snapshot may temporarily lag behind Neon.

The workflow can commit updated snapshots remotely. Run `git pull` before a new
coding session, after committing or otherwise preserving unfinished local changes.

## Manual refresh

In a terminal with `DATABASE_URL` set, supply the API key:

```powershell
$env:RENTCAST_API_KEY = [System.Net.NetworkCredential]::new("", (Read-Host "Paste RentCast API key" -AsSecureString)).Password
.\.venv\Scripts\python.exe backend/update_listings.py
.\.venv\Scripts\python.exe backend/sync_pending.py
```

The first script attempts one RentCast request after reserving budget. The second
reads the saved pending file without another request. Run them in order, and stop
if either fails. After a successful sync, copy the pending file over
`Golden_Listings.json`, commit, and push to publish the matching snapshot. The
pending file and its temporary write file are ignored by Git.

## Manual verification

- Load the public site: snapshot listings appear, then the status changes to
  **Showing database records.** when the backend responds.
- Block the Render `/listings` request in browser developer tools: the saved
  snapshot remains usable, including filtering and reset. Unblock afterward.
- Try a valid rent range, empty bounds, equal bounds, a range with no matches,
  negative values, and a minimum greater than the maximum.
- Reset clears both inputs and restores the full loaded dataset.
- Verify local `/listings` query parameters filter database records.
- Compare counts after a refresh; counts change over time and are not fixed test
  expectations.

## Project files

| File | Purpose |
| --- | --- |
| `index.html`, `style.css` | Page structure, controls, and responsive listing cards |
| `script.js` | Data loading, rendering, filtering, and snapshot fallback |
| `Golden_Listings.json` | Committed snapshot for the public site |
| `backend/main.py` | FastAPI routes, CORS, and parameterized database query |
| `backend/schema.sql` | Listings table definition |
| `backend/import_listings.py` | Manual snapshot importer for initial setup |
| `backend/update_listings.py` | Request reservation, RentCast fetch, and validation |
| `backend/sync_pending.py` | Transactional synchronization from the pending response |
| `backend/requirements.txt` | Python dependencies |
| `.github/workflows/refresh-listings.yml` | Daily refresh and frontend deployment |

## Scope and limitations

This MVP provides rent-range search over the latest imported active listings.
Historical price tracking, deal scoring, maps, and user accounts are not implemented.
The refresh stops on empty or incomplete results rather than replacing the dataset;
queries exceeding 500 listings require a future pagination change. Listings are
provider-supplied records, not independently verified availability.


## Development Assistance

I used ChatGPT for explanations, debugging, implementation guidance, and help with documentation. I integrated and tested the application while learning the technologies involved. Other sources like GeeksforGeeks and W3Schools were used for additional explinations and coding syntax.

## License

MIT; see [LICENSE](LICENSE).
