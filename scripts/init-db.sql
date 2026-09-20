-- Runs once, the first time the Postgres container initialises its data volume.
-- The main `builderhub` database is created by POSTGRES_DB; tests need their own.
CREATE DATABASE builderhub_test OWNER builderhub;
