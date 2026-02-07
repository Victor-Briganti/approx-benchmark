INSTALL json;
LOAD json;

CREATE TABLE IF NOT EXISTS "server" (
  "hostname" VARCHAR PRIMARY KEY,

  "cpu_description" VARCHAR NOT NULL,
  "hertz" DECIMAL(3, 2) NOT NULL,
  "physical_cores" BIGINT NOT NULL,
  "num_threads" BIGINT NOT NULL,
  "gb_ram" FLOAT NOT NULL,
  "operating_system" VARCHAR NOT NULL
);

CREATE TABLE IF NOT EXISTS "benchmark" (
  "name" VARCHAR NOT NULL,
  "version" BIGINT NOT NULL,

  "description" VARCHAR,
  "canceled" BOOLEAN NOT NULL DEFAULT false,

  PRIMARY KEY ("name", "version")
);

CREATE TABLE IF NOT EXISTS "input" (
  "id" BIGINT NOT NULL,
  "benchmark_name" VARCHAR,
  "benchmark_version" BIGINT NOT NULL,

  "binary" BOOLEAN,
  "arguments" JSON,

  PRIMARY KEY ("id", "benchmark_name", "benchmark_version"),
  FOREIGN KEY ("benchmark_name", "benchmark_version")
  REFERENCES "benchmark" ("name", "version")
);

CREATE TABLE IF NOT EXISTS "run" (
  "id" BIGINT NOT NULL,
  "benchmark_name" VARCHAR NOT NULL,
  "benchmark_version" BIGINT NOT NULL,

  "server_name" VARCHAR NOT NULL,
  "thread" BIGINT NOT NULL,
  CHECK ("thread" >= 1),

  "type" VARCHAR NOT NULL,
  "approx_technique" VARCHAR,
  "approx_rate" DOUBLE,
  CHECK ("type" IN ('common', 'omp', 'approx')),
  CHECK (
    ("type" != 'approx')
    OR ("approx_technique" IS NOT NULL AND "approx_rate" IS NOT NULL)
  ),
  CHECK (
    ("type" = 'approx')
    OR ("approx_technique" IS NULL AND "approx_rate" IS NULL)
  ),

  "start_time" TIMESTAMP,
  "end_time" TIMESTAMP,

  PRIMARY KEY ("id", "benchmark_name", "benchmark_version"),
  FOREIGN KEY ("benchmark_name", "benchmark_version")
  REFERENCES "benchmark" ("name", "version"),
  FOREIGN KEY ("server_name")
  REFERENCES "server" ("hostname")
);

CREATE TABLE IF NOT EXISTS "performance_stat" (
  "run_id" BIGINT,
  "benchmark_name" VARCHAR NOT NULL,
  "benchmark_version" BIGINT NOT NULL,
  "metric_name" VARCHAR,

  "metric_value" DOUBLE NOT NULL,

  PRIMARY KEY ("run_id", "benchmark_name", "benchmark_version", "metric_name"),
  FOREIGN KEY ("run_id", "benchmark_name", "benchmark_version")
  REFERENCES "run" ("id", "benchmark_name", "benchmark_version")
);

CREATE TABLE IF NOT EXISTS "run_error" (
  "run_id" BIGINT,
  "benchmark_name" VARCHAR NOT NULL,
  "benchmark_version" BIGINT NOT NULL,

  "error_num" BIGINT NOT NULL,
  "error_code" VARCHAR,
  "error_string" VARCHAR,

  PRIMARY KEY ("run_id", "benchmark_name", "benchmark_version"),
  FOREIGN KEY ("run_id", "benchmark_name", "benchmark_version")
  REFERENCES "run" ("id", "benchmark_name", "benchmark_version")
);

CREATE TABLE IF NOT EXISTS "quality_metrics" (
  "run_id" BIGINT,
  "benchmark_name" VARCHAR NOT NULL,
  "benchmark_version" BIGINT NOT NULL,

  "metric_name" VARCHAR NOT NULL,
  "metric_value" DOUBLE NOT NULL,

  PRIMARY KEY ("run_id", "benchmark_name", "benchmark_version"),
  FOREIGN KEY ("run_id", "benchmark_name", "benchmark_version")
  REFERENCES "run" ("id", "benchmark_name", "benchmark_version")
);
