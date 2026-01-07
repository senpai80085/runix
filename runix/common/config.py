"""
Runix Configuration
Centralized configuration for all components
"""

import os

# GCP Configuration
PROJECT_ID = os.getenv('PROJECT_ID', 'warm-ring-483118-v9')
REGION = os.getenv('REGION', 'asia-south1')
BIGQUERY_DATASET = os.getenv('BIGQUERY_DATASET', 'runix')

# Cloud Monitoring Configuration
MONITORING_LOOKBACK_DAYS = int(os.getenv('MONITORING_LOOKBACK_DAYS', '7'))
METRIC_AGGREGATION_MINUTES = int(os.getenv('METRIC_AGGREGATION_MINUTES', '60'))

# Feature Extraction Thresholds
CPU_IDLE_THRESHOLD = 5.0  # CPU % below this is considered idle
MEMORY_IDLE_THRESHOLD = 10.0  # Memory % below this is considered idle
BURSTINESS_THRESHOLD = 3.0  # p95/mean ratio indicating bursty traffic

# Classification Confidence Thresholds
MIN_CONFIDENCE_SCORE = 0.6  # Minimum confidence to make recommendation
HIGH_CONFIDENCE_THRESHOLD = 0.8  # Threshold for high-confidence classification

# Cost Optimization Settings
# Google Cloud Run pricing (asia-south1)
# https://cloud.google.com/run/pricing
CPU_COST_PER_VCPU_SECOND = 0.00002400  # $0.000024 per vCPU-second
MEMORY_COST_PER_GB_SECOND = 0.00000250  # $0.0000025 per GB-second
REQUEST_COST = 0.0000004  # $0.0000004 per request

# Free tier limits
FREE_TIER_CPU_SECONDS = 180000  # 180K vCPU-seconds/month
FREE_TIER_MEMORY_GB_SECONDS = 360000  # 360K GB-seconds/month
FREE_TIER_REQUESTS = 2000000  # 2M requests/month

# Workload Classification Types
WORKLOAD_TYPES = [
    "Bursty Stateless Service",
    "Always-On API",
    "Event-Driven / Spiky",
    "Background Worker",
    "Over-Provisioned Container"
]

# Risk Levels
RISK_LEVELS = ["Low", "Medium", "High"]

# BigQuery Table Names
TABLE_RAW_METRICS = f"{BIGQUERY_DATASET}.raw_metrics"
TABLE_ENGINEERED_FEATURES = f"{BIGQUERY_DATASET}.engineered_features"
TABLE_WORKLOAD_CLASSIFICATIONS = f"{BIGQUERY_DATASET}.workload_classifications"
TABLE_OPTIMIZATION_RECOMMENDATIONS = f"{BIGQUERY_DATASET}.optimization_recommendations"
