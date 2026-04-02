"""Decision Agent: Uses Ollama llama3 for intelligent procurement decisions."""

import json
import re
import time
from typing import Dict, List, Optional

import requests

from ..logging_config import log_agent_output, log_error, log_performance_metric, logger
from ..models import FewShotMemory


class DecisionAgent:
    """Agent responsible for making procurement decisions using LLM reasoning."""

    MODEL_NAME = 'llama3'
    TIMEOUT_SECONDS = 45
    TEMPERATURE = 0.3

    def __init__(self):
        """Initialize Decision Agent."""
        import os
        
        # Get Ollama URL from environment or use default
        self.ollama_url = os.getenv(
            'AI_PROCUREMENT_OLLAMA_URL',
            'http://ollama:11434/api/generate'  # Default for devcontainer
        )

    def get_few_shot_examples(
        self, part_category_id: Optional[int], limit: int = 3
    ) -> List[Dict]:
        """
        Retrieve few-shot examples from memory store.

        Args:
            part_category_id: ID of the part category (optional)
            limit: Maximum number of examples to retrieve

        Returns:
            List of few-shot examples
        """
        try:
            query = FewShotMemory.objects.filter(
                outcome_quality__in=['excellent', 'good']
            )

            if part_category_id:
                query = query.filter(part_category_id=part_category_id)

            # Order by usage count (popular examples) and recency
            examples = query.order_by('-usage_count', '-created_at')[:limit]

            return [
                {
                    'decision_context': ex.decision_context,
                    'decision_made': ex.decision_made,
                    'reasoning': ex.reasoning,
                    'outcome_quality': ex.outcome_quality,
                }
                for ex in examples
            ]
        except Exception as e:
            print(f'Error retrieving few-shot examples: {e}')
            return []

    def format_few_shot_example(self, example: Dict) -> str:
        """
        Format a few-shot example for inclusion in prompt.

        Args:
            example: Few-shot example dictionary

        Returns:
            Formatted example string
        """
        context = example['decision_context']
        return f"""
Example Decision:
- Part: {context.get('part_name', 'Unknown')}
- Current Stock: {context.get('current_stock', 0)} units
- Forecasted Demand: {context.get('forecasted_demand', 0)} units
- Decision: {example['decision_made']}
- Reasoning: {example['reasoning']}
- Outcome: {example['outcome_quality']}
"""

    def build_llm_prompt(
        self, decision_context: Dict, few_shot_examples: List[Dict]
    ) -> str:
        """
        Build comprehensive LLM prompt with context and examples.

        Args:
            decision_context: Current decision context
            few_shot_examples: List of few-shot examples

        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an AI procurement agent for a manufacturing company.
Analyze the following data and decide if we need to order more stock.

Part Information:
- Part Name: {decision_context['part_name']}
- Current Stock: {decision_context['current_stock']} units
- Minimum Required Stock: {decision_context['minimum_stock']} units

Demand Forecast (next 30 days):
- Predicted Demand: {decision_context['forecasted_demand']} units
- Confidence Interval: [{decision_context['confidence_interval'][0]:.2f}, {decision_context['confidence_interval'][1]:.2f}]
- Trend: {decision_context.get('trend_direction', 'unknown')}

Top Suppliers:
"""

        # Add top 3 suppliers
        for supplier in decision_context.get('top_suppliers', [])[:3]:
            prompt += f"""
{supplier['ranking_position']}. {supplier['supplier_name']}
   - Overall Score: {supplier['overall_score']:.2f}
   - Unit Price: ${supplier['unit_price']:.2f}
   - Lead Time: {supplier['estimated_delivery_days']} days
   - Reliability: {supplier['reliability_score']:.2f}
   - MOQ Met: {supplier['moq_met']}
   - Reason: {supplier['recommendation_reason']}
"""

        # Add few-shot examples if available
        if few_shot_examples:
            prompt += '\n\nPrevious Similar Decisions:\n'
            for example in few_shot_examples:
                prompt += self.format_few_shot_example(example)

        # Add decision instructions
        prompt += """

Based on this analysis, decide:
1. Should we order more stock? (ORDER, DO_NOT_ORDER, or ESCALATE)
2. If ordering, how much should we order?
3. Which supplier should we use?

Consider:
- Current stock vs minimum required
- Forecasted demand and confidence
- Supplier scores and lead times
- Risk of stockout vs cost of excess inventory

Return ONLY a valid JSON object with these keys:
{
  "decision": "ORDER" | "DO_NOT_ORDER" | "ESCALATE",
  "quantity": <integer>,
  "supplier_id": <integer or null>,
  "reasoning": "<1-3 sentences explaining your decision>",
  "confidence_level": "high" | "medium" | "low",
  "risk_factors": [<list of potential risks>],
  "alternative_actions": [<list of alternative approaches>]
}
"""

        return prompt

    def call_ollama(self, prompt: str) -> Dict:
        """
        Call Ollama API with the prompt.

        Args:
            prompt: Formatted prompt string

        Returns:
            Parsed JSON response from LLM

        Raises:
            Exception if API call fails
        """
        start_time = time.time()

        try:
            response = requests.post(
                self.ollama_url,
                json={
                    'model': self.MODEL_NAME,
                    'prompt': prompt,
                    'stream': False,
                    'format': 'json',
                    'options': {'temperature': self.TEMPERATURE, 'top_p': 0.9},
                },
                timeout=self.TIMEOUT_SECONDS,
            )

            response.raise_for_status()

            end_time = time.time()
            response_time_ms = int((end_time - start_time) * 1000)

            # Extract response
            result = response.json()
            llm_output = result.get('response', '{}')

            # Parse JSON
            parsed_output = json.loads(llm_output)
            parsed_output['_response_time_ms'] = response_time_ms

            return parsed_output

        except requests.exceptions.Timeout:
            raise Exception('Ollama API timeout')
        except requests.exceptions.ConnectionError:
            raise Exception('Cannot connect to Ollama API')
        except json.JSONDecodeError as e:
            # Try to extract JSON using regex as fallback
            raise Exception(f'Invalid JSON response from LLM: {e}')
        except Exception as e:
            raise Exception(f'Ollama API error: {e}')

    def validate_llm_output(self, llm_output: Dict) -> bool:
        """
        Validate LLM output structure.

        Args:
            llm_output: Parsed LLM output

        Returns:
            True if valid, raises Exception otherwise
        """
        required_fields = ['decision', 'quantity', 'reasoning']
        for field in required_fields:
            if field not in llm_output:
                raise Exception(f'Missing required field: {field}')

        # Validate decision value
        valid_decisions = ['ORDER', 'DO_NOT_ORDER', 'ESCALATE']
        if llm_output['decision'] not in valid_decisions:
            raise Exception(f"Invalid decision: {llm_output['decision']}")

        # Validate quantity
        if not isinstance(llm_output['quantity'], (int, float)):
            raise Exception('Quantity must be a number')

        if llm_output['quantity'] < 0:
            raise Exception('Quantity cannot be negative')

        return True

    def make_rule_based_decision(self, decision_context: Dict) -> Dict:
        """
        Fallback rule-based decision logic when LLM fails.

        Args:
            decision_context: Current decision context

        Returns:
            Procurement decision dictionary
        """
        current_stock = decision_context['current_stock']
        minimum_stock = decision_context['minimum_stock']
        forecasted_demand = decision_context['forecasted_demand']

        # Calculate projected stock
        projected_stock = current_stock - forecasted_demand

        # Safety buffer (20% above minimum)
        safety_buffer = minimum_stock * 1.2

        if projected_stock < safety_buffer:
            # Need to order
            order_quantity = int(forecasted_demand + safety_buffer - current_stock)

            # Select top-ranked supplier
            top_suppliers = decision_context.get('top_suppliers', [])
            if top_suppliers:
                top_supplier = top_suppliers[0]
                supplier_id = top_supplier['supplier_id']
            else:
                supplier_id = None

            return {
                'decision': 'ORDER',
                'recommended_quantity': order_quantity,
                'recommended_supplier_id': supplier_id,
                'reasoning': (
                    f'Rule-based decision: Projected stock ({projected_stock:.0f}) '
                    f'below safety buffer ({safety_buffer:.0f}). '
                    f'Ordering to maintain minimum stock level.'
                ),
                'confidence_level': 'medium',
                'risk_factors': ['LLM unavailable, using rule-based fallback'],
                'alternative_actions': [],
            }
        else:
            return {
                'decision': 'DO_NOT_ORDER',
                'recommended_quantity': 0,
                'recommended_supplier_id': None,
                'reasoning': (
                    f'Rule-based decision: Projected stock ({projected_stock:.0f}) '
                    f'sufficient for forecasted demand. Current stock above safety buffer.'
                ),
                'confidence_level': 'medium',
                'risk_factors': ['LLM unavailable, using rule-based fallback'],
                'alternative_actions': [],
            }

    def make_decision(self, decision_context: Dict) -> Dict:
        """
        Make procurement decision using LLM reasoning.

        Args:
            decision_context: Current decision context

        Returns:
            Procurement decision dictionary
        """
        try:
            # Get few-shot examples
            part_category_id = decision_context.get('part_category_id')
            few_shot_examples = self.get_few_shot_examples(part_category_id, limit=3)

            # Build prompt
            prompt = self.build_llm_prompt(decision_context, few_shot_examples)

            # Call Ollama
            llm_output = self.call_ollama(prompt)

            # Validate output
            self.validate_llm_output(llm_output)

            # Extract response time
            response_time_ms = llm_output.pop('_response_time_ms', 0)

            # Format decision
            decision = {
                'decision': llm_output['decision'],
                'recommended_quantity': int(llm_output['quantity']),
                'recommended_supplier_id': llm_output.get('supplier_id'),
                'reasoning': llm_output['reasoning'],
                'confidence_level': llm_output.get('confidence_level', 'medium'),
                'risk_factors': llm_output.get('risk_factors', []),
                'alternative_actions': llm_output.get('alternative_actions', []),
                'llm_model_used': self.MODEL_NAME,
                'llm_response_time_ms': response_time_ms,
            }

            return decision

        except Exception as e:
            print(f'LLM decision failed: {e}')
            # Fallback to rule-based decision
            fallback_decision = self.make_rule_based_decision(decision_context)
            fallback_decision['llm_model_used'] = 'rule_based_fallback'
            fallback_decision['llm_response_time_ms'] = 0
            return fallback_decision
