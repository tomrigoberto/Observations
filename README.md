# IRS Transcript Analyzer

App for analyzing batches of IRS transcripts (HTML) across a client household and surfacing observations from a curated library.

## Architecture

This repo contains the application: FastAPI backend + Next.js frontend + Postgres. The observation library is a separate repo (`tomrigoberto/observations-library`); the app loads it as a sibling checkout for development and as a versioned tarball ("rule pack") in production.

For the full design, see `tomrigoberto/docs` under `irs-transcript-analyzer/`.

## Layout

```
backend/    FastAPI app, parsers, rule engine, library loader, PDF rendering
frontend/   Next.js (App Router) + TypeScript + Tailwind
infra/      Postgres init scripts
```

## Local development

Prereqs: Docker, Node 20+, Python 3.12+ (only if running outside Docker).

```bash
# 1. Place a checkout of the library repo as a sibling directory
ls ../observations-library    # should show the library files

# 2. Boot the stack
make up

# 3. Apps
# Backend  → http://localhost:8000  (docs at /docs)
# Frontend → http://localhost:3000
# Postgres → localhost:5432  (db: observations, user: observations, pass: observations)
```

## Status

Skeleton. See `tomrigoberto/docs/irs-transcript-analyzer/architecture/plan.md` for the roadmap.
