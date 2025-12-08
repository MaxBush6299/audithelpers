"""
Evidence Evaluation Agent using Microsoft Agent Framework.

This agent evaluates whether provided evidence is sufficient to pass a PI calibration element
based on the calibrator instructions (Ask/Look For and Calibrator notes).
"""
from __future__ import annotations
import asyncio
import json
import os
import time
from dataclasses import dataclass
from typing import Optional, Dict, Any, List
from enum import Enum

from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class EvaluationStatus(str, Enum):
    """Possible evaluation statuses."""
    PASS = "Pass"
    FAIL = "Fail"
    NEEDS_MORE_EVIDENCE = "Needs More Evidence"
    ERROR = "Error"


@dataclass
class EvaluationResult:
    """Result of evaluating a single PI element."""
    pi_element: str
    status: EvaluationStatus
    llm_response: str
    evidence_slide_nums: List[int]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "PI-Element": self.pi_element,
            "Status": self.status.value,
            "LLM response": self.llm_response,
            "Evidence Slide num": self.evidence_slide_nums
        }


# System prompt for the evidence evaluation agent
EVALUATION_SYSTEM_PROMPT = """You are an expert calibration auditor evaluating whether evidence slides sufficiently demonstrate compliance with PI (Performance Indicator) calibration elements.

## Your Role
You will be given:
1. A PI Element ID (e.g., "2.1", "3.4")
2. Calibrator instructions containing:
   - "Ask/Look For": What the calibrator should ask for or look for during the calibration
   - "Calibrator notes": Additional guidance and context for the calibrator
3. Evidence slides: Text extracted from presentation slides that contain evidence for this element

## Evaluation Criteria
Based on the calibrator instructions, evaluate whether the provided evidence:

**PASS**: The evidence clearly demonstrates compliance with the element requirements. The evidence shows:
- Direct answers to what should be "asked for" or "looked for"
- Documentation, processes, or examples that meet the stated criteria
- Sufficient detail to validate the element during calibration

**FAIL**: The evidence is present but clearly does NOT meet the requirements because:
- The evidence contradicts the requirements
- The evidence shows non-compliance or deficiencies
- The documentation/processes shown do not align with what is required

**NEEDS MORE EVIDENCE**: The evidence is insufficient to make a determination because:
- The evidence is partial or incomplete
- Key aspects of the requirements are not addressed
- The evidence is unclear or ambiguous
- More context or documentation is needed

## Response Format
Respond with a JSON object containing:
- "status": One of "Pass", "Fail", or "Needs More Evidence"
- "reasoning": A brief explanation (2-4 sentences) of why you assigned this status, referencing specific evidence or gaps

Example response:
```json
{
    "status": "Pass",
    "reasoning": "The evidence shows the site's Safety-FMEA hazard and risk inventory with documented high-risk tasks and an active risk reduction plan. The slides demonstrate both the identification process and corrective action tracking as required by the element."
}
```

Be objective and base your evaluation solely on what is shown in the evidence versus what is required by the calibrator instructions."""


class EvidenceEvaluationAgent:
    """Agent for evaluating PI element evidence using Azure OpenAI."""
    
    def __init__(
        self,
        endpoint: Optional[str] = None,
        api_key: Optional[str] = None,
        deployment: Optional[str] = None,
        api_version: str = "2024-12-01-preview",
        max_retries: int = 3,
        retry_delay: float = 1.0
    ):
        """
        Initialize the evidence evaluation agent.
        
        Args:
            endpoint: Azure OpenAI endpoint (defaults to AZURE_AI_ENDPOINT env var)
            api_key: Azure OpenAI API key (defaults to AZURE_AI_API_KEY env var)
            deployment: Model deployment name (defaults to GPT_4_1_DEPLOYMENT env var)
            api_version: Azure OpenAI API version
            max_retries: Maximum number of retry attempts on failure
            retry_delay: Base delay between retries (exponential backoff applied)
        """
        self.endpoint = endpoint or os.getenv("AZURE_AI_ENDPOINT")
        self.api_key = api_key or os.getenv("AZURE_AI_API_KEY")
        self.deployment = deployment or os.getenv("GPT_4_1_DEPLOYMENT")
        self.api_version = api_version
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        
        if not self.endpoint:
            raise ValueError("Azure endpoint not configured. Set AZURE_AI_ENDPOINT environment variable.")
        if not self.api_key:
            raise ValueError("Azure API key not configured. Set AZURE_AI_API_KEY environment variable.")
        if not self.deployment:
            raise ValueError("Model deployment not configured. Set GPT_4_1_DEPLOYMENT environment variable.")
        
        # Initialize the OpenAI client
        from openai import AzureOpenAI
        self.client = AzureOpenAI(
            azure_endpoint=self.endpoint,
            api_key=self.api_key,
            api_version=self.api_version
        )
    
    def _build_user_prompt(
        self,
        pi_element: str,
        ask_look_for: str,
        calibrator_notes: str,
        evidence_texts: List[Dict[str, Any]]
    ) -> str:
        """Build the user prompt for evaluation."""
        prompt_parts = [
            f"## PI Element: {pi_element}",
            "",
            "## Calibrator Instructions",
            f"**Ask/Look For:** {ask_look_for}",
            "",
            f"**Calibrator Notes:** {calibrator_notes}",
            "",
            "## Evidence Slides",
        ]
        
        if not evidence_texts:
            prompt_parts.append("*No evidence slides provided for this element.*")
        else:
            for i, evidence in enumerate(evidence_texts, 1):
                slide_num = evidence.get("slide_index", "?")
                text = evidence.get("full_text", evidence.get("text_preview", ""))
                prompt_parts.append(f"### Slide {slide_num}")
                prompt_parts.append(text)
                prompt_parts.append("")
        
        prompt_parts.append("## Your Evaluation")
        prompt_parts.append("Evaluate the evidence and respond with a JSON object containing 'status' and 'reasoning'.")
        
        return "\n".join(prompt_parts)
    
    def _parse_response(self, response_text: str) -> Dict[str, str]:
        """Parse the LLM response to extract status and reasoning."""
        # Try to extract JSON from the response
        try:
            # Look for JSON block in markdown code fence
            import re
            json_match = re.search(r'```(?:json)?\s*(\{.*?\})\s*```', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group(1))
            
            # Try to parse the entire response as JSON
            return json.loads(response_text)
        except json.JSONDecodeError:
            # If parsing fails, try to extract status from text
            response_lower = response_text.lower()
            if "pass" in response_lower and "fail" not in response_lower:
                status = "Pass"
            elif "fail" in response_lower:
                status = "Fail"
            else:
                status = "Needs More Evidence"
            
            return {
                "status": status,
                "reasoning": response_text
            }
    
    def evaluate_element(
        self,
        pi_element: str,
        ask_look_for: str,
        calibrator_notes: str,
        evidence: List[Dict[str, Any]]
    ) -> EvaluationResult:
        """
        Evaluate a single PI element's evidence.
        
        Args:
            pi_element: The PI element ID (e.g., "2.1")
            ask_look_for: The "Ask/Look For" instructions
            calibrator_notes: The calibrator notes
            evidence: List of evidence slide dictionaries
            
        Returns:
            EvaluationResult with status, reasoning, and slide numbers
        """
        # Extract slide numbers
        slide_nums = [e.get("slide_index", 0) for e in evidence]
        
        # If no evidence, immediately return "Needs More Evidence"
        if not evidence:
            return EvaluationResult(
                pi_element=pi_element,
                status=EvaluationStatus.NEEDS_MORE_EVIDENCE,
                llm_response="No evidence slides were provided for this element. Cannot evaluate without evidence.",
                evidence_slide_nums=slide_nums
            )
        
        # Build the prompt
        user_prompt = self._build_user_prompt(
            pi_element=pi_element,
            ask_look_for=ask_look_for,
            calibrator_notes=calibrator_notes,
            evidence_texts=evidence
        )
        
        # Attempt evaluation with retries
        last_error = None
        for attempt in range(self.max_retries):
            try:
                response = self.client.chat.completions.create(
                    model=self.deployment,
                    messages=[
                        {"role": "system", "content": EVALUATION_SYSTEM_PROMPT},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,  # Low temperature for consistent evaluations
                )
                
                response_text = response.choices[0].message.content
                parsed = self._parse_response(response_text)
                
                # Map status string to enum
                status_str = parsed.get("status", "Needs More Evidence")
                if status_str.lower() == "pass":
                    status = EvaluationStatus.PASS
                elif status_str.lower() == "fail":
                    status = EvaluationStatus.FAIL
                else:
                    status = EvaluationStatus.NEEDS_MORE_EVIDENCE
                
                return EvaluationResult(
                    pi_element=pi_element,
                    status=status,
                    llm_response=parsed.get("reasoning", response_text),
                    evidence_slide_nums=slide_nums
                )
                
            except Exception as e:
                last_error = e
                if attempt < self.max_retries - 1:
                    # Exponential backoff
                    delay = self.retry_delay * (2 ** attempt)
                    print(f"  Attempt {attempt + 1} failed: {e}. Retrying in {delay:.1f}s...")
                    time.sleep(delay)
        
        # All retries exhausted
        return EvaluationResult(
            pi_element=pi_element,
            status=EvaluationStatus.ERROR,
            llm_response=f"Evaluation failed after {self.max_retries} attempts. Last error: {str(last_error)}",
            evidence_slide_nums=slide_nums
        )
