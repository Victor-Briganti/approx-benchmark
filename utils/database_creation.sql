INSTALL json;
LOAD json;

CREATE SEQUENCE IF NOT EXISTS "ExperimentSeq" START 1;
CREATE TABLE IF NOT EXISTS "Experiment" (
  "id" BIGINT DEFAULT nextval('ExperimentSeq'),

  "yaml_snapshot" TEXT NOT NULL,
  "commit" CHAR(40) NOT NULL,

  PRIMARY KEY ("id")
);

CREATE TABLE IF NOT EXISTS "Server" (
  "hostname" VARCHAR PRIMARY KEY,

  "cpu_description" VARCHAR NOT NULL,
  "hertz" DECIMAL(3,2) NOT NULL,
  "cores" INTEGER NOT NULL,
  "threads" INTEGER NOT NULL,
  "ram_memory" INTEGER NOT NULL,
  "operating_system" VARCHAR NOT NULL,
);

CREATE TABLE IF NOT EXISTS "Benchmark" (
  "name" VARCHAR ,
  "version" INTEGER,

  "path" VARCHAR NOT NULL,
  "setup" VARCHAR,
  "description" VARCHAR,
  "canceled" BOOLEAN NOT NULL DEFAULT false,

  PRIMARY KEY ("name", "version")
);

CREATE SEQUENCE IF NOT EXISTS "ExecGroupSeq" START 1;
CREATE TABLE IF NOT EXISTS "ExecutionGroup" (
  "id" BIGINT DEFAULT nextval('ExecGroupSeq'),

  "type" VARCHAR NOT NULL,
  "approx_type" VARCHAR,
  "approx_rate" INTEGER,

  "compile_command" VARCHAR,
  "num_threads" INTEGER NOT NULL,

  "server" VARCHAR NOT NULL,
  "bench_name" VARCHAR NOT NULL,
  "bench_version" INTEGER NOT NULL,

  PRIMARY KEY ("id"),
  FOREIGN KEY ("server")
  REFERENCES "Server" ("hostname"),
  FOREIGN KEY ("bench_name", "bench_version")
  REFERENCES "Benchmark" ("name", "version"),
);

CREATE TABLE IF NOT EXISTS "Execution" (
  "id" BIGINT,
  "group_id" BIGINT,

  "start_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "end_time" TIMESTAMP,

  PRIMARY KEY ("id", "group_id"),
  FOREIGN KEY ("group_id")
  REFERENCES "ExecutionGroup" ("id"),
);

CREATE TABLE IF NOT EXISTS "ExecutionInput" (
  "group_id" BIGINT,

  "input" JSON,

  PRIMARY KEY ("group_id"),
  FOREIGN KEY ("group_id")
  REFERENCES "ExecutionGroup" ("id")
);

CREATE TABLE IF NOT EXISTS "ExecutionEnv" (
  "group_id" BIGINT,
  "name" VARCHAR,
  "value" VARCHAR,

  PRIMARY KEY ("group_id", "name", "value"),
  FOREIGN KEY ("group_id")
  REFERENCES "ExecutionGroup" ("id"),
);

CREATE TABLE IF NOT EXISTS "ExecutionError" (
  "group_id" BIGINT,
  "exec_id" BIGINT,

  "errno" INTEGER NOT NULL,
  "code" VARCHAR NOT NULL,
  "description" VARCHAR,

  PRIMARY KEY ("group_id", "exec_id"),
  FOREIGN KEY ("exec_id", "group_id")
  REFERENCES "Execution" ("id", "group_id"),
);

CREATE TABLE IF NOT EXISTS "Performance" (
  "name" VARCHAR,
  "exec_id" BIGINT,
  "group_id" BIGINT,

  "value" DOUBLE NOT NULL,

  PRIMARY KEY ("name", "group_id", "exec_id"),
  FOREIGN KEY ("exec_id", "group_id")
  REFERENCES "Execution" ("id", "group_id"),
);

CREATE TABLE IF NOT EXISTS "QualityMetrics" (
  "name" VARCHAR,
  "group_id" BIGINT,
  "exec_id" BIGINT,

  "value" DOUBLE NOT NULL,

  PRIMARY KEY ("name", "exec_id", "group_id"),
  FOREIGN KEY ("exec_id", "group_id")
  REFERENCES "Execution" ("id", "group_id"),
);

