"""
api_server.py - FastAPI Question Management API

This is a production-ready REST API server for managing test questions.

Installation:
    pip install fastapi uvicorn pydantic

Run:
    uvicorn api_server:app --reload --port 8000

API Documentation:
    http://localhost:8000/docs (Swagger UI)
    http://localhost:8000/redoc (ReDoc)

Endpoints:
    GET    /api/questions              - List all questions
    GET    /api/questions/{index}      - Get one question by index
    PUT    /api/questions/{index}      - Update question (validated)
    DELETE /api/questions/{index}      - Delete question
    POST   /api/questions/{index}/regenerate - Regenerate with AI
    GET    /api/export/docx            - Export to DOCX
    GET    /api/export/pdf             - Export to PDF
    GET    /api/export/csv             - Export to CSV
    GET    /health                     - Health check
"""

from fastapi import FastAPI, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, validator, Field
from typing import List, Optional
import logging
import io

from services.question_api_service import QuestionAPIService
from services.tqs_export_service import tqs_export_service

# ======================================================
# APP INITIALIZATION
# ======================================================

app = FastAPI(
    title="SmartLesson Question API",
    description="REST API for managing test questions with AI regeneration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# CORS middleware - adjust origins for production
app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:3000",   # React dev server
        "http://localhost:8501",   # Streamlit
        "http://localhost:8000",   # This API
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize service
# TODO: Change to 'database' when database is set up
question_service = QuestionAPIService(storage_backend='session_state')

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


# ======================================================
# PYDANTIC MODELS (Request/Response Schemas)
# ======================================================

class QuestionUpdateRequest(BaseModel):
    """
    Request model for updating a question.
    
    All fields are optional - only include fields you want to update.
    """
    question_text: Optional[str] = Field(
        None, 
        min_length=10, 
        max_length=5000,
        description="The question text"
    )
    choices: Optional[List[str]] = Field(
        None, 
        min_items=4, 
        max_items=4,
        description="Exactly 4 choices for MCQ questions"
    )
    correct_answer: Optional[str] = Field(
        None, 
        pattern="^[A-D]$",
        description="Correct answer: A, B, C, or D (for MCQ only)"
    )
    bloom_level: Optional[str] = Field(
        None,
        description="Bloom's taxonomy level"
    )
    points: Optional[float] = Field(
        None, 
        gt=0, 
        le=100,
        description="Point value (0.5 to 100)"
    )
    answer_key: Optional[str] = Field(
        None,
        description="Expected answer for Short Answer questions"
    )
    sample_answer: Optional[str] = Field(
        None,
        description="Sample answer for Essay/Problem Solving/Drawing questions"
    )
    
    @validator('bloom_level')
    def validate_bloom(cls, v):
        """Validate bloom level is one of the 6 standard levels."""
        if v is not None:
            valid_levels = [
                'Remember', 'Understand', 'Apply', 
                'Analyze', 'Evaluate', 'Create'
            ]
            if v not in valid_levels:
                raise ValueError(
                    f'bloom_level must be one of: {", ".join(valid_levels)}'
                )
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
    outcome_text: Optional[str] = None
    choices: Optional[List[str]] = None
    correct_answer: Optional[str] = None
    answer_key: Optional[str] = None
    sample_answer: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None
    
    class Config:
        schema_extra = {
            "example": {
                "question_number": 1,
                "type": "MCQ",
                "question_text": "What is the capital of France?",
                "bloom_level": "Remember",
                "points": 2.0,
                "outcome_text": "Understand European geography",
                "choices": ["London", "Paris", "Berlin", "Madrid"],
                "correct_answer": "B",
                "created_at": "2026-02-17T10:30:00",
                "updated_at": "2026-02-17T10:30:00"
            }
        }


class UpdateResponse(BaseModel):
    """Response model for update operations."""
    success: bool
    message: str
    data: Optional[QuestionResponse] = None
    errors: List[str] = []


class RegenerateRequest(BaseModel):
    """Request model for regenerating a question."""
    api_key: str = Field(
        ..., 
        min_length=20,
        description="Gemini API key for question generation"
    )


class DeleteResponse(BaseModel):
    """Response model for delete operations."""
    success: bool
    message: str


class HealthResponse(BaseModel):
    """Response model for health check."""
    status: str
    service: str
    version: str


# ======================================================
# API ROUTES
# ======================================================

@app.get(
    "/api/questions", 
    response_model=List[QuestionResponse],
    summary="Get all questions",
    description="Retrieve all questions in the system"
)
async def get_all_questions():
    """
    Retrieve all questions.
    
    Returns:
        List of all questions with full details
    
    Example:
        GET /api/questions
    """
    try:
        questions = question_service.get_all_questions(None)
        logger.info(f"Retrieved {len(questions)} questions")
        return questions
    except Exception as e:
        logger.error(f"Error retrieving questions: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving questions: {str(e)}"
        )


@app.get(
    "/api/questions/{question_index}", 
    response_model=QuestionResponse,
    summary="Get single question",
    description="Retrieve a specific question by its index"
)
async def get_question(question_index: int):
    """
    Retrieve a single question by index.
    
    Args:
        question_index: Zero-based index of the question
    
    Returns:
        Question data with all fields
    
    Raises:
        404: Question not found at the given index
    
    Example:
        GET /api/questions/0
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


@app.put(
    "/api/questions/{question_index}", 
    response_model=UpdateResponse,
    summary="Update question",
    description="Update a question with full validation. Only include fields you want to change."
)
async def update_question(question_index: int, data: QuestionUpdateRequest):
    """
    Update a question with comprehensive validation.
    
    This endpoint:
    - ✅ Validates all input fields
    - ✅ Only updates fields you provide (partial updates supported)
    - ✅ Maintains question order
    - ✅ Verifies correct_answer exists in choices (for MCQ)
    - ✅ Returns the updated question
    
    Args:
        question_index: Zero-based index of the question (0, 1, 2, ...)
        data: Fields to update (only include what you want to change)
    
    Returns:
        UpdateResponse with:
        - success: true/false
        - message: Description of result
        - data: Updated question object
        - errors: List of validation errors (if any)
    
    Validation Rules:
    - question_text: Must be 10-5000 characters
    - choices: Must be exactly 4 items (MCQ only)
    - correct_answer: Must be A, B, C, or D (MCQ only)
    - bloom_level: Must be Remember/Understand/Apply/Analyze/Evaluate/Create
    - points: Must be 0 < points <= 100
    
    Example Request:
        PUT /api/questions/0
        {
            "question_text": "What is the capital of Germany?",
            "choices": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
            "correct_answer": "A",
            "bloom_level": "Remember",
            "points": 2.0
        }
    
    Example Response (Success):
        {
            "success": true,
            "message": "Question 1 updated successfully",
            "data": { ... updated question ... },
            "errors": []
        }
    
    Example Response (Validation Error):
        {
            "success": false,
            "message": "Validation failed",
            "data": null,
            "errors": [
                "Invalid correct_answer: E. Must be A, B, C, or D",
                "Points must be greater than 0"
            ]
        }
    
    Raises:
        400: Validation error or update failed
        404: Question not found at the given index
    """
    logger.info(f"Updating question at index {question_index}")
    
    # Convert Pydantic model to dict, excluding None values
    update_data = data.dict(exclude_none=True)
    
    # Call validated update
    result = question_service.update_question_validated(
        question_index, 
        update_data, 
        None  # TODO: Replace with database session
    )
    
    if not result['success']:
        logger.warning(
            f"Update failed for question {question_index}: {result['errors']}"
        )
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "message": result['message'],
                "errors": result['errors']
            }
        )
    
    logger.info(f"Successfully updated question at index {question_index}")
    return result


@app.delete(
    "/api/questions/{question_index}",
    response_model=DeleteResponse,
    summary="Delete question",
    description="Delete a question and automatically renumber remaining questions"
)
async def delete_question(question_index: int):
    """
    Delete a question and renumber remaining questions.
    
    When a question is deleted:
    1. Question is removed from the list
    2. All subsequent questions are renumbered (1, 2, 3, ...)
    3. Statistics are recalculated
    
    Args:
        question_index: Zero-based index of the question to delete
    
    Returns:
        Success message
    
    Raises:
        404: Question not found or deletion failed
    
    Example:
        DELETE /api/questions/2
        
        Response:
        {
            "success": true,
            "message": "Question at index 2 deleted successfully"
        }
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


@app.post(
    "/api/questions/{question_index}/regenerate", 
    response_model=QuestionResponse,
    summary="Regenerate question with AI",
    description="Use Gemini API to regenerate a question while keeping same metadata"
)
async def regenerate_question(question_index: int, request: RegenerateRequest):
    """
    Regenerate a question using AI (Gemini API).
    
    This will:
    - ✅ Keep the same metadata (outcome, bloom level, type, points)
    - ✅ Generate completely new question text and answers
    - ✅ Preserve question number and order
    - ✅ Update the question in place
    
    The AI generates questions based on:
    - Learning outcome
    - Bloom's taxonomy level
    - Question type (MCQ, Essay, etc.)
    - Point value
    
    Args:
        question_index: Zero-based index of the question
        request: Contains Gemini API key
    
    Returns:
        The newly generated question
    
    Raises:
        400: Regeneration failed (check API key and quota)
        404: Question not found
    
    Example:
        POST /api/questions/0/regenerate
        {
            "api_key": "your-gemini-api-key-here"
        }
        
        Response:
        {
            "question_number": 1,
            "type": "MCQ",
            "question_text": "Which of the following best describes...",
            "choices": [...],
            "correct_answer": "B",
            ...
        }
    """
    logger.info(f"Regenerating question at index {question_index}")
    
    success = question_service.regenerate_question(
        question_index, 
        request.api_key, 
        None  # TODO: Replace with database session
    )
    
    if not success:
        logger.error(f"Failed to regenerate question at index {question_index}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=(
                "Failed to regenerate question. "
                "Please check your API key and ensure you haven't exceeded quota limits."
            )
        )
    
    # Get the regenerated question
    new_question = question_service.get_question_by_index(question_index, None)
    
    logger.info(f"Successfully regenerated question at index {question_index}")
    return new_question


@app.get(
    "/health",
    response_model=HealthResponse,
    summary="Health check",
    description="Check if the API is running"
)
async def health_check():
    """
    Health check endpoint.
    
    Returns:
        Status information about the API
    
    Example:
        GET /health
        
        Response:
        {
            "status": "healthy",
            "service": "SmartLesson Question API",
            "version": "1.0.0"
        }
    """
    return {
        "status": "healthy", 
        "service": "SmartLesson Question API",
        "version": "1.0.0"
    }


# ======================================================
# EXPORT ENDPOINTS
# ======================================================

@app.get(
    "/api/export/docx",
    summary="Export questions to DOCX",
    description="Download all questions as a formatted Word document with answer key"
)
async def export_to_docx(
    course_name: Optional[str] = "Course Name",
    exam_title: Optional[str] = "Test Question Sheet",
    exam_term: Optional[str] = "Midterm",
    instructor_name: Optional[str] = ""
):
    """
    Export all questions to DOCX format.
    
    Query Parameters:
        - course_name: Name of the course
        - exam_title: Title of the exam
        - exam_term: Exam term (Midterm, Final, etc.)
        - instructor_name: Instructor name
    
    Returns:
        DOCX file with formatted questions and answer key
    
    Example:
        GET /api/export/docx?course_name=CS101&exam_title=Midterm%20Exam
    """
    try:
        # Get all questions
        questions = question_service.get_all_questions(None)
        
        if not questions:
            raise HTTPException(
                status_code=404,
                detail="No questions found to export"
            )
        
        # Generate DOCX
        docx_buffer = tqs_export_service.export_to_docx(
            questions=questions,
            course_name=course_name,
            exam_title=exam_title,
            exam_term=exam_term,
            instructor_name=instructor_name
        )
        
        # Generate filename
        filename = f"{exam_title.replace(' ', '_')}_{exam_term}.docx"
        
        # Return file
        return StreamingResponse(
            io.BytesIO(docx_buffer.read()),
            media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to DOCX: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export to DOCX: {str(e)}"
        )


@app.get(
    "/api/export/pdf",
    summary="Export questions to PDF",
    description="Download all questions as a formatted PDF document with answer key"
)
async def export_to_pdf(
    course_name: Optional[str] = "Course Name",
    exam_title: Optional[str] = "Test Question Sheet",
    exam_term: Optional[str] = "Midterm",
    instructor_name: Optional[str] = ""
):
    """
    Export all questions to PDF format.
    
    Query Parameters:
        - course_name: Name of the course
        - exam_title: Title of the exam
        - exam_term: Exam term (Midterm, Final, etc.)
        - instructor_name: Instructor name
    
    Returns:
        PDF file with formatted questions and answer key
    
    Example:
        GET /api/export/pdf?course_name=CS101&exam_title=Final%20Exam
    """
    try:
        # Get all questions
        questions = question_service.get_all_questions(None)
        
        if not questions:
            raise HTTPException(
                status_code=404,
                detail="No questions found to export"
            )
        
        # Generate PDF
        pdf_buffer = tqs_export_service.export_to_pdf(
            questions=questions,
            course_name=course_name,
            exam_title=exam_title,
            exam_term=exam_term,
            instructor_name=instructor_name
        )
        
        # Generate filename
        filename = f"{exam_title.replace(' ', '_')}_{exam_term}.pdf"
        
        # Return file
        return StreamingResponse(
            io.BytesIO(pdf_buffer.read()),
            media_type="application/pdf",
            headers={"Content-Disposition": f"attachment; filename={filename}"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to PDF: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export to PDF: {str(e)}"
        )


@app.get(
    "/api/export/csv",
    summary="Export questions to CSV",
    description="Download all questions as a CSV file for import into other systems"
)
async def export_to_csv():
    """
    Export all questions to CSV format.
    
    Format:
        Question Number, Question Text, Question Type, Option A, Option B, 
        Option C, Option D, Correct Answer, Answer Key/Sample Answer, 
        Bloom Level, Points, Learning Outcome
    
    Returns:
        CSV file with all question data
    
    Example:
        GET /api/export/csv
    """
    try:
        # Get all questions
        questions = question_service.get_all_questions(None)
        
        if not questions:
            raise HTTPException(
                status_code=404,
                detail="No questions found to export"
            )
        
        # Generate CSV
        csv_buffer = tqs_export_service.export_to_csv(questions)
        
        # Return file
        return StreamingResponse(
            io.StringIO(csv_buffer.read()),
            media_type="text/csv",
            headers={"Content-Disposition": "attachment; filename=questions_export.csv"}
        )
    
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Error exporting to CSV: {str(e)}")
        raise HTTPException(
            status_code=500,
            detail=f"Failed to export to CSV: {str(e)}"
        )


# ======================================================
# ERROR HANDLERS
# ======================================================

@app.exception_handler(ValueError)
async def value_error_handler(request, exc):
    """Handle ValueError exceptions."""
    logger.error(f"ValueError: {str(exc)}")
    return HTTPException(
        status_code=status.HTTP_400_BAD_REQUEST,
        detail=str(exc)
    )


# ======================================================
# STARTUP/SHUTDOWN EVENTS
# ======================================================

@app.on_event("startup")
async def startup_event():
    """Run on API startup."""
    logger.info("🚀 SmartLesson Question API starting up...")
    logger.info("📚 API Documentation available at: http://localhost:8000/docs")


@app.on_event("shutdown")
async def shutdown_event():
    """Run on API shutdown."""
    logger.info("👋 SmartLesson Question API shutting down...")


# ======================================================
# MAIN (for running directly)
# ======================================================

if __name__ == "__main__":
    import uvicorn
    
    print("=" * 60)
    print("🚀 Starting SmartLesson Question API Server")
    print("=" * 60)
    print("📍 API URL: http://localhost:8000")
    print("📚 Swagger UI: http://localhost:8000/docs")
    print("📖 ReDoc: http://localhost:8000/redoc")
    print("=" * 60)
    
    uvicorn.run(
        app, 
        host="0.0.0.0", 
        port=8000, 
        log_level="info",
        reload=True  # Auto-reload on code changes (development only)
    )
