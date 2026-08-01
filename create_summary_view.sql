-- Create Summary view in database_v1.db
-- This view aggregates speedup and quality metric statistics for each benchmark application.

CREATE OR REPLACE VIEW Summary AS
WITH 
baseline AS (
  SELECT 
  eg.bench_name,
  eg.bench_version,
  AVG(p.value) AS base_elapsed
  FROM ExecutionGroup eg
  JOIN Performance p ON eg.id = p.group_id
  WHERE eg.type = 'omp' 
  AND eg.num_threads = 1 
  AND p.name = 'elapsed'
  GROUP BY eg.bench_name, eg.bench_version
),

speedup_data AS (
  SELECT 
  eg.bench_name,
  (b.base_elapsed / p.value) AS speedup,
  eg.approx_type AS technique,
  eg.num_threads,
  eg.approx_rate AS argument,
  p.exec_id,
  p.group_id
  FROM ExecutionGroup eg
  JOIN Performance p ON eg.id = p.group_id
  JOIN baseline b ON eg.bench_name = b.bench_name AND eg.bench_version = b.bench_version
  WHERE eg.approx_type IS NOT NULL 
  AND p.name = 'elapsed'
),

ranked_max_speedup AS (
  SELECT *,
  ROW_NUMBER() OVER (
    PARTITION BY bench_name 
    ORDER BY speedup DESC, exec_id ASC, group_id ASC
  ) AS rn
  FROM speedup_data
),

ranked_min_speedup AS (
  SELECT *,
  ROW_NUMBER() OVER (
    PARTITION BY bench_name 
    ORDER BY speedup ASC, exec_id ASC, group_id ASC
  ) AS rn
  FROM speedup_data
),

quality_data AS (
  SELECT 
  eg.bench_name,
  qm.name AS metric_name,
  qm.value AS quality_value,
  eg.approx_type AS technique,
  eg.num_threads,
  eg.approx_rate AS argument,
  qm.exec_id,
  qm.group_id
  FROM QualityMetrics qm
  JOIN ExecutionGroup eg ON qm.group_id = eg.id
  WHERE eg.approx_type IS NOT NULL
),

ranked_best_quality AS (
  SELECT *,
  ROW_NUMBER() OVER (
    PARTITION BY bench_name 
    ORDER BY 
    CASE WHEN metric_name = 'SSIM' THEN quality_value ELSE -quality_value END DESC,
      exec_id ASC,
      group_id ASC
    ) AS rn
    FROM quality_data
  ),

  ranked_worst_quality AS (
    SELECT *,
    ROW_NUMBER() OVER (
      PARTITION BY bench_name 
      ORDER BY 
      CASE WHEN metric_name = 'SSIM' THEN quality_value ELSE -quality_value END ASC,
        exec_id ASC,
        group_id ASC
      ) AS rn
      FROM quality_data
    )

    SELECT 
    max_sp.bench_name AS application,

    -- Maximum speedup details
    max_sp.speedup AS max_speedup,
    max_sp.technique AS max_speedup_technique,
    max_sp.num_threads AS max_speedup_threads,
    max_sp.argument AS max_speedup_argument,

    -- Minimum speedup details
    min_sp.speedup AS min_speedup,
    min_sp.technique AS min_speedup_technique,
    min_sp.num_threads AS min_speedup_threads,
    min_sp.argument AS min_speedup_argument,

    -- Best quality result details
    best_q.quality_value AS best_quality,
    best_q.technique AS best_quality_technique,
    best_q.num_threads AS best_quality_threads,
    best_q.argument AS best_quality_argument,

    -- Worst quality result details
    worst_q.quality_value AS worst_quality,
    worst_q.technique AS worst_quality_technique,
    worst_q.num_threads AS worst_quality_threads,
    worst_q.argument AS worst_quality_argument

    FROM (SELECT * FROM ranked_max_speedup WHERE rn = 1) max_sp
    JOIN (SELECT * FROM ranked_min_speedup WHERE rn = 1) min_sp ON max_sp.bench_name = min_sp.bench_name
    JOIN (SELECT * FROM ranked_best_quality WHERE rn = 1) best_q ON max_sp.bench_name = best_q.bench_name
    JOIN (SELECT * FROM ranked_worst_quality WHERE rn = 1) worst_q ON max_sp.bench_name = worst_q.bench_name
    ORDER BY application;
