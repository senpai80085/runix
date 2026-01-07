"""
Runix Dashboard Server with Gemini AI
Beautiful visual dashboard with AI-powered explanations
"""

from flask import Flask, jsonify, render_template, request
from flask_cors import CORS
import pandas as pd
import numpy as np
import sys
import os
import logging
from datetime import datetime

sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from runix.tests.mock_data_generator import MockDataGenerator
from runix.intelligence.feature_extractor import FeatureExtractor
from runix.intelligence.classifier import WorkloadClassifier
from runix.optimization.cost_optimizer import CostOptimizer
from runix.ingestion.monitoring_client import MonitoringClient
from runix.intelligence.gemini_explainer import GeminiExplainer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__, template_folder='templates')
CORS(app)

# Initialize components
feature_extractor = FeatureExtractor()
classifier = WorkloadClassifier()
cost_optimizer = CostOptimizer()
generator = MockDataGenerator()

# Gemini AI (uses GEMINI_API_KEY env variable)
gemini_explainer = GeminiExplainer(api_key=os.getenv('GEMINI_API_KEY'))

# Try to initialize monitoring client (might fail if no credentials)
try:
    monitoring_client = MonitoringClient()
    logger.info("Monitoring client initialized successfully")
except Exception as e:
    logger.warning(f"Failed to initialize monitoring client: {e}")
    monitoring_client = None


@app.route('/')
def dashboard():
    """Serve the visual dashboard"""
    return render_template('dashboard.html')


@app.route('/health')
def health():
    """Health check"""
    status = {
        'status': 'healthy',
        'gemini_enabled': gemini_explainer.enabled,
        'live_monitoring_enabled': monitoring_client is not None
    }
    return jsonify(status)


@app.route('/analyze', methods=['POST'])
def analyze_live():
    """Analyze a REAL Cloud Run service using live metrics"""
    if not monitoring_client:
        return jsonify({'error': 'Monitoring client not initialized (check GCP credentials)'}), 500
        
    try:
        data = request.json
        service_name = data.get('service_name')
        
        if not service_name:
            return jsonify({'error': 'service_name is required'}), 400
            
        logger.info(f"Analyzing live service: {service_name}")
        
        # 1. Fetch real metrics
        metrics = monitoring_client.fetch_cloud_run_metrics(service_name=service_name)
        
        if not metrics:
            return jsonify({
                'error': f'No metrics found for service "{service_name}". Need at least 1 hour of traffic.'
            }), 404
            
        # 2. Extract features
        features = feature_extractor.extract_features(metrics, service_name)
        
        # 3. Classify workload
        classification = classifier.classify(features)
        
        # 4. Generate optimization recommendation
        recommendation = cost_optimizer.generate_recommendation(features, classification)
        
        # 5. Generate AI Explanation (Gemini)
        ai_explanation = gemini_explainer.generate_explanation(
            classification, recommendation, features
        )
        
        response = {
            'success': True,
            'service_name': service_name,
            'is_mock': False,
            'classification': {
                'workload_type': classification['workload_type'],
                'confidence': f"{classification['confidence']*100:.0f}%",
                'reasoning': classification['reasoning']
            },
            'cost_optimization': {
                'current_monthly': f"${recommendation['cost_impact']['current_monthly_usd']:.2f}",
                'optimized_monthly': f"${recommendation['cost_impact']['optimized_monthly_usd']:.2f}",
                'savings': f"${recommendation['cost_impact']['savings_usd']:.2f}",
                'savings_percentage': f"{recommendation['cost_impact']['savings_percentage']:.0f}%",
                'risk_level': recommendation['risk_level'],
                'within_free_tier': recommendation['cost_impact']['within_free_tier']
            },
            'ai_explanation': ai_explanation,
            'gemini_powered': gemini_explainer.enabled,
            'explanation': recommendation['explanation'],
            'implementation_steps': recommendation['implementation_steps']
        }
        
        return jsonify(response)
        
    except Exception as e:
        logger.error(f"Analysis failed: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/analyze/mock', methods=['GET', 'POST'])
def analyze_mock():
    """Analyze mock workload data with AI explanation"""
    try:
        if request.method == 'POST':
            data = request.get_json() or {}
            workload_type = data.get('workload_type', 'bursty')
        else:
            workload_type = request.args.get('type', 'bursty')
        
        # Generate mock data
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
            return jsonify({'error': f'Invalid workload_type: {workload_type}'}), 400
        
        # Extract features
        features = feature_extractor.extract_features(metrics, resource_id)
        
        # Classify workload
        classification = classifier.classify(features)
        
        # Generate recommendation
        recommendation = cost_optimizer.generate_recommendation(features, classification)
        
        # Generate AI explanation
        ai_explanation = gemini_explainer.generate_explanation(classification, recommendation, features)
        
        # Build response
        return jsonify({
            'success': True,
            'resource_id': resource_id,
            'classification': {
                'workload_type': classification['workload_type'],
                'confidence': f"{classification['confidence']*100:.0f}%",
                'reasoning': classification['reasoning']
            },
            'cost_optimization': {
                'current_monthly': f"${recommendation['cost_impact']['current_monthly_usd']:.2f}",
                'optimized_monthly': f"${recommendation['cost_impact']['optimized_monthly_usd']:.2f}",
                'savings': f"${recommendation['cost_impact']['savings_usd']:.2f}",
                'savings_percentage': f"{recommendation['cost_impact']['savings_percentage']:.0f}%",
                'risk_level': recommendation['risk_level'],
                'within_free_tier': recommendation['cost_impact']['within_free_tier']
            },
            'ai_explanation': ai_explanation,
            'gemini_powered': gemini_explainer.enabled,
            'explanation': recommendation['explanation'],
            'implementation_steps': recommendation['implementation_steps'],
            'timestamp': datetime.utcnow().isoformat()
        })
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            'success': False,
            'error': str(e)
        }), 500


if __name__ == '__main__':
    print()
    print("=" * 60)
    print("  🚀 RUNIX WORKLOAD INTELLIGENCE DASHBOARD")
    print("=" * 60)
    print()
    print("  Dashboard: http://localhost:8080")
    print()
    if gemini_explainer.enabled:
        print("  🤖 Gemini AI: ENABLED ✓")
    else:
        print("  ⚠️  Gemini AI: Not configured")
        print("     Set GEMINI_API_KEY for AI-powered explanations")
    
    if monitoring_client:
        print(f"  📡 Live Monitoring: ENABLED (Project: {monitoring_client.project_id}) ✓")
    else:
        print("  ⚠️  Live Monitoring: DISABLED (No credentials found)")
        
    print()
    print("=" * 60)
    print()
    
    app.run(host='0.0.0.0', port=8080, debug=True)
