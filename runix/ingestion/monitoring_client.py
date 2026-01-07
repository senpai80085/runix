"""
Cloud Monitoring Client
Fetches time-series metrics from Google Cloud Monitoring API
"""

from google.cloud import monitoring_v3
from google.api_core import retry
import pandas as pd
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import PROJECT_ID, MONITORING_LOOKBACK_DAYS


class MonitoringClient:
    """Client for fetching metrics from Cloud Monitoring"""
    
    def __init__(self, project_id: str = PROJECT_ID):
        self.project_id = project_id
        self.client = monitoring_v3.MetricServiceClient()
        self.project_name = f"projects/{project_id}"
    
    def list_monitored_resources(self, resource_type: Optional[str] = None) -> List[Dict]:
        """
        List all monitored resources in the project
        
        Args:
            resource_type: Optional filter (e.g., 'cloud_run_revision')
            
        Returns:
            List of resource dictionaries with type and labels
        """
        query = monitoring_v3.ListTimeSeriesRequest(
            name=self.project_name,
            filter='metric.type="run.googleapis.com/request_count"',
            interval=monitoring_v3.TimeInterval(
                {
                    "end_time": {"seconds": int(datetime.now().timestamp())},
                    "start_time": {"seconds": int((datetime.now() - timedelta(days=1)).timestamp())},
                }
            ),
        )
        
        resources = []
        try:
            results = self.client.list_time_series(request=query)
            for result in results:
                resource = {
                    'type': result.resource.type,
                    'labels': dict(result.resource.labels)
                }
                if resource not in resources:
                    resources.append(resource)
        except Exception as e:
            print(f"Warning: Could not list resources: {e}")
            
        return resources
    
    @retry.Retry(deadline=60)
    def fetch_timeseries(
        self,
        metric_type: str,
        resource_type: str = "cloud_run_revision",
        resource_labels: Optional[Dict] = None,
        hours_back: int = None
    ) -> pd.DataFrame:
        """
        Fetch time-series data for a specific metric
        
        Args:
            metric_type: Full metric type (e.g., 'run.googleapis.com/container/cpu/utilizations')
            resource_type: Resource type to filter
            resource_labels: Optional resource label filters
            hours_back: Hours to look back (default: MONITORING_LOOKBACK_DAYS * 24)
            
        Returns:
            pandas DataFrame with columns: timestamp, value, resource_id, labels
        """
        if hours_back is None:
            hours_back = MONITORING_LOOKBACK_DAYS * 24
        
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)
        
        # Build filter
        filter_parts = [f'metric.type="{metric_type}"']
        filter_parts.append(f'resource.type="{resource_type}"')
        
        if resource_labels:
            for key, value in resource_labels.items():
                filter_parts.append(f'resource.label.{key}="{value}"')
        
        filter_str = " AND ".join(filter_parts)
        
        # Create request
        interval = monitoring_v3.TimeInterval(
            {
                "end_time": {"seconds": int(end_time.timestamp())},
                "start_time": {"seconds": int(start_time.timestamp())},
            }
        )
        
        aggregation = monitoring_v3.Aggregation(
            {
                "alignment_period": {"seconds": 60},  # 1-minute intervals
                "per_series_aligner": monitoring_v3.Aggregation.Aligner.ALIGN_MEAN,
            }
        )
        
        request = monitoring_v3.ListTimeSeriesRequest(
            name=self.project_name,
            filter=filter_str,
            interval=interval,
            aggregation=aggregation,
        )
        
        # Fetch data
        try:
            results = self.client.list_time_series(request=request)
            
            data = []
            for result in results:
                resource_id = self._extract_resource_id(result.resource)
                
                for point in result.points:
                    data.append({
                        'timestamp': point.interval.end_time.timestamp(),
                        'value': self._extract_value(point.value),
                        'resource_id': resource_id,
                        'resource_type': result.resource.type,
                        'metric_type': metric_type,
                        'labels': dict(result.resource.labels)
                    })
            
            if not data:
                print(f"Warning: No data found for {metric_type}")
                return pd.DataFrame()
            
            df = pd.DataFrame(data)
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='s')
            return df.sort_values('timestamp')
            
        except Exception as e:
            print(f"Error fetching {metric_type}: {e}")
            return pd.DataFrame()
    
    def fetch_cloud_run_metrics(self, service_name: Optional[str] = None) -> Dict[str, pd.DataFrame]:
        """
        Fetch all relevant metrics for Cloud Run services
        
        Args:
            service_name: Optional service name filter
            
        Returns:
            Dictionary of metric_name -> DataFrame
        """
        resource_labels = {}
        if service_name:
            resource_labels['service_name'] = service_name
        
        metrics = {
            'cpu_utilization': 'run.googleapis.com/container/cpu/utilizations',
            'memory_utilization': 'run.googleapis.com/container/memory/utilizations',
            'request_count': 'run.googleapis.com/request_count',
            'instance_count': 'run.googleapis.com/container/instance_count',
        }
        
        results = {}
        for name, metric_type in metrics.items():
            print(f"Fetching {name}...")
            df = self.fetch_timeseries(
                metric_type=metric_type,
                resource_type="cloud_run_revision",
                resource_labels=resource_labels
            )
            if not df.empty:
                results[name] = df
        
        return results
    
    def _extract_resource_id(self, resource) -> str:
        """Extract a unique identifier from resource labels"""
        labels = resource.labels
        # Prioritize service_name, fall back to other identifiers
        if 'service_name' in labels:
            return labels['service_name']
        elif 'revision_name' in labels:
            return labels['revision_name']
        elif 'configuration_name' in labels:
            return labels['configuration_name']
        else:
            return str(labels)
    
    def _extract_value(self, value) -> float:
        """Extract numeric value from Value proto"""
        if value.double_value is not None:
            return value.double_value
        elif value.int64_value is not None:
            return float(value.int64_value)
        elif value.distribution_value is not None:
            return value.distribution_value.mean
        else:
            return 0.0


# Test function for development
if __name__ == "__main__":
    client = MonitoringClient()
    
    print(f"Testing Monitoring Client for project: {PROJECT_ID}")
    print("=" * 60)
    
    # List resources
    print("\n1. Listing monitored resources...")
    resources = client.list_monitored_resources()
    if resources:
        print(f"Found {len(resources)} resources:")
        for r in resources[:5]:  # Show first 5
            print(f"  - {r['type']}: {r['labels'].get('service_name', 'N/A')}")
    else:
        print("No resources found (expected if no Cloud Run services deployed)")
    
    # Test metric fetch (will be empty if no services)
    print("\n2. Testing metric fetch...")
    metrics = client.fetch_cloud_run_metrics()
    if metrics:
        for metric_name, df in metrics.items():
            print(f"  - {metric_name}: {len(df)} data points")
    else:
        print("No metrics fetched (expected if no Cloud Run services exist)")
    
    print("\n✅ Monitoring client test complete!")
