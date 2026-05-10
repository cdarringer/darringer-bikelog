# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Project Does

**darringer-bikelog** is a CLI tool for tracking family bike rides. It logs rides to year-organized CSV files (`data/rides/rides_YYYY.csv`), generates an interactive metrics report, and publishes everything to AWS S3.

## Running the Application

```bash
# Log a ride
python bikelog.py --rider "Chris" --distance 15 --bike "Cannondale ST400"

# Log a past ride
python bikelog.py --date 2026-03-15 --rider "Chris" --distance 20 --bike "Torelli"

# List available options
python bikelog.py --list-bikes
python bikelog.py --list-riders

# Generate metrics report (opens in browser)
python brm.py

# Generate for a specific year without opening browser
python brm.py --year 2024 --no-open

# Publish CSVs + HTML report to S3
python brp.py

# Log bike maintenance
python bml.py --bike "Cannondale ST400" --activity "Tune-up" --cost 75.00 --shop "Bicycles NYC"
python bml.py --date 2026-04-15 --bike "Torelli" --activity "New chain" --cost 35.00

# List maintenance records
python bml.py --list
python bml.py --list --bike "Cannondale ST400" --limit 50
```

There are no automated tests. Verification is done manually by inspecting CSV output.

## Architecture

Four scripts, one concern each: `bikelog.py` (log rides), `brm.py` (generate metrics), `brp.py` (publish to S3), `bml.py` (log maintenance). Each has a matching bash wrapper (`brb`, `brm`, `brp`, `bml`). The `brb.py` file is an outdated stub — ignore it.

**Data flow:**
1. `main()` parses CLI args (argparse) and routes to a handler
2. Ride logging: validates rider/bike against `DEFAULT_RIDERS`/`DEFAULT_BIKES`, then `log_ride()` prepends the new record (reverse chronological) to the year's CSV
3. Metrics: `brm.py` loads all CSVs, generates three Plotly charts, writes a self-contained HTML file to `data/rides/bikelog.html`
4. S3 publish: `brp.py` reads `bikelog.ini` for bucket/region/prefix, uses MD5 hashing to skip unchanged files; uploads both CSVs, `bikelog.html`, and `maintenance.csv`
5. Maintenance logging: `bml.py` validates the bike name, auto-calculates lifetime mileage from rides CSVs as of the log date, and prepends the record to `data/maintenance/maintenance.csv`

**Rides CSV format:** `Date, Name, Distance, Bike, Comment` — date stored as MM/DD/YYYY, files named `rides_YYYY.csv`

**Maintenance CSV format:** `Date, Bike, Activity, Cost, Shop` — single file `data/maintenance/maintenance.csv`, newest first; mileage is derived on demand from the rides CSVs

**S3 config** (`bikelog.ini`):
```ini
[s3]
bucket = darringer-public
region = us-east-1
prefix = bikelog/
```
AWS credentials are resolved via `aws configure` or environment variables (not stored in the repo).

## Dependencies

```bash
pip install -r requirements.txt  # boto3 (S3 publishing), plotly + pandas (metrics)
```
