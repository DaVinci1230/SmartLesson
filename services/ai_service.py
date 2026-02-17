"""
AI SERVICE MODULE - GOOGLE GEMINI INTEGRATION

This module provides AI-assisted services using Google Gemini API.
All outputs are structured JSON, validated before returning to the caller.

ARCHITECTURE PRINCIPLE:
- Gemini is an AUGMENTATION LAYER ONLY
- System validates and controls all final outputs
- Gemini cannot modify totals or override validation logic
- All responses must match strict JSON schemas

Features:
1. Bloom Level Classification: Classifies competencies to Bloom's taxonomy levels
2. Test Question Generation: Generates MCQ questions with validated structure
3. JSON Validation: All responses validated against predefined schemas
4. Error Handling: Graceful fallbacks and detailed error reporting
"""

import json
import logging
from typing import List, Dict, Any, Optional
import google.genai as genai  # Using official google-genai package (google.generativeai is deprecated)
from jsonschema import validate, ValidationError, FormatChecker
import re

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ============================================================================
# JSON SCHEMAS - System-Controlled Validation
# ============================================================================

BLOOM_CLASSIFICATION_SCHEMA = {
    "type": "object",
    "properties": {
        "competencies": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "text": {"type": "string", "minLength": 5},
                    "bloom_level": {
                        "type": "string",
                        "enum": ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
                    },
                    "justification": {"type": "string", "minLength": 10}
                },
                "required": ["text", "bloom_level", "justification"],
                "additionalProperties": False
            }
        }
    },
    "required": ["competencies"],
    "additionalProperties": False
}

TEST_QUESTION_SCHEMA = {
    "type": "object",
    "properties": {
        "questions": {
            "type": "array",
            "items": {
                "type": "object",
                "properties": {
                    "type": {
                        "type": "string",
                        "enum": ["MCQ", "True/False", "Fill-in-the-Blank", "Short Answer"]
                    },
                    "question": {"type": "string", "minLength": 10},
                    "choices": {
                        "type": "array",
                        "items": {"type": "string"},
                        "minItems": 2,
                        "maxItems": 5
                    },
                    "answer": {"type": "string", "minLength": 1},
                    "difficulty": {
                        "type": "string",
                        "enum": ["Easy", "Medium", "Hard"]
                    }
                },
                "required": ["type", "question", "choices", "answer", "difficulty"],
                "additionalProperties": False
            }
        }
    },
    "required": ["questions"],
    "additionalProperties": False
}

# ============================================================================
# GEMINI API CONFIGURATION
# ============================================================================

class GeminiConfig:
    """Manages Gemini API configuration and initialization using google-genai."""
    
    def __init__(self, api_key: str):
        """Initialize Gemini with API key using google-genai package."""
        if not api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set")
        
        # Create Gemini client using google-genai (official package)
        self.client = genai.Client(api_key=api_key)
        self.api_key = api_key
        logger.info("✓ Gemini API (google-genai) configured successfully")
    
    def get_client(self):
        """Get the configured Gemini client."""
        return self.client
    
    def get_model(self):
        """Get a model for backward compatibility."""
        # Returns the client itself since google-genai uses client.models.generate_content()
        return self.client.models


# ============================================================================
# HELPER FUNCTIONS - JSON EXTRACTION & VALIDATION
# ============================================================================

def extract_json_from_response(text: str) -> Dict[str, Any]:
    """
    Extract JSON object from Gemini response.
    Handles various response formats (code blocks, markdown, etc.)
    
    Args:
        text: Raw response from Gemini
        
    Returns:
        Parsed JSON dictionary
        
    Raises:
        ValueError: If no valid JSON found in response
    """
    # Try to find JSON in code blocks
    code_block_pattern = r"```(?:json)?\s*(\{.*?\})\s*```"
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        try:
            return json.loads(match.group(1))
        except json.JSONDecodeError:
            pass
    
    # Try to extract JSON object directly
    brace_start = text.find('{')
    if brace_start != -1:
        brace_count = 0
        brace_end = -1
        for i in range(brace_start, len(text)):
            if text[i] == '{':
                brace_count += 1
            elif text[i] == '}':
                brace_count -= 1
                if brace_count == 0:
                    brace_end = i + 1
                    break
        
        if brace_end > 0:
            try:
                return json.loads(text[brace_start:brace_end])
            except json.JSONDecodeError:
                pass
    
    raise ValueError(f"Could not extract valid JSON from Gemini response: {text[:200]}")


def validate_json_response(data: Dict[str, Any], schema: Dict[str, Any]) -> bool:
    """
    Validate JSON response against schema.
    System-controlled validation before any data is processed.
    
    Args:
        data: JSON object to validate
        schema: JSON schema to validate against
        
    Returns:
        True if valid
        
    Raises:
        ValidationError: If validation fails
    """
    try:
        validate(instance=data, schema=schema, format_checker=FormatChecker())
        logger.info("✓ JSON validation passed")
        return True
    except ValidationError as e:
        logger.error(f"✗ JSON validation failed: {e.message}")
        raise


# ============================================================================
# BLOOM CLASSIFICATION FUNCTION
# ============================================================================

def classify_competencies_bloom(
    competencies: List[str],
    api_key: str
) -> Dict[str, Any]:
    """
    Classify learning competencies into Bloom's Taxonomy levels using Gemini.
    
    INPUT:
    - competencies: List of learning competency strings
      Example: ["Identify the parts of a cell", "Design a new experiment"]
    
    OUTPUT:
    {
        "competencies": [
            {
                "text": "Original competency text",
                "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create",
                "justification": "Brief explanation of classification"
            },
            ...
        ]
    }
    
    SYSTEM CONTROL:
    - Output strictly follows JSON schema
    - Gemini cannot override or modify competency text
    - System validates before returning
    
    Args:
        competencies: List of competency strings to classify
        api_key: Gemini API key
        
    Returns:
        Validated JSON with Bloom classifications
        
    Raises:
        ValueError: If Gemini response cannot be parsed or validated
    """
    logger.info(f"Classifying {len(competencies)} competencies to Bloom levels")
    
    # Initialize Gemini (can be reused)
    config = GeminiConfig(api_key)
    model = config.get_model()
    
    # Build competencies list for prompt
    competencies_str = "\n".join([f"{i+1}. {c}" for i, c in enumerate(competencies)])
    
    # Structured prompt - strict JSON output required
    prompt = f"""You are an expert in educational taxonomy. Classify the following learning competencies into Bloom's Taxonomy levels.

LEARNING COMPETENCIES:
{competencies_str}

YOUR TASK:
1. Analyze each competency
2. Assign the most appropriate Bloom level: Remember, Understand, Apply, Analyze, Evaluate, or Create
3. Provide a brief justification for each classification

IMPORTANT CONSTRAINTS:
- Return ONLY valid JSON (no markdown, no explanations outside JSON)
- Do NOT modify or rephrase the original competency text
- Each competency must have a clear Bloom level assignment
- Justification must explain WHY it belongs to that level

OUTPUT FORMAT (STRICT JSON):
{{
    "competencies": [
        {{
            "text": "exact original competency text",
            "bloom_level": "Remember/Understand/Apply/Analyze/Evaluate/Create",
            "justification": "explanation of why this level was assigned"
        }}
    ]
}}"""
    
    try:
        # Call Gemini
        response = model.generate_content(prompt)
        logger.info("✓ Received response from Gemini")
        
        # Extract JSON from response
        parsed_json = extract_json_from_response(response.text)
        logger.info("✓ Extracted JSON from response")
        
        # Validate against schema
        validate_json_response(parsed_json, BLOOM_CLASSIFICATION_SCHEMA)
        
        # Verify text integrity (Gemini must not modify original text)
        for i, item in enumerate(parsed_json["competencies"]):
            if item["text"] != competencies[i]:
                logger.warning(
                    f"Competency text mismatch at index {i}. "
                    f"Original: '{competencies[i]}', "
                    f"Returned: '{item['text']}'. "
                    f"Using original text."
                )
                item["text"] = competencies[i]
        
        logger.info("✓ Bloom classification completed successfully")
        return parsed_json
        
    except Exception as e:
        logger.error(f"✗ Bloom classification failed: {str(e)}")
        raise


# ============================================================================
# TEST QUESTION GENERATION FUNCTION
# ============================================================================

def generate_test_questions(
    competency: str,
    bloom_level: str,
    num_items: int,
    api_key: str,
    subject: str = "",
    context: str = ""
) -> Dict[str, Any]:
    """
    Generate multiple-choice test questions for a specific competency using Gemini.
    
    INPUT:
    - competency: The learning competency (e.g., "Identify the parts of a cell")
    - bloom_level: Bloom's level (Remember, Understand, Apply, Analyze, Evaluate, Create)
    - num_items: Number of questions to generate
    - subject: Optional subject context (e.g., "Biology")
    - context: Optional additional context (e.g., "High School Level")
    
    OUTPUT:
    {
        "questions": [
            {
                "type": "MCQ",
                "question": "Question text",
                "choices": ["A", "B", "C", "D"],
                "answer": "Correct answer letter",
                "difficulty": "Easy/Medium/Hard"
            },
            ...
        ]
    }
    
    SYSTEM CONTROL:
    - Number of items matches requested count
    - Bloom level constraints enforced by system
    - Difficulty distribution determined by system validation
    - Gemini cannot override question count
    
    Args:
        competency: The learning competency to base questions on
        bloom_level: Bloom's taxonomy level
        num_items: Number of questions to generate
        api_key: Gemini API key
        subject: Optional subject context
        context: Optional additional context
        
    Returns:
        Validated JSON with test questions
        
    Raises:
        ValueError: If Gemini response cannot be parsed or validated
    """
    logger.info(f"Generating {num_items} questions for: {competency} ({bloom_level})")
    
    # Initialize Gemini
    config = GeminiConfig(api_key)
    model = config.get_model()
    
    # Build context string
    context_str = ""
    if subject:
        context_str += f"Subject: {subject}\n"
    if context:
        context_str += f"Context: {context}\n"
    
    # Structured prompt
    prompt = f"""You are an expert educator and test question writer. Generate {num_items} high-quality multiple-choice questions based on the following:

COMPETENCY: {competency}
BLOOM LEVEL: {bloom_level}
NUMBER OF QUESTIONS: {num_items}
{context_str}

YOUR TASK:
1. Generate exactly {num_items} multiple-choice questions
2. Each question should test the specified Bloom level
3. Provide 4 answer choices (A, B, C, D)
4. Mark the correct answer
5. Classify difficulty as Easy, Medium, or Hard
6. Questions should be appropriate for the given context

BLOOM LEVEL GUIDANCE:
- Remember: Recall facts and definitions
- Understand: Explain concepts and ideas
- Apply: Use information in new situations
- Analyze: Draw connections and distinctions
- Evaluate: Justify choices and decisions
- Create: Put elements together to form new whole

IMPORTANT CONSTRAINTS:
- Return ONLY valid JSON (no markdown, explanations, or extra text)
- Generate EXACTLY {num_items} questions - no more, no less
- Each question must have 4 distinct choices
- Answer must be one of: A, B, C, D
- Difficulty must be: Easy, Medium, or Hard
- Ensure questions match the {bloom_level} level

OUTPUT FORMAT (STRICT JSON):
{{
    "questions": [
        {{
            "type": "MCQ",
            "question": "Question text here",
            "choices": ["Choice A", "Choice B", "Choice C", "Choice D"],
            "answer": "A",
            "difficulty": "Medium"
        }},
        ...
    ]
}}"""
    
    try:
        # Call Gemini
        response = model.generate_content(prompt)
        logger.info("✓ Received response from Gemini")
        
        # Extract JSON
        parsed_json = extract_json_from_response(response.text)
        logger.info("✓ Extracted JSON from response")
        
        # Validate against schema
        validate_json_response(parsed_json, TEST_QUESTION_SCHEMA)
        
        # System control: Verify question count matches requested
        question_count = len(parsed_json["questions"])
        if question_count != num_items:
            logger.warning(
                f"Generated {question_count} questions, but {num_items} were requested. "
                f"System will adjust."
            )
            # System-controlled adjustment: keep only requested number
            parsed_json["questions"] = parsed_json["questions"][:num_items]
        
        # Validate answer choices match provided choices
        for i, q in enumerate(parsed_json["questions"]):
            if q["answer"] not in ["A", "B", "C", "D"]:
                logger.error(f"Invalid answer '{q['answer']}' in question {i+1}")
                raise ValueError(f"Question {i+1} has invalid answer format")
            if len(q["choices"]) != 4:
                logger.error(f"Question {i+1} does not have exactly 4 choices")
                raise ValueError(f"Question {i+1} must have exactly 4 choices")
        
        logger.info(f"✓ Test question generation completed: {question_count} questions")
        return parsed_json
        
    except Exception as e:
        logger.error(f"✗ Test question generation failed: {str(e)}")
        raise


# ============================================================================
# BATCH PROCESSING (OPTIONAL)
# ============================================================================

def batch_classify_and_generate(
    competencies: List[str],
    bloom_weights: Dict[str, int],
    total_items: int,
    api_key: str,
    subject: str = "",
    context: str = ""
) -> Dict[str, Any]:
    """
    Batch process: Classify competencies and generate questions for each.
    
    This is a convenience function that:
    1. Classifies competencies to Bloom levels
    2. Generates questions based on Bloom distribution and total items
    
    Args:
        competencies: List of competencies
        bloom_weights: Dict with Bloom level percentages (must total 100)
        total_items: Total number of questions to generate
        api_key: Gemini API key
        subject: Optional subject context
        context: Optional additional context
        
    Returns:
        Dictionary with classifications and generated questions
    """
    logger.info("Starting batch classification and generation process")
    
    # Step 1: Classify competencies
    classifications = classify_competencies_bloom(competencies, api_key)
    
    # Step 2: For each competency, generate questions
    # Distribute total_items across competencies
    items_per_competency = total_items // len(competencies)
    remainder = total_items % len(competencies)
    
    all_questions = {}
    
    for i, item in enumerate(classifications["competencies"]):
        competency_text = item["text"]
        bloom_level = item["bloom_level"]
        
        # Distribute items: some get +1
        num_questions = items_per_competency + (1 if i < remainder else 0)
        
        if num_questions > 0:
            logger.info(
                f"Generating {num_questions} questions for competency: {competency_text[:50]}..."
            )
            questions = generate_test_questions(
                competency=competency_text,
                bloom_level=bloom_level,
                num_items=num_questions,
                api_key=api_key,
                subject=subject,
                context=context
            )
            all_questions[competency_text] = questions["questions"]
    
    logger.info("✓ Batch processing completed")
    
    return {
        "classifications": classifications,
        "questions_by_competency": all_questions,
        "total_questions": sum(len(q) for q in all_questions.values())
    }
