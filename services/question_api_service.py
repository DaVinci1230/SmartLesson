"""
Question API Service Module

This module provides API-ready functions for CRUD operations on test questions.
Currently works with session state but designed to be easily adapted for database storage.

Future: Can be converted to FastAPI/Flask endpoints for true REST API.
"""

import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
from services.tqs_service import generate_question_with_gemini, get_tqs_statistics

logger = logging.getLogger(__name__)


class QuestionAPIService:
    """
    Service class for managing test questions.
    
    This is designed to work with session state now but can be easily
    adapted to work with a database by changing the storage backend.
    """
    
    def __init__(self, storage_backend='session_state'):
        """
        Initialize the question API service.
        
        Args:
            storage_backend: 'session_state' or 'database' (future)
        """
        self.storage_backend = storage_backend
    
    def get_all_questions(self, session_state) -> List[Dict[str, Any]]:
        """
        Retrieve all questions from storage.
        
        Args:
            session_state: Streamlit session state object
        
        Returns:
            List of question dictionaries
        """
        if self.storage_backend == 'session_state':
            return session_state.get('generated_tqs', [])
        # Future: Add database query here
        return []
    
    def get_question_by_id(self, question_id: int, session_state) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single question by ID.
        
        Args:
            question_id: Question number/ID
            session_state: Streamlit session state object
        
        Returns:
            Question dictionary or None if not found
        """
        questions = self.get_all_questions(session_state)
        for q in questions:
            if q.get('question_number') == question_id:
                return q
        return None
    
    def get_question_by_index(self, index: int, session_state) -> Optional[Dict[str, Any]]:
        """
        Retrieve a single question by array index.
        
        Args:
            index: Array index (0-based)
            session_state: Streamlit session state object
        
        Returns:
            Question dictionary or None if not found
        """
        questions = self.get_all_questions(session_state)
        if 0 <= index < len(questions):
            return questions[index]
        return None
    
    def create_question(self, question_data: Dict[str, Any], session_state) -> bool:
        """
        Create a new question.
        
        Args:
            question_data: Dictionary containing question fields
            session_state: Streamlit session state object
        
        Returns:
            True if successful, False otherwise
        """
        if self.storage_backend == 'session_state':
            questions = self.get_all_questions(session_state)
            
            # Assign question number
            if questions:
                question_data['question_number'] = max(q['question_number'] for q in questions) + 1
            else:
                question_data['question_number'] = 1
            
            # Add timestamp
            question_data['created_at'] = datetime.now().isoformat()
            question_data['updated_at'] = datetime.now().isoformat()
            
            questions.append(question_data)
            session_state.generated_tqs = questions
            
            # Recalculate statistics
            session_state.tqs_stats = get_tqs_statistics(questions)
            return True
        
        # Future: Add database insert here
        return False
    
    def update_question(self, question_index: int, updated_data: Dict[str, Any], session_state) -> bool:
        """
        Update an existing question by index.
        
        Args:
            question_index: Array index (0-based)
            updated_data: Dictionary with fields to update
            session_state: Streamlit session state object
        
        Returns:
            True if successful, False otherwise
        """
        if self.storage_backend == 'session_state':
            questions = self.get_all_questions(session_state)
            
            if 0 <= question_index < len(questions):
                # Add update timestamp
                updated_data['updated_at'] = datetime.now().isoformat()
                
                # Update question
                questions[question_index].update(updated_data)
                session_state.generated_tqs = questions
                
                # Recalculate statistics
                session_state.tqs_stats = get_tqs_statistics(questions)
                
                logger.info(f"Updated question at index {question_index}")
                return True
            else:
                logger.error(f"Question index {question_index} out of range")
                return False
        
        # Future: Add database update here
        return False
    
    def delete_question(self, question_index: int, session_state) -> bool:
        """
        Delete a question by index.
        
        Args:
            question_index: Array index (0-based)
            session_state: Streamlit session state object
        
        Returns:
            True if successful, False otherwise
        """
        if self.storage_backend == 'session_state':
            questions = self.get_all_questions(session_state)
            
            if 0 <= question_index < len(questions):
                # Remove question
                deleted_q = questions.pop(question_index)
                
                # Renumber remaining questions
                for i, q in enumerate(questions):
                    q['question_number'] = i + 1
                
                session_state.generated_tqs = questions
                
                # Recalculate statistics
                session_state.tqs_stats = get_tqs_statistics(questions)
                
                logger.info(f"Deleted question {deleted_q.get('question_number', 'N/A')}")
                return True
            else:
                logger.error(f"Question index {question_index} out of range")
                return False
        
        # Future: Add database delete here
        return False
    
    def regenerate_question(self, question_index: int, api_key: str, session_state) -> bool:
        """
        Regenerate a question using AI.
        
        Args:
            question_index: Array index (0-based)
            api_key: Gemini API key
            session_state: Streamlit session state object
        
        Returns:
            True if successful, False otherwise
        """
        questions = self.get_all_questions(session_state)
        
        if 0 <= question_index < len(questions):
            old_question = questions[question_index]
            
            # Create a slot from the existing question
            slot = {
                "outcome_id": old_question.get("outcome_id", 0),
                "outcome_text": old_question.get("outcome_text", old_question.get("learning_outcome", "")),
                "bloom_level": old_question.get("bloom_level", old_question.get("bloom", "Remember")),
                "question_type": old_question.get("question_type", old_question.get("type", "MCQ")),
                "points": old_question.get("points", 1)
            }
            
            # Generate new question
            logger.info(f"Regenerating question at index {question_index}")
            new_question = generate_question_with_gemini(slot, api_key)
            
            if new_question:
                # Preserve metadata
                new_question['question_number'] = old_question['question_number']
                new_question['created_at'] = old_question.get('created_at', datetime.now().isoformat())
                new_question['updated_at'] = datetime.now().isoformat()
                new_question['regenerated'] = True
                
                questions[question_index] = new_question
                session_state.generated_tqs = questions
                
                # Recalculate statistics
                session_state.tqs_stats = get_tqs_statistics(questions)
                
                logger.info(f"Successfully regenerated question {new_question['question_number']}")
                return True
            else:
                logger.error(f"Failed to generate new question for index {question_index}")
                return False
        else:
            logger.error(f"Question index {question_index} out of range")
            return False
    
    def bulk_update_questions(self, updates: List[Dict[str, Any]], session_state) -> Dict[str, Any]:
        """
        Update multiple questions in one operation.
        
        Args:
            updates: List of dicts with 'index' and 'data' keys
            session_state: Streamlit session state object
        
        Returns:
            Dictionary with success count and errors
        """
        results = {
            'success_count': 0,
            'error_count': 0,
            'errors': []
        }
        
        for update in updates:
            index = update.get('index')
            data = update.get('data')
            
            if index is not None and data:
                if self.update_question(index, data, session_state):
                    results['success_count'] += 1
                else:
                    results['error_count'] += 1
                    results['errors'].append(f"Failed to update question at index {index}")
            else:
                results['error_count'] += 1
                results['errors'].append(f"Invalid update data: {update}")
        
        return results
    
    def update_question_validated(
        self, 
        question_index: int, 
        update_data: Dict[str, Any], 
        session_state
    ) -> Dict[str, Any]:
        """
        Update a single question with validation.
        
        This is the recommended method for API endpoints as it includes
        comprehensive validation and returns detailed results.
        
        Args:
            question_index: Array index (0-based)
            update_data: Dictionary with fields to update
            session_state: Streamlit session state object
        
        Expected update_data fields:
            - question_text: str (optional)
            - choices: List[str] (optional, MCQ only, must have 4 items)
            - correct_answer: str (optional, MCQ only, must be A/B/C/D)
            - bloom_level: str (optional, must be valid Bloom level)
            - points: float (optional, must be > 0)
            - answer_key: str (optional, Short Answer only)
            - sample_answer: str (optional, Essay/Problem/Drawing only)
        
        Returns:
            Dictionary with:
                - success: bool
                - message: str
                - data: Dict (updated question) or None
                - errors: List[str]
        """
        result = {
            'success': False,
            'message': '',
            'data': None,
            'errors': []
        }
        
        # Get current question
        questions = self.get_all_questions(session_state)
        
        if question_index < 0 or question_index >= len(questions):
            result['message'] = f'Question index {question_index} out of range'
            result['errors'].append('Invalid question index')
            return result
        
        current_question = questions[question_index]
        question_type = current_question.get('type', current_question.get('question_type', 'MCQ'))
        
        # Validation
        valid_bloom_levels = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
        
        # Validate bloom_level if provided
        if 'bloom_level' in update_data:
            if update_data['bloom_level'] not in valid_bloom_levels:
                result['errors'].append(
                    f"Invalid bloom_level: {update_data['bloom_level']}. "
                    f"Must be one of: {', '.join(valid_bloom_levels)}"
                )
        
        # Validate points if provided
        if 'points' in update_data:
            try:
                points = float(update_data['points'])
                if points <= 0:
                    result['errors'].append('Points must be greater than 0')
                elif points > 100:
                    result['errors'].append('Points cannot exceed 100')
            except (ValueError, TypeError):
                result['errors'].append('Points must be a valid number')
        
        # MCQ-specific validation
        if question_type == 'MCQ':
            # Validate choices if provided
            if 'choices' in update_data:
                choices = update_data['choices']
                if not isinstance(choices, list):
                    result['errors'].append('Choices must be a list')
                elif len(choices) != 4:
                    result['errors'].append('MCQ must have exactly 4 choices')
                elif any(not choice or not str(choice).strip() for choice in choices):
                    result['errors'].append('All choices must be non-empty strings')
            
            # Validate correct_answer if provided
            if 'correct_answer' in update_data:
                answer = update_data['correct_answer']
                if answer not in ['A', 'B', 'C', 'D']:
                    result['errors'].append(
                        f"Invalid correct_answer: {answer}. Must be A, B, C, or D"
                    )
                
                # If choices are being updated, verify answer is valid for new choices
                if 'choices' in update_data:
                    choices = update_data['choices']
                    answer_index = ord(answer) - ord('A')
                    if answer_index >= len(choices):
                        result['errors'].append(
                            f"Correct answer {answer} is out of range for provided choices"
                        )
        
        # If there are validation errors, return early
        if result['errors']:
            result['message'] = 'Validation failed'
            return result
        
        # Prepare clean update data (only modified fields)
        clean_update = {}
        
        # Only include fields that are actually being changed
        if 'question_text' in update_data:
            clean_update['question_text'] = str(update_data['question_text']).strip()
        
        if 'bloom_level' in update_data:
            clean_update['bloom'] = update_data['bloom_level']
            clean_update['bloom_level'] = update_data['bloom_level']
        
        if 'points' in update_data:
            clean_update['points'] = float(update_data['points'])
        
        # Type-specific updates
        if question_type == 'MCQ':
            if 'choices' in update_data:
                clean_update['choices'] = [str(c).strip() for c in update_data['choices']]
            if 'correct_answer' in update_data:
                clean_update['correct_answer'] = update_data['correct_answer']
        
        elif question_type == 'Short Answer':
            if 'answer_key' in update_data:
                clean_update['answer_key'] = str(update_data['answer_key']).strip()
        
        else:  # Essay, Problem Solving, Drawing
            if 'sample_answer' in update_data:
                clean_update['sample_answer'] = str(update_data['sample_answer']).strip()
        
        # Perform update
        if self.update_question(question_index, clean_update, session_state):
            updated_question = self.get_question_by_index(question_index, session_state)
            result['success'] = True
            result['message'] = f'Question {updated_question.get("question_number")} updated successfully'
            result['data'] = updated_question
            logger.info(f"Successfully updated question at index {question_index}")
        else:
            result['message'] = 'Failed to update question'
            result['errors'].append('Update operation failed')
            logger.error(f"Failed to update question at index {question_index}")
        
        return result


# ======================================================
# REST API IMPLEMENTATION EXAMPLES
# ======================================================
# ======================================================
# REST API IMPLEMENTATION EXAMPLES
# ======================================================

"""
COMPLETE REST API IMPLEMENTATION

Below are working examples for FastAPI and Flask implementations.
Copy these into your API server file when ready to deploy.

## Installation:
pip install fastapi uvicorn pydantic sqlalchemy psycopg2-binary

## Run:
uvicorn api_server:app --reload --port 8000
"""

# ======================================================
# FASTAPI IMPLEMENTATION
# ======================================================

FASTAPI_EXAMPLE = '''
"""
api_server.py - FastAPI Question Management API

Usage:
    uvicorn api_server:app --reload --port 8000

Endpoints:
    GET    /api/questions              - List all questions
    GET    /api/questions/{index}      - Get one question
    PUT    /api/questions/{index}      - Update question
    DELETE /api/questions/{index}      - Delete question
    POST   /api/questions/{index}/regenerate - Regenerate with AI
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, validator, Field
from typing import List, Optional
import logging

from services.question_api_service import QuestionAPIService

# Initialize FastAPI
app = FastAPI(
    title="SmartLesson Question API",
    description="API for managing test questions",
    version="1.0.0"
)

# CORS middleware (adjust origins as needed)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:8501"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service (use 'database' when ready)
question_service = QuestionAPIService(storage_backend='session_state')

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ======================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ======================================================

class QuestionUpdateRequest(BaseModel):
    """Request model for updating a question."""
    question_text: Optional[str] = Field(None, min_length=10, max_length=5000)
    choices: Optional[List[str]] = Field(None, min_items=4, max_items=4)
    correct_answer: Optional[str] = Field(None, pattern="^[A-D]$")
    bloom_level: Optional[str] = None
    points: Optional[float] = Field(None, gt=0, le=100)
    answer_key: Optional[str] = None
    sample_answer: Optional[str] = None
    
    @validator('bloom_level')
    def validate_bloom(cls, v):
        if v is not None:
            valid_levels = ['Remember', 'Understand', 'Apply', 'Analyze', 'Evaluate', 'Create']
            if v not in valid_levels:
                raise ValueError(f'bloom_level must be one of: {", ".join(valid_levels)}')
        return v
    
    class Config:
        schema_extra = {
            "example": {
                "question_text": "What is the capital of France?",
                "choices": ["London", "Paris", "Berlin", "Madrid"],
                "correct_answer": "B",
                "bloom_level": "Remember",
                "points": 2.0
            }
        }


class QuestionResponse(BaseModel):
    """Response model for a single question."""
    question_number: int
    type: str
    question_text: str
    bloom_level: str
    points: float
    outcome_text: Optional[str]
    choices: Optional[List[str]]
    correct_answer: Optional[str]
    answer_key: Optional[str]
    sample_answer: Optional[str]
    created_at: Optional[str]
    updated_at: Optional[str]


class UpdateResponse(BaseModel):
    """Response model for update operations."""
    success: bool
    message: str
    data: Optional[QuestionResponse]
    errors: List[str] = []


class RegenerateRequest(BaseModel):
    """Request model for regenerating a question."""
    api_key: str = Field(..., min_length=20)


# ======================================================
# API ROUTES
# ======================================================

@app.get("/api/questions", response_model=List[QuestionResponse])
async def get_all_questions():
    """
    Retrieve all questions.
    
    Returns:
        List of all questions in the system
    """
    try:
        # Note: session_state should be replaced with database session
        questions = question_service.get_all_questions(None)
        logger.info(f"Retrieved {len(questions)} questions")
        return questions
    except Exception as e:
        logger.error(f"Error retrieving questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving questions: {str(e)}"
        )


@app.get("/api/questions/{question_index}", response_model=QuestionResponse)
async def get_question(question_index: int):
    """
    Retrieve a single question by index.
    
    Args:
        question_index: Zero-based index of the question
    
    Returns:
        Question data
    
    Raises:
        404: Question not found
    """
    question = question_service.get_question_by_index(question_index, None)
    
    if not question:
        logger.warning(f"Question at index {question_index} not found")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question at index {question_index} not found"
        )
    
    logger.info(f"Retrieved question at index {question_index}")
    return question


@app.put("/api/questions/{question_index}", response_model=UpdateResponse)
async def update_question(question_index: int, data: QuestionUpdateRequest):
    """
    Update a question with validation.
    
    This endpoint:
    - Validates all input fields
    - Only updates modified fields
    - Maintains question order
    - Returns the updated question
    
    Args:
        question_index: Zero-based index of the question
        data: Fields to update (only include fields you want to change)
    
    Returns:
        UpdateResponse with success status and updated question
    
    Example:
        PUT /api/questions/0
        {
            "question_text": "What is the capital of Germany?",
            "choices": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
            "correct_answer": "A"
        }
    
    Raises:
        400: Validation error
        404: Question not found
    """
    logger.info(f"Updating question at index {question_index}")
    
    # Convert Pydantic model to dict, excluding None values
    update_data = data.dict(exclude_none=True)
    
    # Call validated update
    result = question_service.update_question_validated(
        question_index, 
        update_data, 
        None  # Replace with database session
    )
    
    if not result['success']:
        logger.warning(f"Update failed for question {question_index}: {result['errors']}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": result['message'],
                "errors": result['errors']
            }
        )
    
    logger.info(f"Successfully updated question at index {question_index}")
    return result


@app.delete("/api/questions/{question_index}")
async def delete_question(question_index: int):
    """
    Delete a question and renumber remaining questions.
    
    Args:
        question_index: Zero-based index of the question
    
    Returns:
        Success message
    
    Raises:
        404: Question not found
    """
    logger.info(f"Attempting to delete question at index {question_index}")
    
    success = question_service.delete_question(question_index, None)
    
    if not success:
        logger.warning(f"Failed to delete question at index {question_index}")
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Question at index {question_index} not found or could not be deleted"
        )
    
    logger.info(f"Successfully deleted question at index {question_index}")
    return {
        "success": True,
        "message": f"Question at index {question_index} deleted successfully"
    }


@app.post("/api/questions/{question_index}/regenerate", response_model=QuestionResponse)
async def regenerate_question(question_index: int, request: RegenerateRequest):
    """
    Regenerate a question using AI (Gemini API).
    
    This will:
    - Keep the same metadata (outcome, bloom level, type, points)
    - Generate new question text and answers
    - Preserve question number and order
    
    Args:
        question_index: Zero-based index of the question
        request: Contains api_key for Gemini
    
    Returns:
        The newly generated question
    
    Raises:
        400: Regeneration failed
        404: Question not found
    """
    logger.info(f"Regenerating question at index {question_index}")
    
    success = question_service.regenerate_question(
        question_index, 
        request.api_key, 
        None  # Replace with database session
    )
    
    if not success:
        logger.error(f"Failed to regenerate question at index {question_index}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Failed to regenerate question. Check API key and quota."
        )
    
    # Get the regenerated question
    new_question = question_service.get_question_by_index(question_index, None)
    
    logger.info(f"Successfully regenerated question at index {question_index}")
    return new_question


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "healthy", "service": "SmartLesson Question API"}


# ======================================================
# ERROR HANDLERS
# ======================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000, log_level="info")
'''

# ======================================================
# DATABASE IMPLEMENTATION (SQLAlchemy)
# ======================================================

DATABASE_EXAMPLE = '''
"""
database/models.py - Database models for questions

Usage with PostgreSQL:
    DATABASE_URL = "postgresql://user:pass@localhost:5432/smartlesson"
    
Usage with SQLite (development):
    DATABASE_URL = "sqlite:///./smartlesson.db"
"""

from sqlalchemy import Column, Integer, String, Float, Text, DateTime, JSON, create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from datetime import datetime

Base = declarative_base()


class Question(Base):
    """Database model for test questions."""
    __tablename__ = 'questions'
    
    # Primary key
    id = Column(Integer, primary_key=True, index=True)
    
    # Question metadata
    question_number = Column(Integer, nullable=False, index=True)
    question_type = Column(String(50), nullable=False, index=True)  # MCQ, Essay, etc.
    question_text = Column(Text, nullable=False)
    
    # MCQ specific fields
    choices = Column(JSON, nullable=True)  # ["Option A", "Option B", "Option C", "Option D"]
    correct_answer = Column(String(10), nullable=True)  # "A", "B", "C", or "D"
    
    # Short Answer specific
    answer_key = Column(Text, nullable=True)
    
    # Essay/Problem Solving/Drawing specific
    sample_answer = Column(Text, nullable=True)
    rubric = Column(JSON, nullable=True)  # Rubric structure with criteria
    
    # Educational metadata
    outcome_id = Column(Integer, nullable=True, index=True)
    outcome_text = Column(Text, nullable=True)
    bloom_level = Column(String(50), nullable=False, index=True)
    points = Column(Float, nullable=False)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Session/exam context
    exam_id = Column(Integer, nullable=True, index=True)  # Link to exam session
    
    def to_dict(self):
        """Convert model to dictionary."""
        return {
            "id": self.id,
            "question_number": self.question_number,
            "type": self.question_type,
            "question_type": self.question_type,
            "question_text": self.question_text,
            "choices": self.choices,
            "correct_answer": self.correct_answer,
            "answer_key": self.answer_key,
            "sample_answer": self.sample_answer,
            "rubric": self.rubric,
            "outcome_id": self.outcome_id,
            "outcome_text": self.outcome_text,
            "bloom": self.bloom_level,
            "bloom_level": self.bloom_level,
            "points": self.points,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "exam_id": self.exam_id
        }


# Database setup
DATABASE_URL = "postgresql://user:password@localhost:5432/smartlesson"
# or for SQLite: DATABASE_URL = "sqlite:///./smartlesson.db"

engine = create_engine(DATABASE_URL, echo=True)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create tables
Base.metadata.create_all(bind=engine)


# Dependency for FastAPI routes
def get_db():
    """Get database session."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
'''

print("API Implementation examples ready. See FASTAPI_EXAMPLE and DATABASE_EXAMPLE strings above.")
