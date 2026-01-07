"""
Runix Test Service
A simple Cloud Run service for testing Runix analysis
"""

from flask import Flask, jsonify
import random
import time
import os

app = Flask(__name__)

@app.route('/')
def home():
    """Simulates variable load for testing"""
    # Simulate different workload patterns
    delay = random.uniform(0.01, 0.1)
    time.sleep(delay)
    
    return jsonify({
        'service': 'runix-test-workload',
        'status': 'ok',
        'latency_ms': round(delay * 1000, 2),
        'message': 'This is a test Cloud Run service for Runix analysis'
    })

@app.route('/health')
def health():
    return jsonify({'status': 'healthy'})

@app.route('/burst')
def burst():
    """Endpoint to simulate bursty behavior"""
    # Heavier processing
    result = sum(i*i for i in range(10000))
    return jsonify({'result': result, 'type': 'burst'})

@app.route('/idle')
def idle():
    """Lightweight endpoint"""
    return jsonify({'status': 'idle'})

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 8081))
    app.run(host='0.0.0.0', port=port, debug=False)
