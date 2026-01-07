"""
Mock Data Generator - Enhanced Edition
Generates DISTINCT realistic synthetic workload data for testing
"""

import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from typing import Dict


class MockDataGenerator:
    """Generates realistic time-series metrics with distinct patterns"""
    
    def generate_bursty_service_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Generate data for a BURSTY STATELESS SERVICE
        
        Characteristics:
        - Traffic spikes during business hours
        - Significant idle periods at night
        - Strong diurnal pattern
        - Variable CPU with bursts
        """
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days * 24 * 60,
            freq='1min'
        )
        n = len(timestamps)
        
        # Strong diurnal pattern (business hours 9AM-6PM)
        hour_of_day = timestamps.hour.values
        diurnal_pattern = np.where(
            (hour_of_day >= 9) & (hour_of_day <= 18),
            np.sin((hour_of_day - 9) * np.pi / 9) * 0.8 + 0.2,  # Peak during business
            0.05  # Near zero at night
        )
        
        # Add random bursts during active hours
        burst_mask = (np.random.rand(n) > 0.85) & (diurnal_pattern > 0.1)
        bursts = np.where(burst_mask, np.random.uniform(0.4, 0.8, n), 0)
        
        # CPU: follows diurnal + bursts
        cpu_values = (diurnal_pattern * 0.3 + bursts * 0.5 + np.random.normal(0, 0.05, n)).clip(0.02, 0.9)
        
        # Memory: more stable but follows pattern loosely
        memory_values = (diurnal_pattern * 0.2 + 0.25 + np.random.normal(0, 0.05, n)).clip(0.15, 0.6)
        
        # Requests: strongly correlated with diurnal
        base_requests = diurnal_pattern * 200
        request_bursts = np.where(burst_mask, np.random.poisson(150, n), 0)
        request_values = (base_requests + request_bursts + np.random.poisson(10, n)).astype(float)
        
        # Instances: scale with load
        instance_values = np.where(request_values > 100, 2, np.where(request_values > 30, 1, 0))
        
        return self._create_dataframes(timestamps, cpu_values, memory_values, 
                                        request_values, instance_values, 'mock-bursty-service')
    
    def generate_always_on_api_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Generate data for an ALWAYS-ON API
        
        Characteristics:
        - Consistent high load 24/7
        - Minimal idle time
        - Low variance
        - Multiple instances always running
        """
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days * 24 * 60,
            freq='1min'
        )
        n = len(timestamps)
        
        # Very consistent CPU usage with small variance
        cpu_base = 0.45
        cpu_values = np.random.normal(cpu_base, 0.06, n).clip(0.30, 0.65)
        
        # Memory very steady
        memory_values = np.random.normal(0.55, 0.04, n).clip(0.45, 0.70)
        
        # Requests: consistently high with small variance
        request_values = np.random.normal(400, 40, n).clip(250, 600)
        
        # Slight diurnal variation (but minimal)
        hour_of_day = timestamps.hour.values
        slight_diurnal = 1 + 0.1 * np.sin((hour_of_day - 12) * np.pi / 12)
        request_values = request_values * slight_diurnal
        
        # Instances: always 3+ running
        instance_values = np.random.choice([3, 4], n, p=[0.7, 0.3])
        
        return self._create_dataframes(timestamps, cpu_values, memory_values,
                                        request_values, instance_values, 'mock-always-on-api')
    
    def generate_over_provisioned_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Generate data for an OVER-PROVISIONED CONTAINER
        
        Characteristics:
        - Very low CPU usage
        - High idle time
        - Resources far exceed needs
        - Wasteful configuration
        """
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days * 24 * 60,
            freq='1min'
        )
        n = len(timestamps)
        
        # Very low CPU - beta distribution skewed low
        cpu_values = np.random.beta(1.5, 12, n) * 0.25  # Peaks around 5-10%
        
        # Occasional tiny spikes
        spike_mask = np.random.rand(n) > 0.98
        cpu_values[spike_mask] = np.random.uniform(0.15, 0.22, spike_mask.sum())
        
        # Memory: also very low
        memory_values = np.random.beta(2, 10, n) * 0.35  # Low memory usage
        
        # Requests: very sparse
        request_values = np.random.poisson(3, n).astype(float)
        
        # Many zero periods
        zero_mask = np.random.rand(n) > 0.25
        request_values[zero_mask] = 0
        
        # Instances: always at least 1 running (wasteful!)
        instance_values = np.ones(n)
        
        return self._create_dataframes(timestamps, cpu_values, memory_values,
                                        request_values, instance_values, 'mock-over-provisioned')
    
    def generate_event_driven_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Generate data for an EVENT-DRIVEN / SPIKY workload
        
        Characteristics:
        - Extreme spikes followed by complete idle
        - Very high burstiness
        - Triggered by external events
        """
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days * 24 * 60,
            freq='1min'
        )
        n = len(timestamps)
        
        # Mostly idle with rare extreme spikes
        cpu_values = np.random.beta(1, 20, n) * 0.05  # Almost always near 0
        
        # Add 3-4 spikes per day
        spikes_per_day = 4
        total_spikes = int(days * spikes_per_day)
        spike_indices = np.random.choice(n, total_spikes, replace=False)
        
        for idx in spike_indices:
            # Each spike lasts 5-15 minutes
            spike_duration = np.random.randint(5, 15)
            end_idx = min(idx + spike_duration, n)
            cpu_values[idx:end_idx] = np.random.uniform(0.6, 0.95, end_idx - idx)
        
        # Memory follows CPU pattern
        memory_values = cpu_values * 0.6 + 0.1
        
        # Requests: zero most of time, huge during spikes
        request_values = np.zeros(n)
        for idx in spike_indices:
            spike_duration = np.random.randint(5, 15)
            end_idx = min(idx + spike_duration, n)
            request_values[idx:end_idx] = np.random.uniform(500, 2000, end_idx - idx)
        
        # Instances: scale dramatically with spikes
        instance_values = np.where(cpu_values > 0.3, np.random.randint(3, 8, n), 0)
        
        return self._create_dataframes(timestamps, cpu_values, memory_values,
                                        request_values, instance_values, 'mock-event-driven')
    
    def generate_background_worker_data(self, days: int = 7) -> Dict[str, pd.DataFrame]:
        """
        Generate data for a BACKGROUND WORKER
        
        Characteristics:
        - Low external traffic
        - Steady CPU for processing
        - Single instance
        - Queue-based workload
        """
        timestamps = pd.date_range(
            end=datetime.now(),
            periods=days * 24 * 60,
            freq='1min'
        )
        n = len(timestamps)
        
        # Steady moderate CPU (processing queue)
        cpu_values = np.random.normal(0.35, 0.08, n).clip(0.15, 0.55)
        
        # Memory steady
        memory_values = np.random.normal(0.40, 0.05, n).clip(0.30, 0.55)
        
        # Very low external requests (internal queue processing)
        request_values = np.random.poisson(2, n).astype(float)
        
        # Always single instance
        instance_values = np.ones(n)
        
        return self._create_dataframes(timestamps, cpu_values, memory_values,
                                        request_values, instance_values, 'mock-background-worker')
    
    def _create_dataframes(self, timestamps, cpu, memory, requests, instances, resource_id):
        """Helper to create consistent dataframe structure"""
        return {
            'cpu_utilization': pd.DataFrame({
                'timestamp': timestamps,
                'value': cpu,
                'resource_id': resource_id,
                'resource_type': 'cloud_run_revision',
                'metric_type': 'run.googleapis.com/container/cpu/utilizations'
            }),
            'memory_utilization': pd.DataFrame({
                'timestamp': timestamps,
                'value': memory,
                'resource_id': resource_id,
                'resource_type': 'cloud_run_revision',
                'metric_type': 'run.googleapis.com/container/memory/utilizations'
            }),
            'request_count': pd.DataFrame({
                'timestamp': timestamps,
                'value': requests,
                'resource_id': resource_id,
                'resource_type': 'cloud_run_revision',
                'metric_type': 'run.googleapis.com/request_count'
            }),
            'instance_count': pd.DataFrame({
                'timestamp': timestamps,
                'value': instances,
                'resource_id': resource_id,
                'resource_type': 'cloud_run_revision',
                'metric_type': 'run.googleapis.com/container/instance_count'
            })
        }


if __name__ == "__main__":
    print("Testing Enhanced Mock Data Generator...")
    print("=" * 60)
    
    generator = MockDataGenerator()
    
    workloads = {
        'Bursty Service': generator.generate_bursty_service_data(7),
        'Always-On API': generator.generate_always_on_api_data(7),
        'Over-Provisioned': generator.generate_over_provisioned_data(7)
    }
    
    for name, metrics in workloads.items():
        cpu = metrics['cpu_utilization']['value']
        req = metrics['request_count']['value']
        idle_pct = (cpu < 0.05).mean() * 100
        
        print(f"\n{name}:")
        print(f"  CPU: mean={cpu.mean()*100:.1f}%, p95={cpu.quantile(0.95)*100:.1f}%")
        print(f"  Requests: mean={req.mean():.1f}, p95={req.quantile(0.95):.1f}")
        print(f"  Idle time: {idle_pct:.0f}%")
        print(f"  Burstiness: {req.quantile(0.95) / max(req.mean(), 1):.1f}x")
    
    print("\n✅ Data generation complete!")
