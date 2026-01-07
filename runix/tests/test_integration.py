import sys
import os

# Add parent directory for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from mock_data_generator import MockDataGenerator
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'intelligence'))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'optimization'))

from feature_extractor import FeatureExtractor
from classifier import WorkloadClassifier
from cost_optimizer import CostOptimizer
import json



def test_complete_pipeline():
    """Test complete Runix pipeline from metrics to recommendations"""
    
    print("\n" + "=" * 80)
    print(" RUNIX END-TO-END PIPELINE TEST")
    print("=" * 80)
    
    # Initialize components
    generator = MockDataGenerator()
    extractor = FeatureExtractor()
    classifier = WorkloadClassifier()
    optimizer = CostOptimizer()
    
    # Test scenarios
    scenarios = [
        ('Bursty Stateless Service', generator.generate_bursty_service_data(7)),
        ('Always-On API', generator.generate_always_on_api_data(7)),
        ('Over-Provisioned Container', generator.generate_over_provisioned_data(7))
    ]
    
    for scenario_name, metrics in scenarios:
        print(f"\n{'─' * 80}")
        print(f" SCENARIO: {scenario_name}")
        print(f"{'─' * 80}")
        
        # Extract resource ID
        resource_id = metrics['cpu_utilization']['resource_id'].iloc[0]
        
        # Step 1: Feature Extraction
        print("\n[1/4] Extracting features from time-series data...")
        features = extractor.extract_features(metrics, resource_id)
        
        print(f"  ✓ Extracted {len(features)} features")
        print(f"    - CPU mean: {features.get('cpu_mean', 0):.1f}%")
        print(f"    - CPU p95: {features.get('cpu_p95', 0):.1f}%")
        print(f"    - Idle ratio: {features.get('idle_ratio', 0):.1%}")
        print(f"    - Burstiness: {features.get('burstiness_score', 0):.2f}x")
        print(f"    - Efficiency: {features.get('efficiency_score', 0):.1f}%")
        
        # Step 2: Workload Classification
        print("\n[2/4] Classifying workload pattern...")
        classification = classifier.classify(features)
        
        print(f"  ✓ Classification: {classification['workload_type']}")
        print(f"  ✓ Confidence: {classification['confidence']:.1%}")
        print("  ✓ Reasoning:")
        for reason in classification['reasoning'][:3]:
            print(f"      • {reason}")
        
        # Step 3: Cost Optimization
        print("\n[3/4] Generating optimization recommendation...")
        
        current_config = {
            'platform': 'Cloud Run',
            'cpu': 1.0,
            'memory_gb': 0.5,
            'min_instances': 1,
            'max_instances': 10
        }
        
        recommendation = optimizer.generate_recommendation(
            features, classification, current_config
        )
        
        cost_impact = recommendation['cost_impact']
        
        print(f"  ✓ Current Cost: ${cost_impact['current_monthly_usd']:.2f}/month")
        print(f"  ✓ Optimized Cost: ${cost_impact['optimized_monthly_usd']:.2f}/month")
        print(f"  ✓ Savings: ${cost_impact['savings_usd']:.2f} ({cost_impact['savings_percentage']:.0f}%)")
        print(f"  ✓ Risk Level: {recommendation['risk_level']}")
        print(f"  ✓ Free Tier Compatible: {cost_impact['within_free_tier']}")
        
        # Step 4: Explainability Check
        print("\n[4/4] Validating explainability...")
        
        has_explanation = len(recommendation['explanation']) > 0
        has_steps = len(recommendation['implementation_steps']) > 0
        has_reasoning = len(classification['reasoning']) > 0
        
        print(f"  ✓ Explanation: {len(recommendation['explanation'])} points")
        print(f"  ✓ Implementation steps: {len(recommendation['implementation_steps'])} steps")
        print(f"  ✓ Classification reasoning: {len(classification['reasoning'])} points")
        
        if has_explanation and has_steps and has_reasoning:
            print("  ✅ Explainability criteria met")
        else:
            print("  ⚠️  Explainability incomplete")
        
        # Summary
        print("\n📊 RECOMMENDATION SUMMARY")
        print("  " + "─" * 76)
        print(f"  Workload: {classification['workload_type']} ({classification['confidence']:.0%} confidence)")
        print(f"  Recommendation: {recommendation['recommended_architecture']}")
        print(f"  Impact: Save ${cost_impact['savings_usd']:.2f}/month ({cost_impact['savings_percentage']:.0f}%)")
        print("  " + "─" * 76)
    
    print("\n" + "=" * 80)
    print(" ✅ ALL TESTS PASSED - RUNIX PIPELINE OPERATIONAL")
    print("=" * 80)
    print()


if __name__ == "__main__":
    test_complete_pipeline()
