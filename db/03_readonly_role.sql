-- A login that can only read data. Model-written SQL runs as this user,
-- so even a harmful query (DROP, DELETE, UPDATE) is refused by the database itself.
CREATE ROLE eval_reader LOGIN PASSWORD 'eval_reader';
GRANT CONNECT ON DATABASE rushmore TO eval_reader;
GRANT USAGE ON SCHEMA public TO eval_reader;
GRANT SELECT ON ALL TABLES IN SCHEMA public TO eval_reader;
ALTER ROLE eval_reader SET statement_timeout = '5s';
ALTER ROLE eval_reader SET default_transaction_read_only = on;