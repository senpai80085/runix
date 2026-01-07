"""
Gemini AI Explainer - Enhanced Edition
Generates detailed, actionable insights using Google Gemini AI
"""

import google.generativeai as genai
import os
from typing import Dict
from datetime import datetime


class GeminiExplainer:
    """Uses Gemini AI to generate detailed, human-friendly explanations"""
    
    def __init__(self, api_key: str = None):
        self.api_key = api_key or os.getenv('GEMINI_API_KEY')
        self.model = None
        
        if self.api_key:
            genai.configure(api_key=self.api_key)
            self.model = genai.GenerativeModel('gemini-1.5-flash')
    
    def is_available(self) -> bool:
        """Check if Gemini is configured"""
        return self.model is not None
        
    @property
    def enabled(self) -> bool:
        """Alias for is_available for easier property access"""
        return self.is_available()
    
    def generate_explanation(
        self,
        classification: Dict,
        recommendation: Dict,
        features: Dict
    ) -> str:
        """
        Generate a detailed natural language explanation of the analysis
        """
        if not self.is_available():
            return self._fallback_explanation(classification, recommendation, features)
        
        # Extract all available metrics for rich context
        cpu_mean = features.get('cpu_mean', 0)
        cpu_p95 = features.get('cpu_p95', 0)
        cpu_p99 = features.get('cpu_p99', 0)
        memory_mean = features.get('memory_mean', 0)
        memory_p95 = features.get('memory_p95', 0)
        idle_ratio = features.get('idle_ratio', 0) * 100
        burstiness = features.get('burstiness_score', 1)
        diurnal_strength = features.get('diurnal_pattern_strength', 0)
        efficiency = features.get('efficiency_score', 0)
        active_hours = features.get('active_hours_per_day', 0)
        request_mean = features.get('request_rate_mean', 0)
        request_p95 = features.get('request_rate_p95', 0)
        
        cost_impact = recommendation.get('cost_impact', {})
        current_cost = cost_impact.get('current_monthly_usd', 0)
        optimized_cost = cost_impact.get('optimized_monthly_usd', 0)
        savings = cost_impact.get('savings_usd', 0)
        savings_pct = cost_impact.get('savings_percentage', 0)
        
        current_arch = recommendation.get('current_architecture', {})
        recommended_arch = recommendation.get('recommended_architecture', {})
        
        # Build comprehensive prompt
        prompt = f"""You are Runix, an expert cloud cost optimization AI assistant. 
Analyze this Google Cloud Run workload and provide a detailed, actionable insight.

═══════════════════════════════════════════════════════════════
WORKLOAD CLASSIFICATION
═══════════════════════════════════════════════════════════════
• Detected Type: {classification.get('workload_type', 'Unknown')}
• Confidence Score: {classification.get('confidence', 0)*100:.0f}%
• Key Evidence: {'; '.join(classification.get('reasoning', ['No data'])[:3])}

═══════════════════════════════════════════════════════════════
DETAILED METRICS (7-Day Analysis Period)
═══════════════════════════════════════════════════════════════

CPU UTILIZATION:
  • Average: {cpu_mean:.1f}%
  • 95th Percentile (peak load): {cpu_p95:.1f}%
  • 99th Percentile (extreme peaks): {cpu_p99:.1f}%

MEMORY UTILIZATION:
  • Average: {memory_mean:.1f}%
  • 95th Percentile: {memory_p95:.1f}%

TRAFFIC PATTERNS:
  • Average Requests: {request_mean:.0f}/min
  • Peak Requests (p95): {request_p95:.0f}/min
  • Burstiness Score: {burstiness:.2f}x (variance between peak and average)
  • Active Hours/Day: {active_hours:.1f} hours

EFFICIENCY METRICS:
  • Idle Time: {idle_ratio:.0f}% of total time (CPU < 5%)
  • Diurnal Pattern Strength: {diurnal_strength:.2f} (0=random, 1=strong daily cycle)
  • Overall Efficiency Score: {efficiency:.0f}/100

═══════════════════════════════════════════════════════════════
COST ANALYSIS
═══════════════════════════════════════════════════════════════
CURRENT CONFIGURATION:
  • vCPU: {current_arch.get('cpu', 'N/A')}
  • Memory: {current_arch.get('memory', 'N/A')}
  • Min Instances: {current_arch.get('min_instances', 'N/A')}
  • Monthly Cost: ${current_cost:.2f}

RECOMMENDED CONFIGURATION:
  • vCPU: {recommended_arch.get('cpu', 'N/A')}
  • Memory: {recommended_arch.get('memory', 'N/A')}
  • Min Instances: {recommended_arch.get('min_instances', 'N/A')}
  • Monthly Cost: ${optimized_cost:.2f}

SAVINGS POTENTIAL:
  • Monthly Savings: ${savings:.2f}
  • Percentage Reduction: {savings_pct:.0f}%
  • Annual Savings: ${savings * 12:.2f}

═══════════════════════════════════════════════════════════════
YOUR TASK
═══════════════════════════════════════════════════════════════
Write a detailed insight (150-200 words) that:

1. DIAGNOSE: Explain what the workload is doing and why it's classified this way
2. IDENTIFY WASTE: Point out specific inefficiencies with actual numbers
3. RECOMMEND: Explain the optimization strategy in plain terms
4. QUANTIFY: State the exact savings and payback
5. RISK: Mention any trade-offs (like cold starts) honestly

Use specific numbers from the data. Be direct and actionable.
Write in first person as "I analyzed..." format.
Don't use bullet points - write flowing paragraphs."""

        try:
            response = self.model.generate_content(prompt)
            return response.text.strip()
        except Exception as e:
            print(f"Gemini API error: {e}")
            return self._fallback_explanation(classification, recommendation, features)
    
    def _fallback_explanation(self, classification: Dict, recommendation: Dict, features: Dict) -> str:
        """Generate detailed explanation without AI API"""
        workload_type = classification.get('workload_type', 'service')
        cost_impact = recommendation.get('cost_impact', {})
        savings = cost_impact.get('savings_usd', 0)
        savings_pct = cost_impact.get('savings_percentage', 0)
        current_cost = cost_impact.get('current_monthly_usd', 0)
        idle_ratio = features.get('idle_ratio', 0) * 100
        cpu_mean = features.get('cpu_mean', 0)
        cpu_p95 = features.get('cpu_p95', 0)
        burstiness = features.get('burstiness_score', 1)
        
        explanations = {
            "Bursty Stateless Service": f"""I analyzed 7 days of metrics and identified this as a Bursty Stateless Service. 
The data shows your workload is idle {idle_ratio:.0f}% of the time, with CPU averaging just {cpu_mean:.1f}% but spiking to {cpu_p95:.1f}% during bursts. 
The traffic burstiness score of {burstiness:.1f}x confirms significant variance between peak and average load. 
This pattern is perfect for scale-to-zero architecture. By setting min-instances=0, you eliminate costs during the {idle_ratio:.0f}% idle periods. 
This would save ${savings:.2f}/month (${savings*12:.2f}/year) - a {savings_pct:.0f}% reduction from ${current_cost:.2f}. 
The trade-off is cold starts (200-500ms latency for first request after idle), but for bursty workloads this is usually acceptable.""",
            
            "Always-On API": f"""I analyzed 7 days of metrics and identified this as an Always-On API with consistent traffic. 
Your workload maintains steady utilization with CPU averaging {cpu_mean:.1f}% (p95: {cpu_p95:.1f}%) and only {idle_ratio:.0f}% idle time. 
This is already an efficient pattern, but the resources are slightly over-provisioned. 
By right-sizing the CPU and memory allocation to match your p95 utilization, you can save ${savings:.2f}/month ({savings_pct:.0f}% reduction). 
I recommend keeping min-instances=1 to avoid cold starts since this API needs consistent availability. 
The optimization is low-risk and maintains your current performance SLAs.""",
            
            "Over-Provisioned Container": f"""I analyzed 7 days of metrics and found severe over-provisioning. 
Your container averages only {cpu_mean:.1f}% CPU utilization (p95: {cpu_p95:.1f}%) and sits idle {idle_ratio:.0f}% of the time. 
You're paying for resources that are barely being used - this is the #1 cloud cost mistake. 
By right-sizing to match actual usage and enabling scale-to-zero, you would save ${savings:.2f}/month (${savings*12:.2f}/year) - a massive {savings_pct:.0f}% reduction. 
The risk is medium due to potential cold starts, but with {idle_ratio:.0f}% idle time, the savings far outweigh the occasional latency spike. 
I strongly recommend implementing these changes immediately."""
        }
        
        return explanations.get(workload_type, 
            f"Based on 7 days of analysis, optimizing this workload by right-sizing resources and adjusting scaling parameters could save ${savings:.2f}/month ({savings_pct:.0f}% of current ${current_cost:.2f} spend).")


# Test
if __name__ == "__main__":
    explainer = GeminiExplainer()
    
    if explainer.is_available():
        print("✅ Gemini AI is configured!")
    else:
        print("⚠️  No GEMINI_API_KEY found - using enhanced fallback explanations")
