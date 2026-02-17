"""
TQS (Test Question Sheet) Service Module

This module generates actual test questions from an exam blueprint (assigned slots).

Design Principles:
1. SLOT-BASED GENERATION: One question per slot (1:1 mapping guaranteed)
2. POINT PRESERVATION: Questions worth exactly what blueprint specifies (no redistribution)
3. TYPE ALIGNMENT: Question types match slot specifications (MCQ, Essay, etc.)
4. BLOOM ALIGNMENT: Question complexity matches cognitive level
5. METADATA PRESERVATION: All outcome/learning data preserved from slots
6. RUBRIC VALIDATION: All rubrics validated and auto-scaled if needed
7. TOS PROTECTION: Input TOS matrix never modified (read-only consumption)

Workflow:
    Assigned Slots (from Phase 2 soft-mapping)
         ↓
    For each slot: generate_question_with_gemini()
         ├─ Type-specific prompt generation
         ├─ Gemini API call
         ├─ JSON response parsing
         ├─ Schema validation
         └─ Metadata enrichment
         ↓
    Collect all questions
         ↓
    Optional: Shuffle questions
         ↓
    Reassign question_number sequentially
         ↓
    Final TQS (1 question per slot)

Key Guarantees:
    ✅ Question count = Slot count (1:1 guaranteed)
    ✅ Points from slots preserved exactly (no modification)
    ✅ Question numbers sequential after shuffle (1, 2, 3, ...)
    ✅ Outcome text preserved (not paraphrased)
    ✅ Bloom level reflected in question complexity
    ✅ Type-specific fields present (choices for MCQ, rubric for Essay, etc.)
    ✅ All rubric totals validated to equal points
"""

import json
import random
import logging
import os
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import jsonschema  # For schema validation

# Try to import from ai_service for Gemini integration
try:
    from services.ai_service import GeminiConfig
except ImportError:
    GeminiConfig = None

# Set up logging
logger = logging.getLogger(__name__)
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Development mode flag - set to True to get full error messages
DEVELOPMENT_MODE = os.getenv('SMARTLESSON_DEV_MODE', 'False').lower() == 'true'

# =============================================================================
# JSON SCHEMAS FOR VALIDATION
# =============================================================================

# MCQ Schema - Simple structure for multiple choice questions
MCQ_SCHEMA = {
    "type": "object",
    "required": ["question_text", "choices", "correct_answer"],
    "properties": {
        "question_text": {"type": "string"},
        "choices": {
            "type": "array",
            "minItems": 4,
            "maxItems": 4,
            "items": {"type": "string"}
        },
        "correct_answer": {"type": "string"}
    }
}

# Short Answer Schema - Text + answer key + optional rubric
SHORT_ANSWER_SCHEMA = {
    "type": "object",
    "required": ["question_text", "answer_key"],
    "properties": {
        "question_text": {"type": "string"},
        "answer_key": {"type": "string"},
        "rubric": {
            "type": "object",
            "properties": {
                "criteria": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["descriptor", "points"],
                        "properties": {
                            "descriptor": {"type": "string"},
                            "points": {"type": "number"}
                        }
                    }
                },
                "total_points": {"type": "number"}
            }
        }
    }
}

# Constructed Response Schema - Full rubric required (Essay, Problem Solving, Drawing)
CONSTRUCTED_RESPONSE_SCHEMA = {
    "type": "object",
    "required": ["question_text", "sample_answer", "rubric"],
    "properties": {
        "question_text": {"type": "string"},
        "sample_answer": {"type": "string"},
        "rubric": {
            "type": "object",
            "required": ["criteria", "total_points"],
            "properties": {
                "criteria": {
                    "type": "array",
                    "minItems": 1,
                    "items": {
                        "type": "object",
                        "required": ["descriptor", "points"],
                        "properties": {
                            "descriptor": {"type": "string"},
                            "points": {"type": "number"}
                        }
                    }
                },
                "total_points": {"type": "number"}
            }
        }
    }
}


# =============================================================================
# GEMINI API VALIDATION AND ERROR HANDLING
# =============================================================================

def validate_api_key() -> str:
    """
    Validate that GEMINI_API_KEY is set and return it.
    
    Raises:
        EnvironmentError: If GEMINI_API_KEY is not set
    """
    api_key = os.getenv('GEMINI_API_KEY')
    if not api_key:
        error_msg = (
            "GEMINI_API_KEY environment variable is not set. \n"
            "Please set it before running TQS generation. \n"
            "Example: export GEMINI_API_KEY='your-api-key-here'"
        )
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    
    logger.info(f"✓ GEMINI_API_KEY found (length: {len(api_key)} chars)")
    return api_key


def configure_gemini_api(api_key: str) -> bool:
    """
    Configure Gemini API with the given API key using google-genai package.
    
    Args:
        api_key: Google Gemini API key
    
    Returns:
        True if configuration successful
    
    Raises:
        EnvironmentError: If google-genai cannot be imported
    """
    try:
        # Use the new google-genai package (google.generativeai is deprecated)
        import google.genai as genai
        
        # Verify we can create a client (validates API key format)
        test_client = genai.Client(api_key=api_key)
        logger.debug("Gemini API (google-genai) configured successfully")
        return True
    except ImportError as e:
        error_msg = (
            f"google-genai package is not installed. \n"
            f"Install it with: pip install google-genai\n"
            f"Or update: pip install --upgrade google-genai\n"
            f"Error: {str(e)}"
        )
        logger.error(error_msg)
        raise EnvironmentError(error_msg)
    except Exception as e:
        error_msg = f"Failed to configure Gemini API: {str(e)}"
        logger.error(error_msg)
        raise EnvironmentError(error_msg)


def interpret_api_error(error: Exception) -> Tuple[str, str]:
    """
    Interpret common Gemini API errors and provide actionable messages.
    
    Args:
        error: The exception from Gemini API call
    
    Returns:
        Tuple of (error_type, user_friendly_message)
    """
    error_str = str(error).lower()
    error_type_name = type(error).__name__
    
    # Check for common error patterns
    if "401" in error_str or "invalid api key" in error_str or "unauthenticated" in error_str:
        return ("AUTH_ERROR", 
                "Invalid API Key: Your GEMINI_API_KEY is invalid or expired. "
                "Please check your API key and try again.")
    
    elif "429" in error_str or "rate_limit" in error_str or "quota" in error_str:
        return ("RATE_LIMIT", 
                "Rate Limit Exceeded: Too many requests to Gemini API. "
                "Please wait a moment and try again.")
    
    elif "timeout" in error_str or "deadline exceeded" in error_str:
        return ("TIMEOUT", 
                "Network Timeout: Request to Gemini API took too long. "
                "This may indicate a network issue or server overload.")
    
    elif "503" in error_str or "unavailable" in error_str:
        return ("SERVICE_UNAVAILABLE", 
                "Gemini Service Unavailable: The service is temporarily down. "
                "Please try again later.")
    
    elif "context" in error_str or "tokens" in error_str or "length" in error_str:
        return ("TOKEN_LIMIT", 
                "Prompt Too Long: The prompt exceeds token limit. "
                "This question will be retried or skipped.")
    
    else:
        return ("UNKNOWN_ERROR", f"Unexpected error: {str(error)}")


def group_slots_by_characteristics(slots: List[Dict[str, Any]]) -> Dict[Tuple, List[Dict[str, Any]]]:
    """
    Group slots by (question_type, bloom_level, learning_outcome).
    
    This reduces API calls from N (per slot) to G (per group).
    
    Args:
        slots: List of assigned slots
    
    Returns:
        Dictionary mapping (type, bloom, outcome) -> [slots with these characteristics]
    
    Example:
        Input: 50 slots
        Groups: 12 groups (e.g., 5 MCQ/Apply/Outcome1, 3 Essay/Evaluate/Outcome2, ...)
        API calls: 12 instead of 50
    """
    groups = {}
    
    for slot in slots:
        key = (
            slot.get("question_type", "MCQ"),
            slot.get("bloom_level", "Remember"),
            slot.get("outcome_text", "")
        )
        
        if key not in groups:
            groups[key] = []
        
        groups[key].append(slot)
    
    logger.info(f"Grouped {len(slots)} slots into {len(groups)} groups by characteristics")
    for key, group_slots in groups.items():
        qtype, bloom, outcome = key
        logger.debug(f"  Group: {qtype} / {bloom} / {str(outcome)[:40]}... ({len(group_slots)} slots)")
    
    return groups


def generate_batch_questions(
    batch_slots: List[Dict[str, Any]],
    api_key: str
) -> List[Dict[str, Any]]:
    """
    Generate multiple test questions from a batch of slots with same characteristics.
    
    Instead of N API calls (one per slot), makes 1 API call requesting N questions.
    Dramatically reduces API quota consumption: 50 slots → ~10 groups → 10 API calls.
    
    Args:
        batch_slots: List of slots with same (question_type, bloom_level, outcome_text)
        api_key: Google Gemini API key
    
    Returns:
        List of generated questions (one per input slot)
    
    Raises:
        Exception: Re-raises API errors for proper error handling
    """
    if not batch_slots:
        return []
    
    # Extract batch characteristics from first slot (all should be identical)
    question_type = batch_slots[0].get("question_type", "MCQ")
    bloom_level = batch_slots[0].get("bloom_level", "Remember")
    outcome = batch_slots[0].get("outcome_text", "")
    num_questions = len(batch_slots)
    
    logger.info(f"Generating batch of {num_questions} {question_type} questions at {bloom_level} level")
    logger.debug(f"Learning Outcome: {outcome[:60]}...")
    
    try:
        import google.genai as genai
        
        # Create client
        client = genai.Client(api_key=api_key)
        
        # =====================================================================
        # BUILD PROMPT FOR BATCH GENERATION
        # =====================================================================
        
        if question_type == "MCQ":
            prompt = f"""Generate exactly {num_questions} MULTIPLE CHOICE questions for the following learning outcome:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Multiple Choice (4 options each)
Points per question: 1 point

Requirements:
1. Generate EXACTLY {num_questions} questions
2. Each question must be distinct from others
3. Each question includes 4 options (A, B, C, D) with only one correct answer
4. Distractors are plausible but clearly incorrect
5. Cognitive complexity matches {bloom_level} level
6. All questions align with the learning outcome

CRITICAL: Return output as a STRICT JSON array (no markdown, no code blocks, just raw JSON):
[
  {{
    "question_text": "...",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "B"
  }},
  {{
    "question_text": "...",
    "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
    "correct_answer": "A"
  }}
  ...
]

Return ONLY the JSON array, with NO other text."""
        
        elif question_type == "Short Answer":
            prompt = f"""Generate exactly {num_questions} SHORT ANSWER assessment questions for:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Short Answer
Points per question: 1 point

Requirements:
1. Generate EXACTLY {num_questions} distinct questions
2. Each question prompts a brief written response (1-3 sentences)
3. Include answer key for each question
4. Cognitive complexity matches {bloom_level} level

CRITICAL: Return output as a STRICT JSON array:
[
  {{
    "question_text": "...",
    "answer_key": "..."
  }},
  {{
    "question_text": "...",
    "answer_key": "..."
  }}
  ...
]

Return ONLY the JSON array, with NO other text."""
        
        elif question_type == "Essay":
            prompt = f"""Generate exactly {num_questions} ESSAY assessment questions for:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Essay
Points per question: 1 point

Requirements:
1. Generate EXACTLY {num_questions} distinct essay questions
2. Each requires comprehensive written response (2-3 paragraphs)
3. Include sample answer for each
4. Cognitive complexity matches {bloom_level} level

CRITICAL: Return output as a STRICT JSON array:
[
  {{
    "question_text": "...",
    "sample_answer": "..."
  }},
  {{
    "question_text": "...",
    "sample_answer": "..."
  }}
  ...
]

Return ONLY the JSON array, with NO other text."""
        
        elif question_type == "Problem Solving":
            prompt = f"""Generate exactly {num_questions} PROBLEM SOLVING assessment questions for:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Problem Solving
Points per question: 1 point

Requirements:
1. Generate EXACTLY {num_questions} distinct problem scenarios
2. Each should be realistically solvable
3. Include sample solution for each
4. Cognitive complexity matches {bloom_level} level

CRITICAL: Return output as a STRICT JSON array:
[
  {{
    "question_text": "...",
    "sample_answer": "Step 1: ... Step 2: ..."
  }},
  {{
    "question_text": "...",
    "sample_answer": "Step 1: ... Step 2: ..."
  }}
  ...
]

Return ONLY the JSON array, with NO other text."""
        
        elif question_type == "Drawing":
            prompt = f"""Generate exactly {num_questions} DRAWING/VISUAL assessment questions for:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Drawing/Visual
Points per question: 1 point

Requirements:
1. Generate EXACTLY {num_questions} distinct drawing/visual questions
2. Questions ask student to create diagram or visual representation
3. Be specific about what to draw
4. Include description of expected response
5. Cognitive complexity matches {bloom_level} level

CRITICAL: Return output as a STRICT JSON array:
[
  {{
    "question_text": "...",
    "sample_answer": "Should include: ..."
  }},
  {{
    "question_text": "...",
    "sample_answer": "Should include: ..."
  }}
  ...
]

Return ONLY the JSON array, with NO other text."""
        
        else:
            logger.error(f"Unknown question type for batch: {question_type}")
            return []
        
        # =====================================================================
        # CALL GEMINI WITH BATCH PROMPT
        # =====================================================================
        logger.info(f"[BATCH API CALL] {num_questions} {question_type} questions")
        logger.debug(f"Prompt length: {len(prompt)} chars")
        
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents=prompt
        )
        
        response_text = response.text if hasattr(response, 'text') else str(response)
        logger.debug(f"API Response received: {str(response_text)[:200]}...")
        
        # =====================================================================
        # PARSE JSON ARRAY RESPONSE
        # =====================================================================
        
        # Try to extract JSON array from response
        import re
        
        # Pattern: ```json [ ... ] ``` or similar
        code_block_pattern = r'```(?:json)?\s*(\[.*?\])\s*```'
        match = re.search(code_block_pattern, response_text, re.DOTALL)
        json_array = None
        
        if match:
            try:
                json_array = json.loads(match.group(1))
            except json.JSONDecodeError as e:
                logger.warning(f"Failed to parse JSON from code block: {e}")
        
        # Try plain JSON array if code block failed
        if json_array is None:
            plain_json_pattern = r'(\[.*\])'
            match = re.search(plain_json_pattern, response_text, re.DOTALL)
            if match:
                try:
                    json_array = json.loads(match.group(1))
                except json.JSONDecodeError as e:
                    logger.warning(f"Failed to parse JSON array: {e}")
        
        # Last resort: try entire response
        if json_array is None:
            try:
                json_array = json.loads(response_text)
            except json.JSONDecodeError as e:
                logger.error(f"Could not parse batch response as JSON: {e}")
                logger.debug(f"Response text: {response_text[:500]}")
                return []
        
        if not isinstance(json_array, list):
            logger.error(f"Response is not a JSON array, got {type(json_array).__name__}")
            return []
        
        logger.info(f"✓ Parsed {len(json_array)} questions from API response")
        
        # =====================================================================
        # CRITICAL CHECK: Verify we got the expected number of questions
        # =====================================================================
        expected_count = len(batch_slots)
        actual_count = len(json_array)
        
        if actual_count != expected_count:
            logger.error(
                f"❌ BATCH QUESTION COUNT MISMATCH!\n"
                f"   Expected: {expected_count} questions\n"
                f"   Got: {actual_count} questions\n"
                f"   Missing: {expected_count - actual_count} questions\n"
                f"This indicates the API did not return the requested number of questions."
            )
            # Return empty list to trigger retry with exponential backoff
            return []
        
        # =====================================================================
        # MERGE WITH SLOT METADATA
        # =====================================================================
        
        generated_questions = []
        logger.info(f"Merging {len(json_array)} API questions with {len(batch_slots)} slot definitions...")
        
        for idx, (json_question, slot) in enumerate(zip(json_array, batch_slots)):
            if not isinstance(json_question, dict):
                logger.warning(f"Question {idx} is not a dict, skipping")
                continue
            
            try:
                # Create enriched question with metadata from slot
                question = {
                    "question_number": 0,  # Assigned later
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Both field name variants for compatibility
                    "type": question_type,
                    "question_type": question_type,
                    "bloom": bloom_level,
                    "bloom_level": bloom_level,
                    "learning_outcome": outcome,
                    "points": slot.get("points", 1),  # Use actual points from slot
                    # Merge AI-generated content
                    "question_text": json_question.get("question_text", ""),
                    "choices": json_question.get("choices", []),
                    "correct_answer": json_question.get("correct_answer", ""),
                    "answer_key": json_question.get("answer_key", ""),
                    "sample_answer": json_question.get("sample_answer", ""),
                    "rubric": json_question.get("rubric", {}),
                    "generated_at": datetime.now().isoformat()
                }
                
                # Validate and scale rubric if present
                if question.get("rubric"):
                    question["rubric"] = validate_and_scale_rubric(
                        question["rubric"], 
                        question["points"]
                    )
                
                generated_questions.append(question)
                logger.debug(f"  ✓ Question {idx + 1}/{len(json_array)} merged successfully")
            
            except Exception as e:
                logger.error(f"Error merging question {idx}: {e}")
                continue
        
        logger.info(f"✓ Successfully merged {len(generated_questions)} questions from batch")
        return generated_questions
    
    except Exception as e:
        error_type, user_msg = interpret_api_error(e)
        logger.error(f"Batch generation error [{error_type}]: {user_msg}")
        logger.debug(f"Raw error: {type(e).__name__}: {str(e)}")
        if DEVELOPMENT_MODE:
            logger.exception("Full traceback:")
        raise


def extract_json_from_response(response_text: str) -> Optional[Dict[str, Any]]:
    """
    Extract JSON from Gemini response which may contain markdown code blocks.
    
    Handles formats like:
    - ```json { ... } ```
    - ```{ ... }```
    - { ... } (plain JSON)
    - Other text with { ... } embedded
    """
    try:
        # Try to find JSON in code blocks first
        import re
        
        # Pattern: ```json ... ``` or similar
        code_block_pattern = r'```(?:json)?\s*(\{.*?\})\s*```'
        match = re.search(code_block_pattern, response_text, re.DOTALL)
        if match:
            json_str = match.group(1)
            return json.loads(json_str)
        
        # Pattern: plain JSON object { ... }
        plain_json_pattern = r'(\{.*\})'
        match = re.search(plain_json_pattern, response_text, re.DOTALL)
        if match:
            try:
                return json.loads(match.group(1))
            except json.JSONDecodeError:
                pass
        
        # Try parsing entire response as JSON
        return json.loads(response_text)
    
    except Exception as e:
        logger.warning(f"Failed to extract JSON from response: {e}")
        return None


def validate_and_scale_rubric(rubric: Dict[str, Any], required_points: float) -> Dict[str, Any]:
    """
    Validate rubric totals and auto-scale if needed.
    
    If rubric total doesn't match required points:
    - Calculate scale factor
    - Proportionally adjust all criteria points
    - Update total to match exactly
    
    This ensures rubrics are always valid while preserving proportion.
    """
    if "criteria" not in rubric or not rubric["criteria"]:
        return rubric
    
    try:
        current_total = sum(c.get("points", 0) for c in rubric["criteria"])
        
        if current_total == 0:
            # Distribute points evenly
            points_per_criterion = required_points / len(rubric["criteria"])
            for criterion in rubric["criteria"]:
                criterion["points"] = points_per_criterion
            rubric["total_points"] = required_points
        
        elif current_total != required_points:
            # Scale proportionally
            scale_factor = required_points / current_total
            for criterion in rubric["criteria"]:
                criterion["points"] = criterion.get("points", 0) * scale_factor
            rubric["total_points"] = required_points
            
            logger.info(
                f"Auto-scaled rubric: {current_total} → {required_points} "
                f"(scale factor: {scale_factor:.2f})"
            )
        else:
            rubric["total_points"] = required_points
    
    except Exception as e:
        logger.warning(f"Error validating rubric: {e}")
        rubric["total_points"] = required_points
    
    return rubric


def generate_question_with_gemini(slot: Dict[str, Any], api_key: str) -> Optional[Dict[str, Any]]:
    """
    Generate a single test question for a given slot using Gemini API.
    
    This is the core generation function that:
    1. Creates a type-specific prompt
    2. Calls Gemini API with detailed error handling
    3. Parses and validates response
    4. Returns enriched question with metadata
    
    Args:
        slot: Dictionary containing:
            - outcome_id: Identifier for learning outcome
            - outcome_text: Text of learning outcome
            - bloom_level: Bloom's taxonomy level
            - question_type: Question type (MCQ, Short Answer, Essay, Problem Solving, Drawing)
            - points: Point value for this question
        
        api_key: Google Gemini API key
    
    Returns:
        Dictionary with generated question and metadata, or None if generation fails
    
    Raises:
        Exception: Re-raises API errors for proper error handling and logging
    """
    
    try:
        import google.genai as genai
        
        # Configure Gemini
        configure_gemini_api(api_key)
        
        # Create client (google-genai uses a different API than deprecated google.generativeai)
        client = genai.Client(api_key=api_key)
        
        # Extract slot data using correct field names
        question_type = slot.get("question_type", "MCQ")
        bloom_level = slot.get("bloom_level", "Remember")
        outcome = slot.get("outcome_text", "")
        points = slot.get("points", 1)
        outcome_id = slot.get("outcome_id", "?")
        
        # Debug logging
        logger.debug(f"[DEBUG] Processing slot {outcome_id}:")
        logger.debug(f"  - Question Type: {question_type}")
        logger.debug(f"  - Bloom Level: {bloom_level}")
        logger.debug(f"  - Points: {points}")
        logger.debug(f"  - Outcome: {outcome[:60]}...")
        
        logger.info(f"Generating {question_type} for outcome: {outcome[:50]}...")
        
        # =====================================================================
        # MCQ Generation
        # =====================================================================
        if question_type == "MCQ":
            prompt = f"""Generate an assessment question based on the following:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Multiple Choice (4 options)
Points: {points}

Requirements:
1. Question text should be clear and unambiguous
2. Provide exactly 4 answer choices (A, B, C, D)
3. One choice is correct
4. Distractors should be plausible but clearly incorrect
5. Cognitive complexity should match {bloom_level} level

Return ONLY a JSON object with this structure:
{{
  "question_text": "...",
  "choices": ["A) ...", "B) ...", "C) ...", "D) ..."],
  "correct_answer": "B"
}}

Make the question challenging but fair."""

            logger.debug(f"MCQ Prompt (length: {len(prompt)} chars):\n{prompt[:200]}...")
            
            try:
                logger.info(f"Calling Gemini API for MCQ...")
                logger.debug(f"[API CALL] Model: gemini-2.0-flash, Prompt length: {len(prompt)} chars")
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                logger.debug(f"API Response received: {str(response.text)[:200]}...")
                
                json_data = extract_json_from_response(response.text)
                
                if not json_data:
                    logger.error("Failed to parse MCQ JSON response")
                    logger.debug(f"Raw response: {response.text[:500]}")
                    return None
                
                # Validate against schema
                try:
                    jsonschema.validate(instance=json_data, schema=MCQ_SCHEMA)
                except jsonschema.ValidationError as e:
                    logger.error(f"MCQ validation failed: {e}")
                    logger.debug(f"JSON data: {json.dumps(json_data, indent=2)[:500]}")
                    return None
                
                # Enrich with BOTH metadata from slot AND AI output
                # NOTE: Do NOT rely on AI for structural metadata (type, bloom_level, points, outcome)
                question = {
                    "question_number": 0,  # Will be assigned later
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Include both field name variants for compatibility
                    "type": question_type,  # For frontend summary
                    "question_type": question_type,  # For backward compatibility
                    "bloom": bloom_level,  # For frontend summary
                    "bloom_level": bloom_level,  # Standard field name
                    "learning_outcome": outcome,  # For frontend display
                    "points": points,
                    # AI-generated content
                    "question_text": json_data.get("question_text", ""),
                    "choices": json_data.get("choices", []),
                    "correct_answer": json_data.get("correct_answer", ""),
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✓ MCQ generated successfully")
                return question
            
            except Exception as api_error:
                error_type, user_msg = interpret_api_error(api_error)
                logger.error(f"API error during MCQ generation [{error_type}]: {user_msg}")
                logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
                logger.debug(f"Prompt length: {len(prompt)} chars")
                if DEVELOPMENT_MODE:
                    logger.debug(f"Prompt: {prompt[:300]}")
                raise
        
        # =====================================================================
        # SHORT ANSWER Generation
        # =====================================================================
        elif question_type == "Short Answer":
            rubric_instruction = ""
            if points > 3:
                rubric_instruction = f"""RUBRIC: Since this is worth {points} points, provide a rubric with scoring criteria:
- Multiple criteria (2-4)
- Each criterion has a descriptor and points
- Total must equal {points}"""
            
            prompt = f"""Generate a short answer assessment question based on:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Short Answer
Points: {points}

{rubric_instruction}

Requirements:
1. Question text should prompt a brief written response (1-3 sentences)
2. Provide a concise answer key (the correct answer)
3. If rubric provided, each criterion must have points that total {points}
4. Cognitive complexity matches {bloom_level} level

Return ONLY valid JSON with this structure:
{{
  "question_text": "...",
  "answer_key": "...",
  "rubric": {{
    "criteria": [
      {{"descriptor": "...", "points": X}},
      {{"descriptor": "...", "points": Y}}
    ],
    "total_points": {points}
  }}
}}

If rubric not provided, return null for rubric field."""

            logger.debug(f"Short Answer Prompt (length: {len(prompt)} chars):\n{prompt[:200]}...")
            
            try:
                logger.info(f"Calling Gemini API for Short Answer...")
                logger.debug(f"[API CALL] Model: gemini-2.0-flash, Prompt length: {len(prompt)} chars")
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                # Get response text
                response_text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                logger.debug(f"API Response received: {str(response_text)[:200]}...")
                
                json_data = extract_json_from_response(response_text)
                
                if not json_data:
                    logger.error("Failed to parse Short Answer JSON response")
                    logger.debug(f"Raw response: {response_text[:500]}")
                    return None
                
                try:
                    jsonschema.validate(instance=json_data, schema=SHORT_ANSWER_SCHEMA)
                except jsonschema.ValidationError as e:
                    logger.error(f"Short Answer validation failed: {e}")
                    logger.debug(f"JSON data: {json.dumps(json_data, indent=2)[:500]}")
                    return None
                
                # Validate and scale rubric if present
                if json_data.get("rubric"):
                    json_data["rubric"] = validate_and_scale_rubric(json_data["rubric"], points)
                
                question = {
                    "question_number": 0,
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Include both field name variants for compatibility
                    "type": question_type,  # For frontend summary
                    "question_type": question_type,  # For backward compatibility
                    "bloom": bloom_level,  # For frontend summary
                    "bloom_level": bloom_level,  # Standard field name
                    "learning_outcome": outcome,  # For frontend display
                    "points": points,
                    "question_text": json_data.get("question_text", ""),
                    "answer_key": json_data.get("answer_key", ""),
                    "generated_at": datetime.now().isoformat()
                }
                
                if json_data.get("rubric"):
                    question["rubric"] = json_data["rubric"]
                
                logger.info(f"✓ Short Answer generated successfully")
                return question
            
            except Exception as api_error:
                error_type, user_msg = interpret_api_error(api_error)
                logger.error(f"API error during Short Answer generation [{error_type}]: {user_msg}")
                logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
                logger.debug(f"Prompt length: {len(prompt)} chars")
                if DEVELOPMENT_MODE:
                    logger.debug(f"Prompt: {prompt[:300]}")
                raise
        
        # =====================================================================
        # ESSAY Generation
        # =====================================================================
        elif question_type == "Essay":
            prompt = f"""Generate an essay assessment question based on:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Essay (requires comprehensive written response)
Points: {points}

Requirements:
1. Question text should prompt an extended written response (2-3 paragraphs)
2. Include a sample/model answer (2-3 paragraphs)
3. Provide a detailed rubric with 3-4 criteria
4. Each criterion has a descriptor and points
5. All points must total {points}
6. Cognitive complexity matches {bloom_level} level

Return ONLY valid JSON:
{{
  "question_text": "...",
  "sample_answer": "...",
  "rubric": {{
    "criteria": [
      {{"descriptor": "...", "points": X}},
      {{"descriptor": "...", "points": Y}},
      {{"descriptor": "...", "points": Z}}
    ],
    "total_points": {points}
  }}
}}"""

            logger.debug(f"Essay Prompt (length: {len(prompt)} chars):\n{prompt[:200]}...")
            
            try:
                logger.info(f"Calling Gemini API for Essay...")
                logger.debug(f"[API CALL] Model: gemini-2.0-flash, Prompt length: {len(prompt)} chars")
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                # Get response text
                response_text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                logger.debug(f"API Response received: {str(response_text)[:200]}...")
                
                json_data = extract_json_from_response(response_text)
                
                if not json_data:
                    logger.error("Failed to parse Essay JSON response")
                    logger.debug(f"Raw response: {response_text[:500]}")
                    return None
                
                try:
                    jsonschema.validate(instance=json_data, schema=CONSTRUCTED_RESPONSE_SCHEMA)
                except jsonschema.ValidationError as e:
                    logger.error(f"Essay validation failed: {e}")
                    logger.debug(f"JSON data: {json.dumps(json_data, indent=2)[:500]}")
                    return None
                
                # Validate and scale rubric
                json_data["rubric"] = validate_and_scale_rubric(json_data["rubric"], points)
                
                question = {
                    "question_number": 0,
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Include both field name variants for compatibility
                    "type": question_type,  # For frontend summary
                    "question_type": question_type,  # For backward compatibility
                    "bloom": bloom_level,  # For frontend summary
                    "bloom_level": bloom_level,  # Standard field name
                    "learning_outcome": outcome,  # For frontend display
                    "points": points,
                    "question_text": json_data.get("question_text", ""),
                    "sample_answer": json_data.get("sample_answer", ""),
                    "rubric": json_data.get("rubric", {}),
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✓ Essay generated successfully")
                return question
            
            except Exception as api_error:
                error_type, user_msg = interpret_api_error(api_error)
                logger.error(f"API error during Essay generation [{error_type}]: {user_msg}")
                logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
                logger.debug(f"Prompt length: {len(prompt)} chars")
                if DEVELOPMENT_MODE:
                    logger.debug(f"Prompt: {prompt[:300]}")
                raise
        
        # =====================================================================
        # PROBLEM SOLVING Generation
        # =====================================================================
        elif question_type == "Problem Solving":
            prompt = f"""Generate a problem-solving assessment question based on:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Problem Solving
Points: {points}

Requirements:
1. Present a realistic problem scenario
2. Question asks student to solve or show work
3. Provide a sample solution with steps
4. Create a rubric evaluating problem-solving process and correctness
5. Rubric criteria (3-4) must total {points} points
6. Cognitive complexity matches {bloom_level} level

Return ONLY valid JSON:
{{
  "question_text": "...",
  "sample_answer": "Step 1: ... Step 2: ... etc",
  "rubric": {{
    "criteria": [
      {{"descriptor": "Understanding problem: ...", "points": X}},
      {{"descriptor": "Solution approach: ...", "points": Y}},
      {{"descriptor": "Mathematical accuracy: ...", "points": Z}}
    ],
    "total_points": {points}
  }}
}}"""

            logger.debug(f"Problem Solving Prompt (length: {len(prompt)} chars):\n{prompt[:200]}...")
            
            try:
                logger.info(f"Calling Gemini API for Problem Solving...")
                logger.debug(f"[API CALL] Model: gemini-2.0-flash, Prompt length: {len(prompt)} chars")
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                # Get response text
                response_text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                logger.debug(f"API Response received: {str(response_text)[:200]}...")
                
                json_data = extract_json_from_response(response_text)
                
                if not json_data:
                    logger.error("Failed to parse Problem Solving JSON response")
                    logger.debug(f"Raw response: {response_text[:500]}")
                    return None
                
                try:
                    jsonschema.validate(instance=json_data, schema=CONSTRUCTED_RESPONSE_SCHEMA)
                except jsonschema.ValidationError as e:
                    logger.error(f"Problem Solving validation failed: {e}")
                    logger.debug(f"JSON data: {json.dumps(json_data, indent=2)[:500]}")
                    return None
                
                # Validate and scale rubric
                json_data["rubric"] = validate_and_scale_rubric(json_data["rubric"], points)
                
                question = {
                    "question_number": 0,
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Include both field name variants for compatibility
                    "type": question_type,  # For frontend summary
                    "question_type": question_type,  # For backward compatibility
                    "bloom": bloom_level,  # For frontend summary
                    "bloom_level": bloom_level,  # Standard field name
                    "learning_outcome": outcome,  # For frontend display
                    "points": points,
                    "question_text": json_data.get("question_text", ""),
                    "sample_answer": json_data.get("sample_answer", ""),
                    "rubric": json_data.get("rubric", {}),
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✓ Problem Solving generated successfully")
                return question
            
            except Exception as api_error:
                error_type, user_msg = interpret_api_error(api_error)
                logger.error(f"API error during Problem Solving generation [{error_type}]: {user_msg}")
                logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
                logger.debug(f"Prompt length: {len(prompt)} chars")
                if DEVELOPMENT_MODE:
                    logger.debug(f"Prompt: {prompt[:300]}")
                raise
        
        # =====================================================================
        # DRAWING Generation
        # =====================================================================
        elif question_type == "Drawing":
            prompt = f"""Generate a drawing/visual assessment question based on:

Learning Outcome: {outcome}
Bloom Level: {bloom_level}
Question Type: Drawing/Visual (student creates diagram/drawing)
Points: {points}

Requirements:
1. Question asks student to draw, diagram, or create visual representation
2. Be specific about what to draw and what should be included
3. Provide a description of what a complete response should include
4. Create a rubric for evaluating the drawing
5. Rubric criteria (3-4) must total {points} points
6. Cognitive complexity matches {bloom_level} level

Return ONLY valid JSON:
{{
  "question_text": "...",
  "sample_answer": "A diagram should include: 1. ... 2. ... 3. ...",
  "rubric": {{
    "criteria": [
      {{"descriptor": "Completeness of diagram: ...", "points": X}},
      {{"descriptor": "Accuracy of labels/components: ...", "points": Y}},
      {{"descriptor": "Clear organization: ...", "points": Z}}
    ],
    "total_points": {points}
  }}
}}"""

            logger.debug(f"Drawing Prompt (length: {len(prompt)} chars):\n{prompt[:200]}...")
            
            try:
                logger.info(f"Calling Gemini API for Drawing...")
                logger.debug(f"[API CALL] Model: gemini-2.0-flash, Prompt length: {len(prompt)} chars")
                
                response = client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
                
                # Get response text
                response_text = response.text if hasattr(response, 'text') else response.candidates[0].content.parts[0].text
                logger.debug(f"API Response received: {str(response_text)[:200]}...")
                
                json_data = extract_json_from_response(response_text)
                
                if not json_data:
                    logger.error("Failed to parse Drawing JSON response")
                    logger.debug(f"Raw response: {response_text[:500]}")
                    return None
                
                try:
                    jsonschema.validate(instance=json_data, schema=CONSTRUCTED_RESPONSE_SCHEMA)
                except jsonschema.ValidationError as e:
                    logger.error(f"Drawing validation failed: {e}")
                    logger.debug(f"JSON data: {json.dumps(json_data, indent=2)[:500]}")
                    return None
                
                # Validate and scale rubric
                json_data["rubric"] = validate_and_scale_rubric(json_data["rubric"], points)
                
                question = {
                    "question_number": 0,
                    "outcome_id": slot.get("outcome_id", 0),
                    "outcome_text": outcome,
                    # REQUIRED: Include both field name variants for compatibility
                    "type": question_type,  # For frontend summary
                    "question_type": question_type,  # For backward compatibility
                    "bloom": bloom_level,  # For frontend summary
                    "bloom_level": bloom_level,  # Standard field name
                    "learning_outcome": outcome,  # For frontend display
                    "points": points,
                    "question_text": json_data.get("question_text", ""),
                    "sample_answer": json_data.get("sample_answer", ""),
                    "rubric": json_data.get("rubric", {}),
                    "generated_at": datetime.now().isoformat()
                }
                
                logger.info(f"✓ Drawing generated successfully")
                return question
            
            except Exception as api_error:
                error_type, user_msg = interpret_api_error(api_error)
                logger.error(f"API error during Drawing generation [{error_type}]: {user_msg}")
                logger.debug(f"Raw error: {type(api_error).__name__}: {str(api_error)}")
                logger.debug(f"Prompt length: {len(prompt)} chars")
                if DEVELOPMENT_MODE:
                    logger.debug(f"Prompt: {prompt[:300]}")
                raise
        
        else:
            logger.error(f"Unknown question type: {question_type}")
            return None
    
    except Exception as e:
        error_type, user_msg = interpret_api_error(e)
        logger.error(f"Error generating question [{error_type}]: {user_msg}")
        if DEVELOPMENT_MODE:
            logger.exception(f"Full traceback:")
        raise


def generate_tqs(
    assigned_slots: List[Dict[str, Any]],
    api_key: str = None,
    shuffle: bool = True
) -> List[Dict[str, Any]]:
    """
    Generate complete Test Question Sheet from exam blueprint slots.
    
    This is the main public function that orchestrates TQS generation:
    1. Validate API Key and Gemini configuration
    2. Validate all input slots
    3. For each slot, generate one question using Gemini (with batching)
    4. Collect all generated questions
    5. Optionally shuffle the questions
    6. Reassign question_number sequentially
    7. Verify and return final TQS
    
    Args:
        assigned_slots: List of slots from soft-mapping (Phase 2 output)
            Each slot must have:
            - outcome_id, outcome_text, bloom_level, question_type, points
        
        api_key: Google Gemini API key (if None, reads from GEMINI_API_KEY env var)
        
        shuffle: Boolean, whether to shuffle questions (default True)
    
    Returns:
        List of dictionaries, each representing a complete test question
        with all metadata and type-specific fields.
    
    Key Guarantees:
        ✅ Output length = Input length (1:1 slot-to-question mapping)
        ✅ Points preserved exactly from slots
        ✅ Question types match slot specifications
        ✅ Bloom levels reflected in complexity
        ✅ All required fields present
        ✅ All rubrics validated
    
    Raises:
        EnvironmentError: If GEMINI_API_KEY not set or Gemini not configured
        ValueError: If slots invalid
        RuntimeError: If all questions fail to generate
    """
    
    # =========================================================================
    # PHASE -1: VALIDATE API KEY AND GEMINI CONFIGURATION
    # =========================================================================
    logger.info(f"Validating Gemini API configuration...")
    
    # Use provided API key or get from environment
    if api_key is None:
        api_key = validate_api_key()
    else:
        logger.info(f"Using provided API key (length: {len(api_key)} chars)")
    
    # Test Gemini configuration
    try:
        configure_gemini_api(api_key)
    except EnvironmentError as e:
        logger.error(f"Failed to configure Gemini API: {str(e)}")
        raise
    
    logger.info(f"✓ Gemini API configured and ready")
    
    # =========================================================================
    # PHASE 0: VALIDATE INPUT SLOTS
    # =========================================================================
    logger.info(f"Starting TQS generation for {len(assigned_slots)} slots")
    logger.info(f"Shuffle: {shuffle}")
    logger.debug(f"Development mode: {DEVELOPMENT_MODE}")
    logger.debug(f"Batch size: 10 slots per batch (for token limit management)")
    
    logger.info("Validating assigned slots...")
    
    # Check if assigned_slots is valid
    if not assigned_slots or not isinstance(assigned_slots, list):
        error_msg = f"Invalid assigned_slots: expected non-empty list, received {type(assigned_slots).__name__}"
        logger.error(error_msg)
        raise ValueError(error_msg)
    
    # Convert AssignedSlot objects to dictionaries if needed
    converted_slots = []
    for slot in assigned_slots:
        if hasattr(slot, 'to_dict') and callable(getattr(slot, 'to_dict')):
            # Convert object to dictionary
            converted_slots.append(slot.to_dict())
        else:
            # Already a dictionary
            converted_slots.append(slot)
    assigned_slots = converted_slots
    
    logger.debug(f"Converted {len(assigned_slots)} slots to dictionary format")
    
    # Validate each slot
    required_fields = ['outcome_id', 'outcome_text', 'bloom_level', 'question_type', 'points']
    for idx, slot in enumerate(assigned_slots):
        if not isinstance(slot, dict):
            error_msg = f"Slot {idx} is not a dictionary: {type(slot)}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        missing_fields = [f for f in required_fields if f not in slot]
        if missing_fields:
            error_msg = f"Slot {idx} missing fields: {missing_fields}"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        # Validate field values
        if not slot.get('outcome_text') or not str(slot.get('outcome_text')).strip():
            error_msg = f"Slot {idx}: outcome_text is empty"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if slot.get('bloom_level') not in ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']:
            error_msg = f"Slot {idx}: invalid bloom_level '{slot.get('bloom_level')}'"
            logger.error(error_msg)
            raise ValueError(error_msg)
        
        if not isinstance(slot.get('points'), (int, float)) or slot.get('points') <= 0:
            error_msg = f"Slot {idx}: points must be positive number, got {slot.get('points')}"
            logger.error(error_msg)
            raise ValueError(error_msg)
    
    logger.info(f"✓ All {len(assigned_slots)} slots validated successfully")
    
    # Log sample slots for debugging
    logger.info(f"Sample slots (first 3):")
    for idx, slot in enumerate(assigned_slots[:3]):
        logger.info(
            f"  Slot {idx}: outcome={str(slot.get('outcome_text', ''))[:40]}... "
            f"bloom={slot.get('bloom_level')} type={slot.get('question_type')} points={slot.get('points')}"
        )
    
    # =========================================================================
    # PHASE 1: GROUP SLOTS AND GENERATE QUESTIONS (using batch API calls)
    # =========================================================================
    
    logger.info("="*80)
    logger.info("PHASE 1: Batch Generation (reduced API calls)")
    logger.info("="*80)
    
    # Store expected count BEFORE generation - THIS IS CRITICAL FOR DEBUGGING
    expected_question_count = len(assigned_slots)
    logger.info(f"📊 EXPECTED QUESTIONS: {expected_question_count} (from {expected_question_count} slots)")
    logger.info(f"📊 EXPECTED TOTAL POINTS: {sum(s.get('points', 1) for s in assigned_slots)}")
    
    logger.info(f"Grouping {len(assigned_slots)} slots by characteristics...")
    
    # Group slots by (question_type, bloom_level, learning_outcome)
    groups = group_slots_by_characteristics(assigned_slots)
    
    logger.info(f"Created {len(groups)} groups for batch generation")
    logger.info(f"Expected API calls: {len(groups)} (reduction from {len(assigned_slots)} single calls)")
    
    # Generate questions for each group with RETRY LOGIC
    generated_questions = []
    failed_groups = []
    MAX_RETRIES = 2
    
    for group_num, (characteristics, batch_slots) in enumerate(groups.items(), 1):
        qtype, bloom, outcome = characteristics
        num_slots = len(batch_slots)
        
        logger.info(f"\n[Group {group_num}/{len(groups)}] {qtype} / {bloom} / {str(outcome)[:40]}...")
        logger.info(f"  Expected questions: {num_slots}")
        
        batch_questions = None
        last_error = None
        
        # Retry loop with exponential backoff
        for retry_attempt in range(MAX_RETRIES + 1):
            try:
                # Generate all questions in this batch with ONE API call
                batch_questions = generate_batch_questions(batch_slots, api_key)
                
                if not batch_questions:
                    last_error = "generate_batch_questions returned empty list"
                    logger.warning(f"  ⚠️  Attempt {retry_attempt + 1}/{MAX_RETRIES + 1}: Got 0 questions (expected {num_slots})")
                    if retry_attempt < MAX_RETRIES:
                        import time
                        wait_time = 2 ** retry_attempt
                        logger.info(f"  ⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    continue
                
                # CHECK: Verify we got the expected number of questions
                if len(batch_questions) != num_slots:
                    last_error = f"Expected {num_slots} questions, got {len(batch_questions)}"
                    logger.error(f"  ❌ Attempt {retry_attempt + 1}/{MAX_RETRIES + 1}: {last_error} - THIS IS A BUG!")
                    if retry_attempt < MAX_RETRIES:
                        import time
                        wait_time = 2 ** retry_attempt
                        logger.info(f"  ⏳ Waiting {wait_time}s before retry...")
                        time.sleep(wait_time)
                    continue
                
                # Success!
                logger.info(f"  ✓ Generated {len(batch_questions)} questions")
                generated_questions.extend(batch_questions)
                break
            
            except Exception as e:
                error_msg = f"{type(e).__name__}: {str(e)}"
                last_error = error_msg
                logger.warning(f"  ⚠️  Attempt {retry_attempt + 1}/{MAX_RETRIES + 1}: {error_msg}")
                if retry_attempt < MAX_RETRIES:
                    import time
                    wait_time = 2 ** retry_attempt
                    logger.info(f"  ⏳ Waiting {wait_time}s before retry...")
                    time.sleep(wait_time)
                if DEVELOPMENT_MODE:
                    logger.exception("Full traceback:")
        
        # After all retries, check if batch succeeded
        if batch_questions is None or len(batch_questions) != num_slots:
            failed_groups.append((characteristics, batch_slots, last_error))
            logger.error(f"  ✗ BATCH FAILED after {MAX_RETRIES + 1} attempts")
    
    # Convert failed_groups to failed_slots format for compatibility
    failed_slots = []
    for characteristics, batch_slots, error_msg in failed_groups:
        for slot_idx, slot in enumerate(batch_slots, 1):
            failed_slots.append((slot_idx, slot, error_msg))
    
    # Report generation results
    logger.info(f"\n" + "="*80)
    logger.info(f"GENERATION RESULTS (after all retries):")
    logger.info(f"="*80)
    logger.info(f"  Expected: {expected_question_count} questions")
    logger.info(f"  Generated: {len(generated_questions)} questions")
    logger.info(f"  Missing: {expected_question_count - len(generated_questions)} questions")
    logger.info(f"  Failed batches: {len(failed_groups)}")
    
    if len(generated_questions) != expected_question_count:
        logger.error(f"\n🔥 WARNING: Question count MISMATCH!")
        logger.error(f"   Expected: {expected_question_count}")
        logger.error(f"   Got: {len(generated_questions)}")
        logger.error(f"   Missing: {expected_question_count - len(generated_questions)}")
    
    if failed_slots:
        logger.error(f"\n❌ CRITICAL: {len(failed_slots)} questions were NOT generated:")
        for slot_idx, slot, error in failed_slots[:10]:
            outcome_text = str(slot.get('outcome_text', 'N/A'))[:40]
            logger.error(
                f"  - Slot {slot_idx}: {slot.get('question_type')} / {slot.get('bloom_level')} / {outcome_text}... ({error})"
            )
        
        if len(failed_slots) > 10:
            logger.error(f"  ... and {len(failed_slots) - 10} more missing questions")
        
        # Only fail completely if no questions were generated
        if len(generated_questions) == 0:
            error_msg = f"Failed to generate any questions. First error: {failed_slots[0][2] if failed_slots else 'Unknown'}"
            logger.error(error_msg)
            raise RuntimeError(error_msg)
        
        logger.warning(f"\n⚠️  WARNING: Continuing with {len(generated_questions)}/{expected_question_count} questions (INCOMPLETE!)")
    
    # =========================================================================
    # PHASE 2: SHUFFLE (optional)
    # =========================================================================
    if shuffle:
        logger.info("Shuffling questions...")
        random.shuffle(generated_questions)
    
    # =========================================================================
    # PHASE 3: REASSIGN QUESTION_NUMBER SEQUENTIALLY
    # =========================================================================
    logger.info("Assigning sequential question numbers...")
    for idx, question in enumerate(generated_questions, 1):
        question["question_number"] = idx
    
    # =========================================================================
    # PHASE 4: VERIFICATION & SAFETY CHECKS (CRITICAL)
    # =========================================================================
    logger.info(f"\n" + "="*80)
    logger.info("PHASE 4: FINAL VERIFICATION & SAFETY CHECKS")
    logger.info(f"="*80)
    
    # CRITICAL SAFETY CHECK #1: Question count must match
    logger.info(f"Checking question count: {len(generated_questions)} vs expected {expected_question_count}")
    
    count_mismatch = len(generated_questions) != expected_question_count
    if count_mismatch:
        missing_count = expected_question_count - len(generated_questions)
        logger.error(f"\n🔥 CRITICAL MISMATCH DETECTED!")
        logger.error(f"   Expected: {expected_question_count} questions")
        logger.error(f"   Generated: {len(generated_questions)} questions")
        logger.error(f"   MISSING: {missing_count} questions")
        logger.error(f"\nThis indicates {missing_count} questions were lost during generation.")
    else:
        logger.info(f"✓ Question count matches: {len(generated_questions)} == {expected_question_count}")
    
    # CRITICAL SAFETY CHECK #2: Total points must match
    expected_total_points = sum(s.get('points', 1) for s in assigned_slots)
    actual_total_points = sum(q.get('points', 1) for q in generated_questions)
    logger.info(f"Checking total points: {actual_total_points} vs expected {expected_total_points}")
    
    points_mismatch = actual_total_points != expected_total_points
    if points_mismatch:
        logger.warning(f"Points mismatch: expected {expected_total_points}, got {actual_total_points}")
    else:
        logger.info(f"✓ Total points matches: {actual_total_points} == {expected_total_points}")
    
    # Verify sequential numbering
    question_numbers = [q["question_number"] for q in generated_questions]
    expected_numbers = list(range(1, len(generated_questions) + 1))
    if question_numbers != expected_numbers:
        logger.error("Questions are NOT numbered sequentially!")
    else:
        logger.info(f"✓ Questions numbered sequentially: 1-{len(generated_questions)}")
    
    # Log validation summary
    logger.info(f"\n" + "-"*80)
    logger.info(f"FINAL VERIFICATION SUMMARY:")
    logger.info(f"-"*80)
    logger.info(f"  Questions: {len(generated_questions)}/{expected_question_count} ({'✓ MATCH' if not count_mismatch else f'✗ MISMATCH ({missing_count} missing)'})")
    logger.info(f"  Total Points: {actual_total_points}/{expected_total_points} ({'✓ MATCH' if not points_mismatch else '✗ MISMATCH'})")
    logger.info(f"  Question types: {len(set(q.get('question_type') for q in generated_questions))} types")
    logger.info(f"  Bloom levels: {len(set(q.get('bloom_level') for q in generated_questions))} levels")
    logger.info(f"-"*80)
    
    # Validate all required fields are present
    logger.info("Validating all questions have required metadata...")
    
    # ===== SAFETY ASSERTION: Guarantee counts match =====
    if len(generated_questions) != expected_question_count:
        missing = expected_question_count - len(generated_questions)
        error_msg = (
            f"\n🔥 ASSERTION FAILED: Question count mismatch!\n"
            f"Expected: {expected_question_count} questions\n"
            f"Got: {len(generated_questions)} questions\n"
            f"Missing: {missing} questions\n\n"
            f"This is a CRITICAL data integrity issue. The TQS is incomplete.\n"
            f"See application logs above for details about which batches failed.\n"
        )
        logger.error(error_msg)
        raise AssertionError(
            f"Generated {len(generated_questions)} questions but expected {expected_question_count}. "
            f"Missing {missing} questions. This indicates a generation failure. "
            f"Review logs for details."
        )
    
    logger.info(f"✓ ASSERTION PASSED: Generated {expected_question_count} questions as expected")
    
    try:
        validate_tqs_before_stats(generated_questions)
    except ValueError as e:
        logger.error(f"Validation failed: {e}")
        raise RuntimeError(f"Generated questions invalid: {e}")
    
    # Calculate statistics
    total_points = sum(q.get("points", 0) for q in generated_questions)
    logger.info(f"\n{'='*60}")
    logger.info(f"TQS GENERATION COMPLETE")
    logger.info(f"{'='*60}")
    logger.info(f"Total questions: {len(generated_questions)}")
    logger.info(f"Total points: {total_points}")
    if failed_slots:
        logger.info(f"Failed slots: {len(failed_slots)} (recovered with partial TQS)")
    logger.info(f"{'='*60}\n")
    
    return generated_questions


def validate_question_fields(question: Dict[str, Any]) -> Tuple[bool, str]:
    """
    Validate that a question has all required metadata fields.
    
    Do NOT rely on AI to provide structural metadata. All required fields
    must come from the assigned slot.
    
    Args:
        question: The question dictionary to validate
    
    Returns:
        Tuple of (is_valid, error_message)
    """
    required_fields = {
        "question_number": "Question number",
        "question_text": "Question text",
        "type": "Question type",
        "bloom": "Bloom level",
        "learning_outcome": "Learning outcome",
        "points": "Points value",
        "outcome_id": "Outcome ID"
    }
    
    missing_fields = []
    for field, display_name in required_fields.items():
        if field not in question:
            missing_fields.append(f"{display_name} ({field})")
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    # Validate field values
    if not question.get("question_text"):
        return False, "Question text is empty"
    
    if not question.get("type"):
        return False, "Question type is empty"
    
    if question.get("points", 0) <= 0:
        return False, f"Invalid points value: {question.get('points')}"
    
    return True, ""


def validate_tqs_before_stats(tqs: List[Dict[str, Any]]) -> bool:
    """
    Validate all questions have required fields before calculating statistics.
    
    Args:
        tqs: List of test questions
    
    Returns:
        True if all questions valid
    
    Raises:
        ValueError: If any question has missing fields
    """
    for idx, question in enumerate(tqs):
        is_valid, error_msg = validate_question_fields(question)
        if not is_valid:
            error_str = f"Question {idx + 1}: {error_msg}"
            logger.error(error_str)
            raise ValueError(error_str)
    
    logger.info(f"✓ All {len(tqs)} questions validated successfully")
    return True


def get_tqs_statistics(tqs: List[Dict[str, Any]]) -> Dict[str, Any]:
    """
    Generate statistics about the Test Question Sheet.
    
    Args:
        tqs: List of test questions
    
    Returns:
        Dictionary containing:
        - total_questions: Count of questions
        - total_points: Sum of all points
        - questions_by_type: Count per question type
        - points_by_type: Total points per type
        - questions_by_bloom: Count per Bloom level
        - points_by_bloom: Total points per Bloom level
    """
    
    stats = {
        "total_questions": len(tqs),
        "total_points": sum(q.get("points", 0) for q in tqs),
        "questions_by_type": {},
        "points_by_type": {},
        "questions_by_bloom": {},
        "points_by_bloom": {}
    }
    
    for question in tqs:
        qtype = question.get("type", "Unknown")
        bloom = question.get("bloom", "Unknown")
        points = question.get("points", 0)
        
        # By type
        stats["questions_by_type"][qtype] = stats["questions_by_type"].get(qtype, 0) + 1
        stats["points_by_type"][qtype] = stats["points_by_type"].get(qtype, 0) + points
        
        # By Bloom
        stats["questions_by_bloom"][bloom] = stats["questions_by_bloom"].get(bloom, 0) + 1
        stats["points_by_bloom"][bloom] = stats["points_by_bloom"].get(bloom, 0) + points
    
    return stats


def export_tqs_to_json(tqs: List[Dict[str, Any]], filename: str = "tqs_export.json") -> str:
    """
    Export TQS to JSON file.
    
    Args:
        tqs: List of test questions
        filename: Output filename
    
    Returns:
        Path to exported file
    """
    
    try:
        with open(filename, 'w') as f:
            json.dump(tqs, f, indent=2)
        logger.info(f"TQS exported to {filename}")
        return filename
    except Exception as e:
        logger.error(f"Failed to export TQS: {e}")
        return ""


def display_tqs_preview(tqs: List[Dict[str, Any]], max_questions: int = 3) -> None:
    """
    Display a preview of TQS questions (for debugging).
    
    Args:
        tqs: List of test questions
        max_questions: Maximum number to display
    """
    
    print("\n" + "="*80)
    print("TQS PREVIEW")
    print("="*80)
    
    for q in tqs[:max_questions]:
        print(f"\nQ{q.get('question_number', '?')}: {q.get('type', 'Unknown')} ({q.get('points', 0)} pts)")
        print(f"  Outcome: {q.get('outcome', '')[:60]}...")
        print(f"  Bloom: {q.get('bloom', 'Unknown')}")
        print(f"  Text: {q.get('question_text', '')[:80]}...")
        
        if q.get('type') == 'MCQ':
            print(f"  Choices: {len(q.get('choices', []))} options")
            print(f"  Answer: {q.get('correct_answer', '?')}")
        
        elif q.get('type') == 'Short Answer':
            key_preview = q.get('answer_key', '')[:50]
            print(f"  Key: {key_preview}...")
        
        else:
            sample_preview = q.get('sample_answer', '')[:50]
            print(f"  Sample: {sample_preview}...")
            if q.get('rubric'):
                criteria_count = len(q['rubric'].get('criteria', []))
                print(f"  Rubric: {criteria_count} criteria, {q['rubric'].get('total_points', 0)} pts")
    
    print("\n" + "="*80)
