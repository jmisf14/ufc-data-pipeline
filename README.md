## UFC Stats Data Pipeline

A Scrapy + Postgres data pipeline that continuously collects fight, fighter, and event statistics from `ufcstats.com`, loads them into Postgres, and supports automated weekly refreshes (via GitHub Actions) for downstream analytics and machine learning.

### What this repo contains

- **Scraper**: Scrapy spider (`ufcstatspider`) that crawls events → fights → fighters.
- **Loader**: a Scrapy item pipeline that creates tables (if needed) and inserts/updates records in Postgres.
- **Local stack (optional)**: Docker Compose services for Postgres, pgAdmin, and Grafana.
- **Production DB**: intended to run against **Supabase Postgres** (managed database).
- **Automation**: scheduled GitHub Actions workflow to refresh data every Monday.

### Data model (tables)

- **`events`**: event metadata (name/date/location/link)
- **`fights`**: fight-level outcomes + round totals + significant-strike breakdowns
- **`fighters`**: fighter bio + record + career rate stats

### How it works (high-level)

- **Incremental by date**: the pipeline reads the latest `events.date` already stored in the database and only scrapes/loads newer events.
- **Upserts by logic**:
  - events/fights are inserted in batches at the end of the crawl
  - fighters are inserted if new, otherwise updated (to keep fighter stats fresh)

### Prerequisites

- **Python**: 3.10+ (for local runs)
- **Docker Desktop**: for the local stack (optional)
- **Supabase project**: if you want a managed Postgres database

---

## Run locally (Docker Compose)

### 1) Create a `.env`

Create a `.env` file in the project root (values are examples):

```bash
POSTGRES_DB=ufcstats
POSTGRES_USER=ufc
POSTGRES_PASSWORD=change_me
POSTGRES_HOST=db
POSTGRES_PORT=5432

PGADMIN_DEFAULT_EMAIL=you@example.com
PGADMIN_DEFAULT_PASSWORD=change_me

MAILTO=you@example.com
```

### 2) Start the stack

```bash
docker compose up -d --build
```

### 3) Run the scraper now (don’t wait for cron)

```bash
docker compose exec app bash -lc 'cd /stat_scrape && scrapy crawl ufcstatspider'
```

### 4) Verify data loaded

```bash
docker compose exec db bash -lc 'psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "select count(*) from events; select count(*) from fights; select count(*) from fighters;"'
```

### 5) UI tools

- **pgAdmin**: `http://localhost:8888`
- **Grafana**: `http://localhost:3000`

---

## Supabase (managed Postgres)

### One-time migration (local → Supabase)

1) **Dump** your local Docker DB:

```bash
docker compose exec -T db pg_dump -U "$POSTGRES_USER" -d "$POSTGRES_DB" --format=custom --no-owner --no-privileges > ufcstats.dump
```

2) **Restore** to Supabase:

- Use Supabase dashboard → **Connect → Database**
- Prefer **Session pooler** for IPv4 environments
- Supabase requires SSL (`sslmode=require`)

```bash
pg_restore --no-owner --no-privileges \
  --dbname "postgresql://<SUPABASE_USER>:<SUPABASE_PASSWORD>@<SUPABASE_HOST>:<SUPABASE_PORT>/postgres?sslmode=require" \
  ufcstats.dump
```

### Export CSV (for ML / analysis)

- **Table Editor**: select table → export CSV
- **SQL Editor**: run a query → Export → CSV

---

## Automation: GitHub Actions (every Monday)

This repo is designed to run the scraper on a schedule and write results into **Supabase Postgres**.

### 1) Add GitHub Secrets

In GitHub: **Settings → Secrets and variables → Actions**, create:

- **`SUPABASE_DB_HOST`**
- **`SUPABASE_DB_PORT`**
- **`SUPABASE_DB_NAME`** (usually `postgres`)
- **`SUPABASE_DB_USER`** (pooler often looks like `postgres.<project-ref>`)
- **`SUPABASE_DB_PASSWORD`**

### 2) Add a scheduled workflow

Create `.github/workflows/supabase_scrape.yml` that:

- runs `scrapy crawl ufcstatspider`
- reads DB creds from Secrets
- sets `PGSSLMODE=require`
- uses a Monday `cron` schedule (note: cron is UTC)

### 3) Validate

- Trigger the workflow once with **Run workflow**
- Verify in Supabase:

```sql
select max(date) as newest_event_date, count(*) as total_events from events;
```

---

## Notes / disclaimers

- **Data source**: this project scrapes `ufcstats.com`. Be mindful of the site’s terms and robots policies.
- **Credits**: inspired by the original pipeline design described in [sterlingmaxclark.com](https://sterlingmaxclark.com/ufc-stats-data-pipeline/#elementor-toc__heading-anchor-0) and the upstream repo at [sterling-c/UFCstats-Data-Pipeline](https://github.com/sterling-c/UFCstats-Data-Pipeline).
