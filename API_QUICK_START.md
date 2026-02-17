# REST API Quick Start Guide

## 🚀 Backend API Endpoint - Complete Implementation

This guide shows you how to use the **validated update endpoint** for questions.

---

## 📦 Installation

```bash
pip install fastapi uvicorn pydantic
```

---

## ▶️ Start the API Server

```bash
# Method 1: Using uvicorn directly
uvicorn api_server:app --reload --port 8000

# Method 2: Run the file directly
python api_server.py
```

**Access Points:**
- 📍 API Base: http://localhost:8000
- 📚 Swagger UI (Interactive Docs): http://localhost:8000/docs
- 📖 ReDoc: http://localhost:8000/redoc

---

## 🎯 Update Question Endpoint

### **Endpoint:** `PUT /api/questions/{question_index}`

### **Features:**
✅ Validates all input fields  
✅ Only updates modified fields (partial updates)  
✅ Verifies `correct_answer` exists in `choices`  
✅ Returns updated question  
✅ Keeps question order intact  
✅ Auto-recalculates statistics  

### **Input Schema:**

```json
{
  "question_text": "string (optional, 10-5000 chars)",
  "choices": ["string", "string", "string", "string"] (optional, exactly 4 for MCQ),
  "correct_answer": "A|B|C|D (optional, MCQ only)",
  "bloom_level": "Remember|Understand|Apply|Analyze|Evaluate|Create (optional)",
  "points": 0.5-100.0 (optional),
  "answer_key": "string (optional, Short Answer only)",
  "sample_answer": "string (optional, Essay/Problem/Drawing)"
}
```

### **Validation Rules:**

| Field | Rules |
|-------|-------|
| `question_text` | 10-5000 characters |
| `choices` | Exactly 4 items (MCQ only) |
| `correct_answer` | Must be A, B, C, or D (MCQ only)<br>Must exist in `choices` array |
| `bloom_level` | Must be one of: Remember, Understand, Apply, Analyze, Evaluate, Create |
| `points` | Must be > 0 and ≤ 100 |

---

## 📝 Example Requests

### **1. Update MCQ Question (Full Update)**

```bash
curl -X PUT "http://localhost:8000/api/questions/0" \
  -H "Content-Type: application/json" \
  -d '{
    "question_text": "What is the capital of Germany?",
    "choices": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
    "correct_answer": "A",
    "bloom_level": "Remember",
    "points": 2.0
  }'
```

**Response (Success):**
```json
{
  "success": true,
  "message": "Question 1 updated successfully",
  "data": {
    "question_number": 1,
    "type": "MCQ",
    "question_text": "What is the capital of Germany?",
    "choices": ["Berlin", "Munich", "Hamburg", "Frankfurt"],
    "correct_answer": "A",
    "bloom_level": "Remember",
    "points": 2.0,
    "outcome_text": "Understand European geography",
    "created_at": "2026-02-17T10:30:00",
    "updated_at": "2026-02-17T11:45:00"
  },
  "errors": []
}
```

---

### **2. Partial Update (Only Change Points)**

```bash
curl -X PUT "http://localhost:8000/api/questions/0" \
  -H "Content-Type: application/json" \
  -d '{
    "points": 3.0
  }'
```

**Response:**
```json
{
  "success": true,
  "message": "Question 1 updated successfully",
  "data": { 
    // All other fields unchanged, only points updated
    "points": 3.0
  },
  "errors": []
}
```

---

### **3. Update Bloom Level Only**

```bash
curl -X PUT "http://localhost:8000/api/questions/2" \
  -H "Content-Type: application/json" \
  -d '{
    "bloom_level": "Apply"
  }'
```

---

### **4. Update Choices and Correct Answer**

```bash
curl -X PUT "http://localhost:8000/api/questions/0" \
  -H "Content-Type: application/json" \
  -d '{
    "choices": ["Paris", "London", "Rome", "Madrid"],
    "correct_answer": "A"
  }'
```

---

### **5. Validation Error Example**

**Request:**
```bash
curl -X PUT "http://localhost:8000/api/questions/0" \
  -H "Content-Type: application/json" \
  -d '{
    "correct_answer": "E",
    "points": -5
  }'
```

**Response (400 Bad Request):**
```json
{
  "success": false,
  "message": "Validation failed",
  "data": null,
  "errors": [
    "Invalid correct_answer: E. Must be A, B, C, or D",
    "Points must be greater than 0"
  ]
}
```

---

## 🐍 Python Client Examples

### **Using Requests Library**

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Update a question
def update_question(index, data):
    response = requests.put(
        f"{BASE_URL}/questions/{index}",
        json=data
    )
    return response.json()

# Example 1: Full update
result = update_question(0, {
    "question_text": "What is the capital of France?",
    "choices": ["London", "Paris", "Berlin", "Madrid"],
    "correct_answer": "B",
    "bloom_level": "Remember",
    "points": 2.0
})

if result['success']:
    print(f"✅ {result['message']}")
    print(f"Updated question: {result['data']['question_text']}")
else:
    print(f"❌ Update failed: {result['errors']}")

# Example 2: Partial update (only points)
result = update_question(0, {"points": 3.0})
```

---

### **Using HTTPX (Async)**

```python
import httpx
import asyncio

async def update_question_async(index, data):
    async with httpx.AsyncClient() as client:
        response = await client.put(
            f"http://localhost:8000/api/questions/{index}",
            json=data
        )
        return response.json()

# Run async
result = asyncio.run(update_question_async(0, {
    "question_text": "Updated question text",
    "bloom_level": "Apply"
}))
```

---

## 🧪 Testing with Interactive Docs

1. Open http://localhost:8000/docs in your browser
2. Find **PUT /api/questions/{question_index}**
3. Click "Try it out"
4. Enter:
   - `question_index`: 0
   - Request body:
     ```json
     {
       "question_text": "Test question?",
       "bloom_level": "Understand",
       "points": 5.0
     }
     ```
5. Click "Execute"
6. See the response below!

---

## 📊 All Available Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/questions` | List all questions |
| GET | `/api/questions/{index}` | Get single question |
| **PUT** | `/api/questions/{index}` | **Update question (validated)** |
| DELETE | `/api/questions/{index}` | Delete question |
| POST | `/api/questions/{index}/regenerate` | Regenerate with AI |
| GET | `/health` | Health check |

---

## 🔧 Database Update Logic

### **Current: Session State**

The API currently uses session state. To switch to database:

### **Step 1: Update `api_server.py`**

```python
# Change this line:
question_service = QuestionAPIService(storage_backend='session_state')

# To:
question_service = QuestionAPIService(storage_backend='database')
```

### **Step 2: Implement Database Methods**

In `services/question_api_service.py`, add database logic:

```python
class QuestionAPIService:
    def update_question(self, question_index: int, updated_data: Dict, db_session):
        if self.storage_backend == 'database':
            # Get question from database
            question = db_session.query(Question).filter(
                Question.id == question_index
            ).first()
            
            if not question:
                return False
            
            # Update fields
            for key, value in updated_data.items():
                setattr(question, key, value)
            
            # Set timestamp
            question.updated_at = datetime.utcnow()
            
            # Commit
            db_session.commit()
            db_session.refresh(question)
            
            return True
```

### **Step 3: Database Schema**

```sql
CREATE TABLE questions (
    id SERIAL PRIMARY KEY,
    question_number INTEGER NOT NULL,
    question_type VARCHAR(50) NOT NULL,
    question_text TEXT NOT NULL,
    choices JSONB,
    correct_answer VARCHAR(10),
    answer_key TEXT,
    sample_answer TEXT,
    rubric JSONB,
    outcome_id INTEGER,
    outcome_text TEXT,
    bloom_level VARCHAR(50) NOT NULL,
    points DECIMAL(5,2) NOT NULL,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    exam_id INTEGER
);

CREATE INDEX idx_questions_type ON questions(question_type);
CREATE INDEX idx_questions_bloom ON questions(bloom_level);
CREATE INDEX idx_questions_exam ON questions(exam_id);
```

---

## 🛡️ Key Features

### **1. Comprehensive Validation**
- ✅ Field type checking
- ✅ Value range validation
- ✅ MCQ-specific rules (4 choices, valid answer)
- ✅ Bloom level validation
- ✅ Points range checking

### **2. Partial Updates**
- Only updates fields you provide
- Other fields remain unchanged
- No need to send entire question object

### **3. Automatic Features**
- Auto-updates `updated_at` timestamp
- Recalculates statistics after update
- Maintains question order
- Logs all operations

### **4. Error Handling**
- Detailed error messages
- Validation errors listed individually
- HTTP status codes follow REST standards

---

## 🚨 Common Errors & Solutions

| Error | Cause | Solution |
|-------|-------|----------|
| 400 - Validation failed | Invalid field value | Check error message, fix field |
| 404 - Not found | Wrong question index | Verify index (0-based) |
| 500 - Server error | Backend issue | Check server logs |

---

## 📚 Additional Resources

- **API Documentation**: http://localhost:8000/docs
- **Service Code**: `services/question_api_service.py`
- **Server Code**: `api_server.py`
- **Implementation Guide**: `EDITABLE_TQS_CARDS_IMPLEMENTATION.md`

---

## 🎯 Quick Test Script

Save as `test_api.py`:

```python
import requests

BASE_URL = "http://localhost:8000/api"

# Test update endpoint
response = requests.put(
    f"{BASE_URL}/questions/0",
    json={
        "question_text": "What is 2 + 2?",
        "choices": ["2", "3", "4", "5"],
        "correct_answer": "C",
        "bloom_level": "Remember",
        "points": 1.0
    }
)

result = response.json()

if result['success']:
    print("✅ Update successful!")
    print(f"Message: {result['message']}")
    print(f"Updated question: {result['data']['question_text']}")
else:
    print("❌ Update failed!")
    print(f"Errors: {result['errors']}")
```

Run:
```bash
python test_api.py
```

---

## ✅ Summary

The update endpoint provides:
- **Validated** field-level updates
- **Partial** update support
- **Verified** correct_answer in choices
- **Maintained** question order
- **Automatic** statistics recalculation
- **Detailed** error reporting

**Ready to use!** Start the server and test with the examples above. 🚀
