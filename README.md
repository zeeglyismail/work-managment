# Worklog

A small, self-hosted web app for logging daily work and producing a monthly PDF report.

It replaces a spreadsheet where times were typed in by hand, and where `=NOW()` changed
every time Excel recalculated. Here you press **Start** when you begin a task and **Stop** when
you finish. Times are recorded once and never change.

## Features

- **One-click timer**: start a task, and starting the next one stops the previous one automatically.
- **Manual entries**: add or fix past work with start and end times, a project and notes.
- **Projects**: colour-coded groups (client, product, kind of work); they can be archived or deleted.
  Deleting a project keeps its entries.
- **Dashboard**: today, this week and this month, a 14-day chart and the time per project.
- **Monthly log**: browse by month, search, filter by project and export to CSV.
- **Monthly PDF report**: totals, time by project, a daily summary and a detailed log.
  - Last month's report is saved automatically once the month ends.
    The app checks every hour, so it still catches up if the server was down on the 1st.
  - You can download a fresh PDF of any month at any time.
- **Single account**: there is no sign-up. The username and password come from `.env`,
  and repeated wrong passwords are throttled.
- Works on a phone, and supports light and dark mode.

## Stack

| Layer    | Choice                                               |
|----------|------------------------------------------------------|
| Frontend | React 18 + TypeScript (Vite)                         |
| Backend  | FastAPI, SQLAlchemy 2                                |
| Database | SQLite (a single file in a Docker volume)            |
| PDF      | reportlab                                            |
| Deploy   | One Docker image (Docker Compose)                    |

## Run with Docker

```bash
cp .env.example .env      # then set APP_PASSWORD, SECRET_KEY, OWNER_NAME
docker compose up -d --build
```

Open http://localhost:9001.

If you are testing over plain HTTP from another machine, set `COOKIE_SECURE=false`.
Otherwise the browser won't keep the session cookie.

The port is bound to `127.0.0.1:9001` only. Put your own reverse proxy or tunnel in front of it.

### Backups

All data lives in the `worklog-data` volume:

- `worklog.db`: the SQLite database
- `reports/`: the saved monthly PDFs

```bash
docker compose cp worklog:/data ./backup-$(date +%F)
```

## Configuration (`.env`)

| Variable        | Default        | Purpose                                              |
|-----------------|----------------|------------------------------------------------------|
| `APP_USERNAME`  | `admin`        | Sign-in username                                     |
| `APP_PASSWORD`  | `change-me`    | Sign-in password                                     |
| `SECRET_KEY`    | dev value      | Signs the session cookie, so keep it long and random |
| `OWNER_NAME`    | empty          | Name printed on the PDF reports                      |
| `TZ_NAME`       | `Asia/Dhaka`   | Timezone for "today", the timer and reports          |
| `COOKIE_SECURE` | `false`        | Set to `true` when served over HTTPS                 |
| `PORT`          | `9001`         | Host port (bound to localhost)                       |

## Backup spreadsheet

[`sheet/Work_Log_Backup.xlsx`](sheet/Work_Log_Backup.xlsx) is a manual backup log for
Google Sheets (File → Import → Upload) or Excel:

- one tab per month, Oct 2026 to Sep 2027, plus a Summary tab
- each day has three In/Out time pairs in 12-hour format
- Working Hours and the monthly totals are calculated automatically

To change the months or the number of In/Out pairs, edit `MONTHS` / `PAIRS` in
`sheet/make_sheet.py` and run `python sheet/make_sheet.py` (requires `openpyxl`).

## Local development

```bash
# API on :8000
cd backend
python -m venv .venv && .venv/Scripts/activate   # or: source .venv/bin/activate
pip install -r requirements-dev.txt
APP_PASSWORD=dev uvicorn app.main:app --reload
pytest

# UI on :5173 (proxies /api to :8000)
cd frontend
npm install
npm run dev
```

The interactive API docs are at `/api/docs`.

## Notes

- Times are stored as local wall-clock time in `TZ_NAME`. This is a one-person log, so
  "which day was this" never depends on the browser's timezone.
- An entry that runs past midnight counts towards the day it started.
- Only one timer can run at a time.
