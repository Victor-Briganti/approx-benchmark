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

CREATE SEQUENCE IF NOT EXISTS "ExecutionSeq" START 1;
CREATE TABLE IF NOT EXISTS "Execution" (
	"id" BIGINT DEFAULT nextval('ExecutionSeq'),

  "type" VARCHAR NOT NULL,
  "approx_rate" INTEGER,
  CHECK (
     ("type" = 'common') OR ("type" = 'omp') OR ("approx_rate" IS NOT NULL)
  ),

  "compile_command" VARCHAR,
  "exec_num" INTEGER NOT NULL,
  "num_threads" INTEGER NOT NULL,
  "start_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "end_time" TIMESTAMP,

  "server" VARCHAR NOT NULL,
  "bench_name" VARCHAR NOT NULL,
  "bench_version" INTEGER NOT NULL,
  "exp_id" BIGINT NOT NULL,
  
  PRIMARY KEY ("id"),
  FOREIGN KEY ("server")
    REFERENCES "Server" ("hostname"),
  FOREIGN KEY ("bench_name", "bench_version")
    REFERENCES "Benchmark" ("name", "version"),
  FOREIGN KEY ("exp_id")
    REFERENCES "Experiment" ("id")
);

CREATE TABLE IF NOT EXISTS "ExecutionInput" (
  "exec_id" BIGINT,

  "input" JSON,

  PRIMARY KEY ("exec_id"),
  FOREIGN KEY ("exec_id")
    REFERENCES "Execution" ("id")
);

CREATE TABLE IF NOT EXISTS "ExecutionEnv" (
	"exec_id" BIGINT,
  "name" VARCHAR,
  "value" VARCHAR,
  
  PRIMARY KEY ("exec_id", "name", "value"),
  FOREIGN KEY ("exec_id")
    REFERENCES "Execution" ("id"),
);

CREATE TABLE IF NOT EXISTS "ExecutionError" (
	"exec_id" BIGINT,

  "errno" INTEGER NOT NULL,
  "code" VARCHAR NOT NULL,
  "description" VARCHAR,
  
  PRIMARY KEY ("exec_id"),
  FOREIGN KEY ("exec_id")
    REFERENCES "Execution" ("id"),
);

CREATE TABLE IF NOT EXISTS "Performance" (
	"name" VARCHAR,
	"exec_id" BIGINT,

  "value" DOUBLE NOT NULL,

  PRIMARY KEY ("name", "exec_id"),
  FOREIGN KEY ("exec_id")
    REFERENCES "Execution" ("id"),
);

CREATE TABLE IF NOT EXISTS "QualityMetrics" (
	"name" VARCHAR,
	"exec_id" BIGINT,

  "value" DOUBLE NOT NULL,

  PRIMARY KEY ("name", "exec_id"),
  FOREIGN KEY ("exec_id")
    REFERENCES "Execution" ("id"),
);

