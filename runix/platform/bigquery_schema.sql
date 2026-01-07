-- Runix BigQuery Schema
-- Dataset: runix (asia-south1 for free tier)
-- Creation: bq mk --location=asia-south1 --dataset warm-ring-483118-v9:runix

-- Table 1: Raw Metrics from Cloud Monitoring
CREATE TABLE IF NOT EXISTS `warm-ring-483118-v9.runix.raw_metrics` (
  timestamp TIMESTAMP NOT NULL,
  resource_type STRING NOT NULL,
  resource_id STRING NOT NULL,
  metric_type STRING NOT NULL,
  value FLOAT64 NOT NULL,
  project_id STRING NOT NULL,
  labels JSON,
  ingested_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(timestamp)
CLUSTER BY resource_id, metric_type
OPTIONS(
  description="Raw time-series metrics from Cloud Monitoring",
  partition_expiration_days=90  -- Auto-cleanup to stay in free tier
);

-- Table 2: Engineered Features
CREATE TABLE IF NOT EXISTS `warm-ring-483118-v9.runix.engineered_features` (
  analysis_id STRING NOT NULL,
  resource_id STRING NOT NULL,
  project_id STRING NOT NULL,
  window_start TIMESTAMP NOT NULL,
  window_end TIMESTAMP NOT NULL,
  
  -- CPU Features
  cpu_mean FLOAT64,
  cpu_stddev FLOAT64,
  cpu_p50 FLOAT64,
  cpu_p95 FLOAT64,
  cpu_p99 FLOAT64,
  
  -- Memory Features
  memory_mean FLOAT64,
  memory_stddev FLOAT64,
  memory_p95 FLOAT64,
  
  -- Request Features
  request_rate_mean FLOAT64,
  request_rate_stddev FLOAT64,
  request_rate_p95 FLOAT64,
  
  -- Pattern Features
  burstiness_score FLOAT64,
  idle_ratio FLOAT64,
  active_hours_per_day FLOAT64,
  diurnal_pattern_strength FLOAT64,
  concurrency_mean FLOAT64,
  concurrency_p95 FLOAT64,
  
  -- Cost Features
  cost_idle_ratio FLOAT64,
  efficiency_score FLOAT64,
  over_provision_penalty FLOAT64,
  
  analyzed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(window_start)
CLUSTER BY resource_id, project_id;

-- Table 3: Workload Classifications
CREATE TABLE IF NOT EXISTS `warm-ring-483118-v9.runix.workload_classifications` (
  classification_id STRING NOT NULL,
  resource_id STRING NOT NULL,
  project_id STRING NOT NULL,
  analysis_id STRING NOT NULL,
  
  -- Classification Results
  workload_type STRING NOT NULL,
  confidence FLOAT64 NOT NULL,
  
  -- Explainability
  reasoning ARRAY<STRING>,
  key_metrics JSON,
  
  -- Metadata
  classified_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP(),
  
  -- Primary key constraint (not enforced, but documented)
  -- PRIMARY KEY (classification_id) NOT ENFORCED
)
PARTITION BY DATE(classified_at)
CLUSTER BY resource_id, workload_type;

-- Table 4: Optimization Recommendations
CREATE TABLE IF NOT EXISTS `warm-ring-483118-v9.runix.optimization_recommendations` (
  recommendation_id STRING NOT NULL,
  resource_id STRING NOT NULL,
  project_id STRING NOT NULL,
  classification_id STRING NOT NULL,
  
  -- Current State
  current_architecture JSON NOT NULL,
  
  -- Recommendation
  recommended_architecture JSON NOT NULL,
  
  -- Cost Impact
  cost_impact JSON NOT NULL,
  
  -- Risk & Explanation
  risk_level STRING NOT NULL,
  explanation ARRAY<STRING>,
  implementation_steps ARRAY<STRING>,
  
  -- Approval Workflow
  approval_status STRING DEFAULT 'pending',
  approved_by STRING,
  approved_at TIMESTAMP,
  
  -- Metadata
  recommended_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP()
)
PARTITION BY DATE(recommended_at)
CLUSTER BY resource_id, approval_status;

-- View: Latest Recommendations per Resource
CREATE OR REPLACE VIEW `warm-ring-483118-v9.runix.latest_recommendations` AS
SELECT 
  r.*,
  c.workload_type,
  c.confidence
FROM (
  SELECT *,
    ROW_NUMBER() OVER (PARTITION BY resource_id ORDER BY recommended_at DESC) as rn
  FROM `warm-ring-483118-v9.runix.optimization_recommendations`
) r
JOIN `warm-ring-483118-v9.runix.workload_classifications` c
  ON r.classification_id = c.classification_id
WHERE r.rn = 1;

-- View: Dashboard Summary
CREATE OR REPLACE VIEW `warm-ring-483118-v9.runix.dashboard_summary` AS
SELECT 
  r.resource_id,
  r.project_id,
  c.workload_type,
  c.confidence,
  f.cpu_mean,
  f.cpu_p95,
  f.memory_mean,
  f.idle_ratio,
  f.burstiness_score,
  f.efficiency_score,
  r.cost_impact,
  r.risk_level,
  r.recommended_at
FROM `warm-ring-483118-v9.runix.latest_recommendations` r
JOIN `warm-ring-483118-v9.runix.engineered_features` f
  ON r.resource_id = f.resource_id
JOIN `warm-ring-483118-v9.runix.workload_classifications` c
  ON r.classification_id = c.classification_id
ORDER BY r.recommended_at DESC;
