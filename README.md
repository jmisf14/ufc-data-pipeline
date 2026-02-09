## UFC Data Pipeline

This repository powers my capstone **UFC analytics + prediction** project by keeping a Postgres database continuously updated with structured data scraped from `ufcstats.com`.

### What this project does

- **Scrapes** UFC events, fights, and fighters from `ufcstats.com`
- **Stores** the data in Postgres (hosted on **Supabase** for the capstone)
- **Refreshes automatically** on a weekly schedule (GitHub Actions) so new events get appended
- **Enables analytics/ML workflows**: the tables can be queried directly or exported to CSV for feature engineering and model training

### How it works (high level)

- A Scrapy spider (`ufcstatspider`) crawls: **events → fight cards → fight details → fighter pages**
- A pipeline writes to Postgres:
  - creates tables if needed
  - inserts new events/fights
  - inserts new fighters or updates existing fighters
- The job is intended to run on a schedule so the database stays current.

### Core tables

- **`events`**: event metadata (name, date, location, link)
- **`fights`**: fight outcomes + detailed striking/grappling stats
- **`fighters`**: fighter bios, records, and career rate stats

### Data platform & automation

- **Database**: Supabase Postgres
- **Scheduler**: GitHub Actions (weekly run)

### Credits

This work is based on the original pipeline concept and implementation from:

- [sterling-c/UFCstats-Data-Pipeline](https://github.com/sterling-c/UFCstats-Data-Pipeline)
- [sterlingmaxclark.com: UFC stats data pipeline write-up](https://sterlingmaxclark.com/ufc-stats-data-pipeline/#elementor-toc__heading-anchor-0)
