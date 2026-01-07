"""
Feature Extractor
Transforms raw time-series metrics into analytical features
"""

import pandas as pd
import numpy as np
from typing import Dict, List, Tuple
from datetime import datetime, timedelta
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import (
    CPU_IDLE_THRESHOLD, 
    MEMORY_IDLE_THRESHOLD,
    BURSTINESS_THRESHOLD
)


class FeatureExtractor:
    """Extracts analytical features from raw time-series metrics"""
    
    def __init__(self):
        self.cpu_idle_threshold = CPU_IDLE_THRESHOLD
        self.memory_idle_threshold = MEMORY_IDLE_THRESHOLD
    
    def extract_features(self, metrics: Dict[str, pd.DataFrame], resource_id: str) -> Dict:
        """
        Extract features from metrics for a specific resource
        
        Args:
            metrics: Dict of metric_name -> DataFrame
            resource_id: Resource identifier
            
        Returns:
            Dictionary of extracted features
        """
        features = {
            'resource_id': resource_id,
            'window_start': None,
            'window_end': None,
        }
        
        # Extract CPU features
        if 'cpu_utilization' in metrics:
            cpu_df = metrics['cpu_utilization']
            cpu_df = cpu_df[cpu_df['resource_id'] == resource_id]
            if not cpu_df.empty:
                features.update(self._extract_cpu_features(cpu_df))
                features['window_start'] = cpu_df['timestamp'].min()
                features['window_end'] = cpu_df['timestamp'].max()
        
        # Extract memory features
        if 'memory_utilization' in metrics:
            mem_df = metrics['memory_utilization']
            mem_df = mem_df[mem_df['resource_id'] == resource_id]
            if not mem_df.empty:
                features.update(self._extract_memory_features(mem_df))
        
        # Extract request features
        if 'request_count' in metrics:
            req_df = metrics['request_count']
            req_df = req_df[req_df['resource_id'] == resource_id]
            if not req_df.empty:
                features.update(self._extract_request_features(req_df))
        
        # Extract concurrency features
        if 'instance_count' in metrics:
            inst_df = metrics['instance_count']
            inst_df = inst_df[inst_df['resource_id'] == resource_id]
            if not inst_df.empty:
                features.update(self._extract_concurrency_features(inst_df))
        
        # Calculate composite features
        features.update(self._calculate_composite_features(features))
        
        return features
    
    def _extract_cpu_features(self, df: pd.DataFrame) -> Dict:
        """Extract CPU utilization features"""
        values = df['value'].values * 100  # Convert to percentage
        
        return {
            'cpu_mean': float(np.mean(values)),
            'cpu_stddev': float(np.std(values)),
            'cpu_p50': float(np.percentile(values, 50)),
            'cpu_p95': float(np.percentile(values, 95)),
            'cpu_p99': float(np.percentile(values, 99)),
            'cpu_min': float(np.min(values)),
            'cpu_max': float(np.max(values)),
        }
    
    def _extract_memory_features(self, df: pd.DataFrame) -> Dict:
        """Extract memory utilization features"""
        values = df['value'].values * 100  # Convert to percentage
        
        return {
            'memory_mean': float(np.mean(values)),
            'memory_stddev': float(np.std(values)),
            'memory_p50': float(np.percentile(values, 50)),
            'memory_p95': float(np.percentile(values, 95)),
            'memory_min': float(np.min(values)),
            'memory_max': float(np.max(values)),
        }
    
    def _extract_request_features(self, df: pd.DataFrame) -> Dict:
        """Extract request rate features"""
        values = df['value'].values
        
        # Calculate requests per minute
        df_sorted = df.sort_values('timestamp')
        if len(df_sorted) > 1:
            time_diffs = df_sorted['timestamp'].diff().dt.total_seconds() / 60  # minutes
            request_rates = values[1:] / time_diffs[1:].values
        else:
            request_rates = values
        
        return {
            'request_rate_mean': float(np.mean(request_rates)),
            'request_rate_stddev': float(np.std(request_rates)),
            'request_rate_p50': float(np.percentile(request_rates, 50)),
            'request_rate_p95': float(np.percentile(request_rates, 95)),
            'request_rate_max': float(np.max(request_rates)),
            'total_requests': float(np.sum(values)),
        }
    
    def _extract_concurrency_features(self, df: pd.DataFrame) -> Dict:
        """Extract concurrency (instance count) features"""
        values = df['value'].values
        
        return {
            'concurrency_mean': float(np.mean(values)),
            'concurrency_stddev': float(np.std(values)),
            'concurrency_p50': float(np.percentile(values, 50)),
            'concurrency_p95': float(np.percentile(values, 95)),
            'concurrency_max': float(np.max(values)),
        }
    
    def _calculate_composite_features(self, features: Dict) -> Dict:
        """Calculate composite features from basic metrics"""
        composite = {}
        
        # Burstiness score (ratio of p95 to mean requests)
        if 'request_rate_mean' in features and features['request_rate_mean'] > 0:
            composite['burstiness_score'] = features['request_rate_p95'] / features['request_rate_mean']
        else:
            composite['burstiness_score'] = 1.0
        
        # Idle ratio (percentage of time CPU is below threshold)
        if 'cpu_mean' in features:
            # Estimate: if mean is below threshold, high idle ratio
            # This is simplified; real implementation would analyze full time series
            if features['cpu_mean'] < self.cpu_idle_threshold:
                composite['idle_ratio'] = 0.8
            elif features['cpu_mean'] < self.cpu_idle_threshold * 2:
                composite['idle_ratio'] = 0.5
            else:
                composite['idle_ratio'] = max(0.0, 1.0 - (features['cpu_mean'] / 100.0))
        else:
            composite['idle_ratio'] = 0.5
        
        # Active hours per day (estimate based on request patterns)
        if 'request_rate_mean' in features and 'request_rate_max' in features:
            if features['request_rate_max'] > 0:
                activity_ratio = features['request_rate_mean'] / features['request_rate_max']
                composite['active_hours_per_day'] = activity_ratio * 24
            else:
                composite['active_hours_per_day'] = 24.0
        else:
            composite['active_hours_per_day'] = 24.0
        
        # Diurnal pattern strength (simplified - would use FFT in production)
        # For now, use stddev as proxy for pattern strength
        if 'request_rate_stddev' in features and 'request_rate_mean' in features:
            if features['request_rate_mean'] > 0:
                cv = features['request_rate_stddev'] / features['request_rate_mean']
                composite['diurnal_pattern_strength'] = min(1.0, cv / 2)  # Normalized
            else:
                composite['diurnal_pattern_strength'] = 0.0
        else:
            composite['diurnal_pattern_strength'] = 0.0
        
        # Cost idle ratio (percentage of cost wasted on idle)
        composite['cost_idle_ratio'] = composite['idle_ratio'] * 100
        
        # Efficiency score (inverse of idle ratio)
        composite['efficiency_score'] = (1.0 - composite['idle_ratio']) * 100
        
        # Over-provision penalty
        if 'cpu_p95' in features:
            if features['cpu_p95'] < 30:
                composite['over_provision_penalty'] = 70 - features['cpu_p95']
            else:
                composite['over_provision_penalty'] = 0.0
        else:
            composite['over_provision_penalty'] = 0.0
        
        return composite


# Test function
if __name__ == "__main__":
    print("Testing Feature Extractor with synthetic data...")
    
    # Create synthetic metrics
    timestamps = pd.date_range(start='2026-01-01', periods=100, freq='1min')
    
    metrics = {
        'cpu_utilization': pd.DataFrame({
            'timestamp': timestamps,
            'value': np.random.beta(2, 5, 100) * 0.5,  # Low CPU usage
            'resource_id': 'test-service'
        }),
        'memory_utilization': pd.DataFrame({
            'timestamp': timestamps,
            'value': np.random.normal(0.3, 0.1, 100),
            'resource_id': 'test-service'
        }),
        'request_count': pd.DataFrame({
            'timestamp': timestamps,
            'value': np.random.poisson(10, 100),
            'resource_id': 'test-service'
        }),
        'instance_count': pd.DataFrame({
            'timestamp': timestamps,
            'value': np.random.choice([0, 1, 2], 100, p=[0.3, 0.5, 0.2]),
            'resource_id': 'test-service'
        })
    }
    
    extractor = FeatureExtractor()
    features = extractor.extract_features(metrics, 'test-service')
    
    print("\nExtracted Features:")
    print("=" * 60)
    for key, value in features.items():
        if isinstance(value, float):
            print(f"{key:30s}: {value:10.2f}")
        else:
            print(f"{key:30s}: {value}")
    
    print("\n✅ Feature extraction test complete!")
