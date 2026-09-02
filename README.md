# Retail Inventory API

![Python](https://img.shields.io/badge/Python-3.11%2B-blue?style=flat-square&logo=python)
![Django](https://img.shields.io/badge/Django-5.2%2B-092E20?style=flat-square&logo=django)
![SQLModel](https://img.shields.io/badge/SQLModel-ORM-red?style=flat-square)
![Alembic](https://img.shields.io/badge/Alembic-Migrations-6D2024?style=flat-square&logo=sqlalchemy)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15-336791?style=flat-square&logo=postgresql)
![Supabase](https://img.shields.io/badge/Supabase-Cloud%20DB-3ECF8E?style=flat-square&logo=supabase)
![Docker](https://img.shields.io/badge/Docker-Enabled-2496ED?style=flat-square&logo=docker)
![pytest](https://img.shields.io/badge/pytest-97%25%20coverage-brightgreen?style=flat-square&logo=pytest)

## Status

![API](https://img.shields.io/badge/API-Live-success?style=flat-square)
![Render](https://img.shields.io/badge/Deployed%20on-Render-46E3B7?style=flat-square&logo=render)
![Version](https://img.shields.io/badge/version-0.0.0-blue?style=flat-square)
![Last Commit](https://img.shields.io/github/last-commit/chris-kechagias/retail-inventory-api?style=flat-square)
![Commits](https://img.shields.io/github/commit-activity/m/chris-kechagias/retail-inventory-api?style=flat-square&label=Activity)
![License](https://img.shields.io/github/license/chris-kechagias/retail-inventory-api?style=flat-square)

---

## About

A REST API for managing retail product inventory and variants. Built with Django, SQLModel, and PostgreSQL, with structured JSON logging, centralised exception handling, and Docker support.

**Live API:** [retail-inventory-api-yati.onrender.com/docs](https://retail-inventory-api-yati.onrender.com/docs)

---

## Installation

### Prerequisites

- Python 3.11+
- [uv](https://docs.astral.sh/uv/)
- Docker & Docker Compose

### Clone

```bash
git clone https://github.com/chris-kechagias/retail-inventory-api.git
cd retail-inventory-api
```

### Environment variables

Copy `.env.example` to `.env` and fill in the values:

```bash
cp .env.example .env
```

```env
# Local Docker
DB_USERNAME=your_db_user
DB_PASSWORD=your_db_password
DB_HOST=localhost
DB_PORT=5432
DB_NAME=retail_inventory_db

# Supabase (Cloud) — Transaction pooler
# DB_USERNAME=postgres.<your-project-ref>
# DB_PASSWORD=your_supabase_password
# DB_HOST=aws-1-<region>.pooler.supabase.com
# DB_PORT=6543
# DB_NAME=postgres
```

### Option 1: Local (uv)

Install uv if you don't have it:

```bash
pip install uv
```

Install dependencies and start the database:

```bash
uv sync
docker compose up -d db
```

Run the development server:

```bash
task dev
# or manually:
uv run uvicorn main:app --reload
```

### Option 2: Full Docker

```bash
task build
# or manually:
docker compose up --build
```

The API will be available at http://localhost:8000.

---

## Testing

Run the full test suite with:
```bash
uv run pytest -v
```

29 tests covering all endpoints: products, variants, analytics, and health check. Uses SQLite in-memory database — no external dependencies required.

---

## Acknowledgements

Special thanks to [qquorum](https://github.com/qquorum), Senior Software Developer, for code reviews, architectural guidance, and mentorship throughout this project.

---

## Author

**Chris Kechagias**

[![Medium Badge](https://img.shields.io/badge/@ck.chris.kechagias-black?style=flat&logo=medium&logoColor=white&link=https://medium.com/@ck.chris.kechagias)](https://medium.com/@ck.chris.kechagias)<br>
[![GitHub](https://skillicons.dev/icons?i=github)](https://github.com/chris-kechagias)<br>
[![LinkedIn](https://skillicons.dev/icons?i=linkedin)](https://www.linkedin.com/in/chkechagias)<br>
[![dev.to](https://skillicons.dev/icons?i=devto)](https://dev.to/kris_k)<br>



*Transitioning from retail operations to AI engineering.*

**⭐ If you find this project helpful, consider giving it a star!** 