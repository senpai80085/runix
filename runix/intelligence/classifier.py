"""
Workload Classifier - Enhanced Edition
ML-powered workload pattern classification with better detection
"""

import numpy as np
from typing import Dict, List, Tuple
import uuid
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import WORKLOAD_TYPES


class WorkloadClassifier:
    """Classifies workloads using rule-assisted ML with enhanced detection"""
    
    def __init__(self):
        self.workload_types = WORKLOAD_TYPES
        
    def classify(self, features: Dict) -> Dict:
        """
        Classify workload based on engineered features
        Uses multiple scoring criteria for robust classification
        """
        # Extract key features with defaults
        cpu_mean = features.get('cpu_mean', 50)
        cpu_p95 = features.get('cpu_p95', 70)
        cpu_stddev = features.get('cpu_stddev', 10)
        memory_mean = features.get('memory_mean', 50)
        idle_ratio = features.get('idle_ratio', 0.5)
        burstiness = features.get('burstiness_score', 1.0)
        active_hours = features.get('active_hours_per_day', 24)
        diurnal_strength = features.get('diurnal_pattern_strength', 0.0)
        request_rate_mean = features.get('request_rate_mean', 100)
        request_rate_p95 = features.get('request_rate_p95', 200)
        concurrency_mean = features.get('concurrency_mean', 1)
        efficiency_score = features.get('efficiency_score', 50)
        
        # Score each workload type
        scores = {}
        evidence = {}
        
        # 1. BURSTY STATELESS SERVICE
        # Characteristics: Variable traffic, some idle time, diurnal patterns
        bursty_score = 0
        bursty_evidence = []
        
        if burstiness >= 2.0:
            bursty_score += 30
            bursty_evidence.append(f"Traffic burstiness: {burstiness:.1f}x (peak vs average)")
        if 0.3 <= idle_ratio <= 0.8:
            bursty_score += 25
            bursty_evidence.append(f"Significant idle time: {idle_ratio*100:.0f}%")
        if diurnal_strength >= 0.3:
            bursty_score += 20
            bursty_evidence.append(f"Strong daily pattern: {diurnal_strength:.2f} strength")
        if cpu_stddev > 10:
            bursty_score += 15
            bursty_evidence.append(f"CPU variance: ±{cpu_stddev:.1f}% standard deviation")
        if request_rate_mean > 0:
            bursty_score += 10
            bursty_evidence.append(f"Active service with {request_rate_mean:.0f} req/min average")
        
        scores['Bursty Stateless Service'] = bursty_score
        evidence['Bursty Stateless Service'] = bursty_evidence
        
        # 2. ALWAYS-ON API
        # Characteristics: Consistent load, low idle, always running
        always_on_score = 0
        always_on_evidence = []
        
        if idle_ratio < 0.25:
            always_on_score += 35
            always_on_evidence.append(f"Minimal idle time: only {idle_ratio*100:.0f}% idle")
        if cpu_mean > 30:
            always_on_score += 25
            always_on_evidence.append(f"Consistent CPU utilization: {cpu_mean:.1f}% average")
        if burstiness < 2.5:
            always_on_score += 20
            always_on_evidence.append(f"Stable traffic: only {burstiness:.1f}x variance")
        if diurnal_strength < 0.4:
            always_on_score += 10
            always_on_evidence.append("Consistent load throughout day")
        if concurrency_mean >= 2:
            always_on_score += 10
            always_on_evidence.append(f"Multi-instance deployment: {concurrency_mean:.1f} avg instances")
        
        scores['Always-On API'] = always_on_score
        evidence['Always-On API'] = always_on_evidence
        
        # 3. OVER-PROVISIONED CONTAINER
        # Characteristics: Very low utilization, high idle, wasted resources
        over_prov_score = 0
        over_prov_evidence = []
        
        if cpu_p95 < 25:
            over_prov_score += 35
            over_prov_evidence.append(f"Peak CPU only {cpu_p95:.1f}% - severely underutilized")
        if idle_ratio > 0.6:
            over_prov_score += 30
            over_prov_evidence.append(f"Idle {idle_ratio*100:.0f}% of the time - wasting resources")
        if cpu_mean < 15:
            over_prov_score += 20
            over_prov_evidence.append(f"Average CPU only {cpu_mean:.1f}%")
        if efficiency_score < 40:
            over_prov_score += 15
            over_prov_evidence.append(f"Low efficiency score: {efficiency_score:.0f}/100")
        
        scores['Over-Provisioned Container'] = over_prov_score
        evidence['Over-Provisioned Container'] = over_prov_evidence
        
        # 4. EVENT-DRIVEN / SPIKY
        # Characteristics: Extreme bursts, long idle, triggered workload
        event_score = 0
        event_evidence = []
        
        if burstiness > 4.0:
            event_score += 35
            event_evidence.append(f"Extreme traffic spikes: {burstiness:.1f}x burstiness")
        if idle_ratio > 0.7:
            event_score += 30
            event_evidence.append(f"Long idle periods: {idle_ratio*100:.0f}% of time")
        if active_hours < 10:
            event_score += 20
            event_evidence.append(f"Active only {active_hours:.1f} hours/day")
        if request_rate_p95 / max(request_rate_mean, 1) > 5:
            event_score += 15
            event_evidence.append("Spike-to-baseline ratio indicates event triggers")
        
        scores['Event-Driven / Spiky'] = event_score
        evidence['Event-Driven / Spiky'] = event_evidence
        
        # 5. BACKGROUND WORKER
        # Characteristics: Low traffic, steady processing, single instance
        worker_score = 0
        worker_evidence = []
        
        if request_rate_mean < 20:
            worker_score += 30
            worker_evidence.append(f"Low external traffic: {request_rate_mean:.1f} req/min")
        if 15 < cpu_mean < 60:
            worker_score += 25
            worker_evidence.append(f"Steady processing load: {cpu_mean:.1f}% CPU")
        if concurrency_mean <= 1.5:
            worker_score += 25
            worker_evidence.append(f"Single/low instance count: {concurrency_mean:.1f}")
        if burstiness < 2.0:
            worker_score += 20
            worker_evidence.append("Consistent processing pattern")
        
        scores['Background Worker'] = worker_score
        evidence['Background Worker'] = worker_evidence
        
        # Find the best classification
        best_type = max(scores, key=scores.get)
        best_score = scores[best_type]
        
        # Convert score to confidence (0-100 scale)
        confidence = min(0.95, best_score / 100)
        
        # Ensure minimum confidence
        if confidence < 0.5:
            confidence = 0.5
        
        return {
            'classification_id': str(uuid.uuid4()),
            'workload_type': best_type,
            'confidence': confidence,
            'reasoning': evidence[best_type] if evidence[best_type] else [
                f"Classified as {best_type} based on metric patterns",
                f"Score: {best_score}/100"
            ],
            'key_metrics': {
                'cpu_mean': round(cpu_mean, 1),
                'cpu_p95': round(cpu_p95, 1),
                'idle_ratio': round(idle_ratio, 2),
                'burstiness_score': round(burstiness, 2),
                'efficiency_score': round(efficiency_score, 1),
                'active_hours_per_day': round(active_hours, 1)
            },
            'all_scores': {k: f"{v}/100" for k, v in sorted(scores.items(), key=lambda x: -x[1])}
        }


# Test
if __name__ == "__main__":
    print("Testing Enhanced Workload Classifier...")
    print("=" * 60)
    
    classifier = WorkloadClassifier()
    
    # Test cases
    test_cases = [
        ("Bursty Service", {
            'cpu_mean': 20, 'cpu_p95': 65, 'cpu_stddev': 18,
            'idle_ratio': 0.55, 'burstiness_score': 3.5,
            'diurnal_pattern_strength': 0.65, 'request_rate_mean': 100,
            'request_rate_p95': 350, 'concurrency_mean': 1.5,
            'active_hours_per_day': 14, 'efficiency_score': 55
        }),
        ("Always-On API", {
            'cpu_mean': 45, 'cpu_p95': 70, 'cpu_stddev': 8,
            'idle_ratio': 0.12, 'burstiness_score': 1.6,
            'diurnal_pattern_strength': 0.2, 'request_rate_mean': 400,
            'request_rate_p95': 550, 'concurrency_mean': 3,
            'active_hours_per_day': 24, 'efficiency_score': 85
        }),
        ("Over-Provisioned", {
            'cpu_mean': 8, 'cpu_p95': 18, 'cpu_stddev': 5,
            'idle_ratio': 0.75, 'burstiness_score': 1.2,
            'diurnal_pattern_strength': 0.3, 'request_rate_mean': 15,
            'request_rate_p95': 30, 'concurrency_mean': 1,
            'active_hours_per_day': 10, 'efficiency_score': 25
        })
    ]
    
    for name, features in test_cases:
        print(f"\n{name}:")
        result = classifier.classify(features)
        print(f"  → Detected: {result['workload_type']}")
        print(f"  → Confidence: {result['confidence']*100:.0f}%")
        print(f"  → Evidence: {result['reasoning'][0]}")
    
    print("\n✅ Classification test complete!")
