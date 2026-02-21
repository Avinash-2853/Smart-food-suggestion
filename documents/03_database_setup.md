# Database Setup & Seeding Guide

This document outlines how to set up the local PostgreSQL database and ingest the CSV data using Docker. 

## Overview
We've set up a `docker-compose.yml` file that orchestrates two services:
1. `db`: A PostGIS enabled PostgreSQL container which automatically configures the database schema on initialization using the `scripts/init_schema.sql` (which was extracted from the `data-model.md` design).
2. `seeder`: A Python container that runs the data ingestion script (`scripts/seed_data.py`). It mounts the local `data/` and `scripts/` directories and automatically starts ingestion after the `db` is healthy.

## Prerequisites
- Docker and Docker Compose installed.

## Files Created/Updated
1. `docker-compose.yml`: Core orchestration file mapping volumes and environments.
2. `scripts/init_schema.sql`: Extracted SQL chunks containing our relational schema.
3. `scripts/seed_data.py`: Updated to use the local `data` directory and connect using standard `DATABASE_URL` environment variables rather than a shared config codebase.
4. `Dockerfile.seeder`: The lightweight Python image to install the `asyncpg` dependency.
5. `requirements.seeder.txt`: Python dependencies required for the seeding script.

## Setup Instructions

Simply run the following command in the root of the project to build the containers and start the database and seed ingestion process:

```bash
docker compose up --build
```

**What to expect:**
1. The Postgres database will initialize and run the `init_schema.sql` to establish the tables (`restaurants`, `menu_categories`, `menu_items`, etc).
2. The seeder container will wait until the database is healthy.
3. The seeder script will parse `df_restaurants.csv`, `df_menu_categories.csv`, and `df_menuitems.csv` and dump the contents into the respective SQL tables, resolving relationships (UUIDs) on the fly.

Once you see `✅ Seeding completed successfully!` from the seeder, the ingestion is fully completed!
