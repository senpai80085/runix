"""
Runix Quick Demo
Shows the platform working end-to-end
"""
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from runix.tests.mock_data_generator import MockDataGenerator
from runix.intelligence.feature_extractor import FeatureExtractor
from runix.intelligence.classifier import WorkloadClassifier
from runix.optimization.cost_optimizer import CostOptimizer

print("=" * 70)
print("  RUNIX WORKLOAD INTELLIGENCE PLATFORM - LIVE DEMO")
print("=" * 70)

# Initialize
generator = MockDataGenerator()
extractor = FeatureExtractor()
classifier = WorkloadClassifier()
optimizer = CostOptimizer()

# Demo: Analyze a bursty service
print("\n[STEP 1] Generating 7 days of mock Cloud Run metrics...")
metrics = generator.generate_bursty_service_data(7)
print(f"  Generated {len(metrics['cpu_utilization'])} data points per metric")

print("\n[STEP 2] Extracting analytical features...")
features = extractor.extract_features(metrics, 'mock-bursty-service')
print(f"  CPU Mean: {features.get('cpu_mean', 0):.1f}%")
print(f"  CPU P95: {features.get('cpu_p95', 0):.1f}%")
print(f"  Idle Ratio: {features.get('idle_ratio', 0)*100:.0f}%")
print(f"  Burstiness Score: {features.get('burstiness_score', 0):.2f}x")
print(f"  Efficiency: {features.get('efficiency_score', 0):.0f}%")

print("\n[STEP 3] ML Classification...")
classification = classifier.classify(features)
print(f"  Workload Type: {classification['workload_type']}")
print(f"  Confidence: {classification['confidence']*100:.0f}%")
print("  Evidence:")
for reason in classification['reasoning'][:3]:
    print(f"    - {reason}")

print("\n[STEP 4] Cost Optimization Recommendation...")
recommendation = optimizer.generate_recommendation(features, classification)
cost = recommendation['cost_impact']
print(f"  Current Cost: ${cost['current_monthly_usd']:.2f}/month")
print(f"  Optimized Cost: ${cost['optimized_monthly_usd']:.2f}/month")
print(f"  SAVINGS: ${cost['savings_usd']:.2f} ({cost['savings_percentage']:.0f}%)")
print(f"  Risk Level: {recommendation['risk_level']}")
print(f"  Free Tier: {'Yes' if cost['within_free_tier'] else 'No'}")

print("\n[STEP 5] Implementation Steps:")
for step in recommendation['implementation_steps'][:2]:
    print(f"  {step}")

print("\n" + "=" * 70)
print("  RUNIX DEMO COMPLETE")
print("=" * 70)
print("\nRunix successfully analyzed workload and generated cost-saving recommendation!")
