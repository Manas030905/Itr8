-- Runs once, the first time the Postgres container initialises its data volume.
-- The main `itr8` database is created by POSTGRES_DB; tests need their own.
CREATE DATABASE itr8_test OWNER itr8;
