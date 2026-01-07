"""
Runix Cloud Run Service
Flask API for workload intelligence analysis
"""

from flask import Flask, request, jsonify
from google.cloud import bigquery
import sys
import os
from datetime import datetime
import json

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from ingestion.monitoring_client import MonitoringClient
from intelligence.feature_extractor import FeatureExtractor
from intelligence.classifier import WorkloadClassifier
from optimization.cost_optimizer import CostOptimizer
from common.config import PROJECT_ID, BIGQUERY_DATASET

app = Flask(__name__)

# Initialize components
monitoring_client = MonitoringClient(PROJECT_ID)
feature_extractor = FeatureExtractor()
classifier = WorkloadClassifier()
optimizer = CostOptimizer()
bq_client = bigquery.Client(project=PROJECT_ID)


@app.route('/')
def index():
    """Health check endpoint"""
    return jsonify({
        'service': 'Runix Workload Intelligence',
        'status': 'operational',
        'version': '1.0.0',
        'project': PROJECT_ID
    })


@app.route('/analyze', methods=['POST'])
def analyze():
    """
    Analyze a workload and generate recommendation
    
    Request body:
    {
        "service_name": "optional-service-name",
        "lookback_hours": 168  # default 7 days
    }
    """
    try:
        data = request.get_json() or {}
        service_name = data.get('service_name')
        lookback_hours = data.get('lookback_hours', 168)
        
        # Fetch metrics from Cloud Monitoring
        app.logger.info(f"Fetching metrics for service: {service_name or 'all'}")
        metrics = monitoring_client.fetch_cloud_run_metrics(service_name)
        
        if not metrics:
            return jsonify({
                'error': 'No metrics found',
                'message': 'No Cloud Run services with sufficient metrics. Use /analyze/mock for testing.'
            }), 404
        
        # Get resource ID
        resource_id = metrics[list(metrics.keys())[0]]['resource_id'].iloc[0]
        
        # Extract features
        app.logger.info(f"Extracting features for {resource_id}")
        features = feature_extractor.extract_features(metrics, resource_id)
        
        # Classify workload
        app.logger.info("Classifying workload")
        classification = classifier.classify(features)
        
        # Generate recommendation
        app.logger.info("Generating cost optimization recommendation")
        recommendation = optimizer.generate_recommendation(
            features, classification
        )
        
        # Store in BigQuery
        _store_results(resource_id, features, classification, recommendation)
        
        # Return results
        return jsonify({
            'resource_id': resource_id,
            'classification': classification,
            'recommendation': recommendation,
            'features': features,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Analysis error: {str(e)}")
        return jsonify({
            'error': 'Analysis failed',
            'message': str(e)
        }), 500


@app.route('/analyze/mock', methods=['POST'])
def analyze_mock():
    """
    Analyze mock workload data (for testing without real services)
    
    Request body:
    {
        "workload_type": "bursty" | "always-on" | "over-provisioned"
    }
    """
    try:
        from tests.mock_data_generator import MockDataGenerator
        
        data = request.get_json() or {}
        workload_type = data.get('workload_type', 'bursty')
        
        # Generate mock data
        generator = MockDataGenerator()
        
        if workload_type == 'bursty':
            metrics = generator.generate_bursty_service_data(7)
            resource_id = 'mock-bursty-service'
        elif workload_type == 'always-on':
            metrics = generator.generate_always_on_api_data(7)
            resource_id = 'mock-always-on-api'
        elif workload_type == 'over-provisioned':
            metrics = generator.generate_over_provisioned_data(7)
            resource_id = 'mock-over-provisioned'
        else:
            return jsonify({'error': 'Invalid workload_type'}), 400
        
        # Extract features
        features = feature_extractor.extract_features(metrics, resource_id)
        
        # Classify workload
        classification = classifier.classify(features)
        
        # Generate recommendation
        recommendation = optimizer.generate_recommendation(
            features, classification
        )
        
        # Return results (don't store mock data)
        return jsonify({
            'resource_id': resource_id,
            'classification': classification,
            'recommendation': recommendation,
            'features': features,
            'mock_data': True,
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        app.logger.error(f"Mock analysis error: {str(e)}")
        return jsonify({
            'error': 'Mock analysis failed',
            'message': str(e)
        }), 500


@app.route('/health')
def health():
    """Kubernetes-style health check"""
    return jsonify({'status': 'healthy'}), 200


def _store_results(resource_id, features, classification, recommendation):
    """Store analysis results in BigQuery"""
    try:
        # Store engineered features
        features_table = f"{PROJECT_ID}.{BIGQUERY_DATASET}.engineered_features"
        features_row = {
            'analysis_id': classification['classification_id'],
            'resource_id': resource_id,
            'project_id': PROJECT_ID,
            'window_start': features.get('window_start'),
            'window_end': features.get('window_end'),
            **{k: v for k, v in features.items() if isinstance(v, (int, float))}
        }
        
        # Store classification
        classification_table = f"{PROJECT_ID}.{BIGQUERY_DATASET}.workload_classifications"
        classification_row = {
            'classification_id': classification['classification_id'],
            'resource_id': resource_id,
            'project_id': PROJECT_ID,
            'analysis_id': classification['classification_id'],
            'workload_type': classification['workload_type'],
            'confidence': classification['confidence'],
            'reasoning': classification['reasoning'],
            'key_metrics': json.dumps(classification['key_metrics'])
        }
        
        # Store recommendation
        recommendation_table = f"{PROJECT_ID}.{BIGQUERY_DATASET}.optimization_recommendations"
        recommendation_row = {
            'recommendation_id': recommendation['recommendation_id'],
            'resource_id': resource_id,
            'project_id': PROJECT_ID,
            'classification_id': classification['classification_id'],
            'current_architecture': json.dumps(recommendation['current_architecture']),
            'recommended_architecture': json.dumps(recommendation['recommended_architecture']),
            'cost_impact': json.dumps(recommendation['cost_impact']),
            'risk_level': recommendation['risk_level'],
            'explanation': recommendation['explanation'],
            'implementation_steps': recommendation['implementation_steps']
        }
        
        # Insert rows
        errors = bq_client.insert_rows_json(features_table, [features_row])
        errors += bq_client.insert_rows_json(classification_table, [classification_row])
        errors += bq_client.insert_rows_json(recommendation_table, [recommendation_row])
        
        if errors:
            app.logger.warning(f"BigQuery insert errors: {errors}")
            
    except Exception as e:
        app.logger.error(f"Failed to store results in BigQuery: {e}")


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8080))
    app.run(host='0.0.0.0', port=port, debug=False)
