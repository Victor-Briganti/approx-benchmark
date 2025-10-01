INSTALL json;
LOAD json;

CREATE SEQUENCE IF NOT EXISTS "hardware_sequence" START 1;
CREATE TABLE IF NOT EXISTS "hardware" (
	"id" BIGINT PRIMARY KEY DEFAULT nextval('hardware_sequence'),
	"cpu_description" VARCHAR NOT NULL,
	"hertz" DECIMAL(3, 2) NOT NULL,
	"physical_cores" BIGINT NOT NULL,
	"num_threads" BIGINT NOT NULL,
	"gb_ram" FLOAT NOT NULL,
	"operating_system" VARCHAR NOT NULL,
	"hostname" VARCHAR
);

CREATE SEQUENCE IF NOT EXISTS "benchmark_sequence" START 1;
CREATE TABLE IF NOT EXISTS "benchmark" (
	"id" BIGINT PRIMARY KEY DEFAULT nextval('benchmark_sequence'),
	"name" VARCHAR NOT NULL,
	"version" BIGINT NOT NULL,
	"description" VARCHAR,
	"canceled" BOOLEAN NOT NULL DEFAULT false
);

CREATE SEQUENCE IF NOT EXISTS "input_sequence" START 1;
CREATE TABLE IF NOT EXISTS "input" (
	"id" BIGINT PRIMARY KEY DEFAULT nextval('input_sequence') ,
	"benchmark_id" BIGINT NOT NULL REFERENCES "benchmark"("id"),
	"version" BIGINT NOT NULL,
	"binary" BOOLEAN,
	"arguments" JSON
);

CREATE TABLE IF NOT EXISTS "input_binary" (
	"input_id" BIGINT PRIMARY KEY REFERENCES "input"("id"),
	"data" BLOB NOT NULL
);

CREATE SEQUENCE IF NOT EXISTS "run_sequence" START 1;
CREATE TABLE IF NOT EXISTS "run" (
	"id" BIGINT PRIMARY KEY DEFAULT nextval('run_sequence'),
	"benchmark_id" BIGINT NOT NULL REFERENCES "benchmark"("id"),
	"hardware_id" BIGINT NOT NULL REFERENCES "hardware"("id"),
	"thread" BIGINT NOT NULL,
	"type" VARCHAR NOT NULL, -- Can be base, omp, approx or common
	"execution_num" BIGINT NOT NULL,
	"approx_technique" VARCHAR,
	"approx_level" DOUBLE,
	"start_time" TIMESTAMP,
	"end_time" TIMESTAMP
);

CREATE TABLE IF NOT EXISTS "performance_stat" (
	"run_id" BIGINT REFERENCES "run"("id"),
	"metric_name" VARCHAR,
	"metric_value" DOUBLE NOT NULL,
	PRIMARY KEY ("run_id", "metric_name")
);

CREATE TABLE IF NOT EXISTS "run_error" (
	"run_id" BIGINT PRIMARY KEY REFERENCES "run"("id"),
	"error_num" BIGINT NOT NULL,
	"error_code" VARCHAR,
	"error_string" VARCHAR
);