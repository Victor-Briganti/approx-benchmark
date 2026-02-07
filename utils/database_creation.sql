INSTALL json;
LOAD json;

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
  
  "description" VARCHAR,
  "canceled" BOOLEAN NOT NULL DEFAULT false,

  PRIMARY KEY ("name", "version")
);

CREATE TABLE IF NOT EXISTS "BenchmarkInput" (
  "name" VARCHAR,
  "version" INTEGER,
  
  "input" JSON,

  PRIMARY KEY ("name", "version"),
  FOREIGN KEY ("name", "version")
    REFERENCES "Benchmark" ("name", "version")
);

CREATE SEQUENCE IF NOT EXISTS "ExecutionSeq" START 1;
CREATE TABLE IF NOT EXISTS "Execution" (
	"id" BIGINT DEFAULT nextval('ExecutionSeq'),

  "type" VARCHAR NOT NULL,
  "approx_rate" INTEGER,
  CHECK (
    ("type" != 'common')
    OR ("approx_rate" IS NOT NULL)
  ),

  "exec_num" INTEGER NOT NULL,
  "threads" INTEGER NOT NULL,
  "start_time" TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
  "end_time" TIMESTAMP,

  "server" VARCHAR NOT NULL,
  "bench_name" VARCHAR NOT NULL,
  "bench_version" INTEGER NOT NULL,
  
  PRIMARY KEY ("id"),
  FOREIGN KEY ("server")
    REFERENCES "Server" ("hostname"),
  FOREIGN KEY ("bench_name", "bench_version")
    REFERENCES "Benchmark" ("name", "version")
);

CREATE TABLE IF NOT EXISTS "ExecError" (
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

