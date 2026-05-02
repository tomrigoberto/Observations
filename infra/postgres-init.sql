-- Postgres init: extensions and roles only.
-- Schema is owned by the backend (alembic migrations).

CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
