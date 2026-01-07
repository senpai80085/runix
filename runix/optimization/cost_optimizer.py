"""
Cost Optimizer
Generates cost-optimal architecture recommendations with explainability
"""

import uuid
from typing import Dict, List
import sys
import os

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from common.config import (
    CPU_COST_PER_VCPU_SECOND,
    MEMORY_COST_PER_GB_SECOND,
    REQUEST_COST,
    FREE_TIER_CPU_SECONDS,
    FREE_TIER_MEMORY_GB_SECONDS,
    FREE_TIER_REQUESTS,
    RISK_LEVELS
)


class CostOptimizer:
    """
    Generates cost-optimal architecture recommendations
    Uses official Google Cloud pricing formulas
    """
    
    def __init__(self):
        self.cpu_cost_per_second = CPU_COST_PER_VCPU_SECOND
        self.memory_cost_per_gb_second = MEMORY_COST_PER_GB_SECOND
        self.request_cost = REQUEST_COST
        
    def generate_recommendation(
        self,
        features: Dict,
        classification: Dict,
        current_config: Dict = None
    ) -> Dict:
        """
        Generate cost optimization recommendation
        
        Args:
            features: Engineered features
            classification: Workload classification result
            current_config: Current architecture configuration
            
        Returns:
            Recommendation with cost impact and implementation steps
        """
        if current_config is None:
            # Default current configuration (typical Cloud Run setup)
            current_config = {
                'platform': 'Cloud Run',
                'cpu': 1.0,  # vCPU
                'memory_gb': 0.5,  # GB
                'min_instances': 1,
                'max_instances': 10,
                'timeout_seconds': 300
            }
        
        workload_type = classification['workload_type']
        confidence = classification['confidence']
        
        # Calculate current costs
        current_cost = self._calculate_monthly_cost(
            features, current_config
        )
        
        # Generate optimal configuration based on workload type
        if workload_type == "Bursty Stateless Service":
            optimized_config, explanation = self._optimize_bursty_service(
                features, current_config
            )
        elif workload_type == "Always-On API":
            optimized_config, explanation = self._optimize_always_on_api(
                features, current_config
            )
        elif workload_type == "Event-Driven / Spiky":
            optimized_config, explanation = self._optimize_event_driven(
                features, current_config
            )
        elif workload_type == "Background Worker":
            optimized_config, explanation = self._optimize_background_worker(
                features, current_config
            )
        elif workload_type == "Over-Provisioned Container":
            optimized_config, explanation = self._optimize_over_provisioned(
                features, current_config
            )
        else:
            optimized_config = current_config
            explanation = ["No optimization recommendation available"]
        
        # Calculate optimized costs
        optimized_cost = self._calculate_monthly_cost(
            features, optimized_config
        )
        
        # Determine risk level
        risk_level = self._assess_risk(
            workload_type, current_config, optimized_config, confidence
        )
        
        # Generate implementation steps
        implementation_steps = self._generate_implementation_steps(
            current_config, optimized_config
        )
        
        # Build recommendation
        return {
            'recommendation_id': str(uuid.uuid4()),
            'current_architecture': current_config,
            'recommended_architecture': optimized_config,
            'cost_impact': {
                'current_monthly_usd': round(current_cost, 2),
                'optimized_monthly_usd': round(optimized_cost, 2),
                'savings_usd': round(current_cost - optimized_cost, 2),
                'savings_percentage': round(
                    ((current_cost - optimized_cost) / current_cost * 100) if current_cost > 0 else 0,
                    1
                ),
                'within_free_tier': optimized_cost < 0.5
            },
            'risk_level': risk_level,
            'explanation': explanation,
            'implementation_steps': implementation_steps,
            'approval_required': True
        }
    
    def _calculate_monthly_cost(self, features: Dict, config: Dict) -> float:
        """
        Calculate monthly cost using official GCP pricing
        
        Cost formula (Cloud Run):
        - vCPU: $0.000024 per vCPU-second
        - Memory: $0.0000025 per GB-second  
        - Requests: $0.0000004 per request
        
        Free tier:
        - 180,000 vCPU-seconds
        - 360,000 GB-seconds
        - 2M requests
        """
        # Estimate monthly usage
        seconds_per_month = 30 * 24 * 3600  # 2,592,000 seconds
        
        # Active time (accounting for idle)
        idle_ratio = features.get('idle_ratio', 0.5)
        active_ratio = 1 - idle_ratio
        
        # CPU cost
        cpu = config.get('cpu', 1.0)
        min_instances = config.get('min_instances', 0)
        
        if min_instances > 0:
            # Always-on: charged for all time
            cpu_seconds = cpu * seconds_per_month * min_instances
        else:
            # Scale-to-zero: charged only for active time
            cpu_seconds = cpu * seconds_per_month * active_ratio
        
        cpu_seconds_billable = max(0, cpu_seconds - FREE_TIER_CPU_SECONDS)
        cpu_cost = cpu_seconds_billable * self.cpu_cost_per_second
        
        # Memory cost
        memory_gb = config.get('memory_gb', 0.5)
        
        if min_instances > 0:
            memory_gb_seconds = memory_gb * seconds_per_month * min_instances
        else:
            memory_gb_seconds = memory_gb * seconds_per_month * active_ratio
        
        memory_gb_seconds_billable = max(0, memory_gb_seconds - FREE_TIER_MEMORY_GB_SECONDS)
        memory_cost = memory_gb_seconds_billable * self.memory_cost_per_gb_second
        
        # Request cost
        total_requests = features.get('total_requests', 0)
        # Extrapolate to monthly
        window_days = 7  # Assuming 7-day analysis window
        monthly_requests = (total_requests / window_days) * 30
        
        requests_billable = max(0, monthly_requests - FREE_TIER_REQUESTS)
        request_cost = requests_billable * self.request_cost
        
        total_cost = cpu_cost + memory_cost + request_cost
        return total_cost
    
    def _optimize_bursty_service(self, features: Dict, current: Dict) -> tuple:
        """Optimize bursty stateless service"""
        optimized = current.copy()
        explanation = []
        
        # Scale to zero
        if current.get('min_instances', 1) > 0:
            optimized['min_instances'] = 0
            explanation.append(
                f"Set min-instances=0 to eliminate idle cost "
                f"({features.get('idle_ratio', 0)*100:.0f}% idle time)"
            )
        
        # Right-size CPU
        cpu_p95 = features.get('cpu_p95', 50)
        if cpu_p95 < 50:
            optimized['cpu'] = 0.5
            explanation.append(
                f"Reduce CPU to 0.5 vCPU (p95 utilization: {cpu_p95:.0f}%)"
            )
        
        # Right-size memory
        memory_p95 = features.get('memory_p95', 50)
        if memory_p95 < 40:
            optimized['memory_gb'] = 0.25
            explanation.append(
                f"Reduce memory to 256MB (p95 utilization: {memory_p95:.0f}%)"
            )
        
        explanation.append("Scale-to-zero prevents idle compute costs")
        explanation.append(f"Expected cold start: ~200-500ms")
        
        return optimized, explanation
    
    def _optimize_always_on_api(self, features: Dict, current: Dict) -> tuple:
        """Optimize always-on API"""
        optimized = current.copy()
        explanation = []
        
        # Keep min-instances for latency
        if current.get('min_instances', 0) == 0:
            optimized['min_instances'] = 1
            explanation.append("Maintain min-instance=1 for low latency")
        
        # Right-size based on actual usage
        cpu_p95 = features.get('cpu_p95', 50)
        target_cpu = min(2.0, max(0.5, cpu_p95 / 60))  # Target 60% at p95
        
        if abs(current.get('cpu', 1) - target_cpu) > 0.2:
            optimized['cpu'] = target_cpu
            explanation.append(
                f"Adjust CPU to {target_cpu} vCPU (current p95: {cpu_p95:.0f}%)"
            )
        
        explanation.append("Always-on architecture is optimal for this workload")
        explanation.append(f"Idle time minimal: {features.get('idle_ratio', 0)*100:.0f}%")
        
        return optimized, explanation
    
    def _optimize_event_driven(self, features: Dict, current: Dict) -> tuple:
        """Optimize event-driven/spiky workload"""
        optimized = current.copy()
        explanation = []
        
        # Aggressive scale-to-zero
        optimized['min_instances'] = 0
        optimized['cpu'] = 0.5
        optimized['memory_gb'] = 0.25
        
        explanation.append(
            f"Extreme burstiness ({features.get('burstiness_score', 0):.1f}x) "
            "requires scale-to-zero"
        )
        explanation.append(
            f"Active only {features.get('active_hours_per_day', 0):.0f} hours/day"
        )
        explanation.append("Cold starts acceptable for event-driven pattern")
        explanation.append("Consider Cloud Functions for simpler deployments")
        
        return optimized, explanation
    
    def _optimize_background_worker(self, features: Dict, current: Dict) -> tuple:
        """Optimize background worker"""
        optimized = current.copy()
        explanation = []
        
        # Single instance, right-sized
        optimized['min_instances'] = 1
        optimized['max_instances'] = 1
        optimized['cpu'] = 0.5
        
        explanation.append("Background workers benefit from stable single instance")
        explanation.append(f"Low traffic: {features.get('request_rate_mean', 0):.0f} req/min")
        explanation.append("Reduced CPU allocation: 0.5 vCPU sufficient")
        
        return optimized, explanation
    
    def _optimize_over_provisioned(self, features: Dict, current: Dict) -> tuple:
        """Optimize over-provisioned container"""
        optimized = current.copy()
        explanation = []
        
        # Aggressive right-sizing
        cpu_p95 = features.get('cpu_p95', 50)
        optimized['cpu'] = max(0.5, cpu_p95 / 50)  # Target 50% at p95
        
        memory_p95 = features.get('memory_p95', 50)
        optimized['memory_gb'] = max(0.25, memory_p95 / 50 * 0.5)
        
        # Scale to zero if high idle
        if features.get('idle_ratio', 0) > 0.5:
            optimized['min_instances'] = 0
            explanation.append("Scale-to-zero to eliminate idle waste")
        
        explanation.append(
            f"Severe over-provisioning detected (CPU p95: {cpu_p95:.0f}%)"
        )
        explanation.append(
            f"Reduce CPU from {current.get('cpu', 1)} to {optimized['cpu']} vCPU"
        )
        explanation.append(
            f"Est. wasted cost: {features.get('over_provision_penalty', 0):.0f}%"
        )
        
        return optimized, explanation
    
    def _assess_risk(
        self,
        workload_type: str,
        current: Dict,
        optimized: Dict,
        confidence: float
    ) -> str:
        """Assess risk level of recommendation"""
        if confidence < 0.6:
            return "High"
        
        # Check for major changes
        cpu_change = abs(optimized.get('cpu', 1) - current.get('cpu', 1))
        min_change = abs(optimized.get('min_instances', 0) - current.get('min_instances', 0))
        
        if min_change > 0 or cpu_change > 0.5:
            return "Medium"
        
        return "Low"
    
    def _generate_implementation_steps(self, current: Dict, optimized: Dict) -> List[str]:
        """Generate gcloud commands for implementation"""
        steps = []
        
        changes = []
        if optimized.get('cpu') != current.get('cpu'):
            changes.append(f"--cpu={optimized['cpu']}")
        if optimized.get('memory_gb') != current.get('memory_gb'):
            memory_mb = int(optimized['memory_gb'] * 1024)
            changes.append(f"--memory={memory_mb}Mi")
        if optimized.get('min_instances') != current.get('min_instances'):
            changes.append(f"--min-instances={optimized['min_instances']}")
        if optimized.get('max_instances') != current.get('max_instances'):
            changes.append(f"--max-instances={optimized['max_instances']}")
        
        if changes:
            cmd = f"gcloud run services update SERVICE_NAME {' '.join(changes)} --region=REGION"
            steps.append(cmd)
            steps.append("Replace SERVICE_NAME and REGION with your values")
            steps.append("Monitor performance for 24-48 hours")
            steps.append("Rollback if issues: gcloud run services update SERVICE_NAME --min-instances=1")
        
        return steps


# Test function
if __name__ == "__main__":
    print("Testing Cost Optimizer...")
    print("=" * 60)
    
    # Test with bursty service
    features = {
        'cpu_mean': 15, 'cpu_p95': 45, 'cpu_p99': 65,
        'memory_mean': 25, 'memory_p95': 40,
        'idle_ratio': 0.5, 'burstiness_score': 4.2,
        'total_requests': 50000, 'efficiency_score': 50
    }
    
    classification = {
        'workload_type': 'Bursty Stateless Service',
        'confidence': 0.87,
        'reasoning': ['Test classification']
    }
    
    current_config = {
        'platform': 'Cloud Run',
        'cpu': 1.0,
        'memory_gb': 0.5,
        'min_instances': 1,
        'max_instances': 10
    }
    
    optimizer = CostOptimizer()
    recommendation = optimizer.generate_recommendation(
        features, classification, current_config
    )
    
    print("\nRecommendation:")
    print(f"Workload: {classification['workload_type']}")
    print(f"Risk: {recommendation['risk_level']}")
    print(f"\nCurrent: {recommendation['current_architecture']}")
    print(f"Optimized: {recommendation['recommended_architecture']}")
    print(f"\nCost Impact:")
    print(f"  Current: ${recommendation['cost_impact']['current_monthly_usd']:.2f}/month")
    print(f"  Optimized: ${recommendation['cost_impact']['optimized_monthly_usd']:.2f}/month")
    print(f"  Savings: ${recommendation['cost_impact']['savings_usd']:.2f} ({recommendation['cost_impact']['savings_percentage']:.0f}%)")
    print(f"  Free Tier: {recommendation['cost_impact']['within_free_tier']}")
    print(f"\nExplanation:")
    for exp in recommendation['explanation']:
        print(f"  - {exp}")
    print(f"\nImplementation:")
    for step in recommendation['implementation_steps']:
        print(f"  {step}")
    
    print("\n✅ Cost optimization test complete!")
