import re
from PyPDF2 import PdfReader
import io


def extract_syllabus_details(pdf_file, exam_term="Midterm"):
    """
    Extract course details from a PDF syllabus.
    Focuses on Section IV (Learning Plan) and extracts learning outcomes from the syllabus table.
    
    Parameters:
    - pdf_file: PDF file object
    - exam_term: "Midterm" or "Final" - filters which learning outcomes to extract
      * Midterm: Extract outcomes from start until "Midterm Examination"
      * Final: Extract outcomes from "Midterm Examination" to "Final Examination"
    
    Returns a dictionary with:
    - course_code: str
    - course_title: str
    - semester: str (1st, 2nd, Summer)
    - academic_year: str
    - instructor: str
    - learning_outcomes: list of str (from syllabus table, filtered by exam_term)
    """
    
    try:
        # Read PDF - LIMIT to first 15 pages to get full syllabus table
        pdf_reader = PdfReader(pdf_file)
        pages_to_read = min(15, len(pdf_reader.pages))
        text = ""
        
        for i in range(pages_to_read):
            page_text = pdf_reader.pages[i].extract_text()
            if page_text:
                text += page_text + "\n"
        
        # Initialize result dictionary
        result = {
            "course_code": "",
            "course_title": "",
            "semester": "",
            "academic_year": "",
            "instructor": "",
            "learning_outcomes": []
        }
        
        # ==========================================
        # EXTRACT BASIC COURSE INFORMATION
        # ==========================================
        
        # Extract Course Code
        code_match = re.search(r'(?:Course\s*Code|Code)\s*[:=]\s*(\w+[-\s]?\d{3,4})', text, re.IGNORECASE)
        if code_match:
            result["course_code"] = code_match.group(1).replace(" ", "").upper()
        
        # Extract Course Title
        title_match = re.search(r'(?:Course\s*Title|Subject)\s*[:=]\s*([^\n]{5,100})', text, re.IGNORECASE)
        if title_match:
            result["course_title"] = title_match.group(1).strip()
        
        # Extract Instructor
        instructor_match = re.search(r'(?:Instructor|Professor)\s*[:=]\s*([^\n]{2,100})', text, re.IGNORECASE)
        if instructor_match:
            result["instructor"] = instructor_match.group(1).strip()
        
        # Extract Semester
        sem_match = re.search(r'(?:Semester)\s*[:=]\s*(1st|2nd|Summer|First|Second)', text, re.IGNORECASE)
        if sem_match:
            sem_text = sem_match.group(1).lower()
            if "1" in sem_text or "first" in sem_text:
                result["semester"] = "1st"
            elif "2" in sem_text or "second" in sem_text:
                result["semester"] = "2nd"
            elif "summer" in sem_text:
                result["semester"] = "Summer"
        
        # Extract Academic Year
        year_match = re.search(r'(?:Academic\s*Year|AY)\s*[:=]\s*(\d{4}[–\-]\d{4})', text)
        if year_match:
            result["academic_year"] = year_match.group(1).strip()
        
        # ==========================================
        # EXTRACT LEARNING OUTCOMES FROM LEARNING PLAN
        # ==========================================
        
        # Find Section IV / IV. LEARNING PLAN start
        section_iv_idx = text.upper().find('IV. LEARNING PLAN')
        if section_iv_idx == -1:
            section_iv_idx = text.upper().find('SECTION IV')
        if section_iv_idx == -1:
            section_iv_idx = text.upper().find('IV -')
        if section_iv_idx == -1:
            section_iv_idx = text.upper().find('IV.')
        
        if section_iv_idx >= 0:
            # Extract large section containing full syllabus table
            section_text = text[section_iv_idx:section_iv_idx + 50000]
            
            # Replace multiple spaces and normalize newlines
            section_text = re.sub(r'\s+', ' ', section_text)
            
            # Split more intelligently - look for "o " pattern which marks new objectives
            # But first, let's use a simpler approach: find all lines with "o " at the start
            # after cleaning
            
            outcomes = []
            passed_midterm = False
            
            # ===== Find where objectives start =====
            # Look for patterns: "\no " which indicates a bulleted learning objective
            
            # Use regex to find all "o xxx" patterns that are learning outcomes
            # They appear after the week/timeframe number in the learning outcomes column
            
            # Split by bullet markers - supports different bullet types
            # The most common pattern in PDFs is " o " so we prioritize that
            # Comment out or modify the bullets list below to add/remove support
            
            # Supported bullet types (add/remove as needed):
            bullets_to_try = [
                ' o ',        # Main pattern (used in your syllabus)
                ' • ',        # Bullet point
                ' * ',        # Asterisk
                ' ▪ ',        # Black square
                ' □ ',        # Empty square
                ' ○ ',        # Empty circle
                # ' - ',      # Dash (commented: causes issues with "Human - Computer")
                # ' ◆ ',      # Diamond
                # ' ★ ',      # Star
            ]
            
            # Try splitting with the first bullet type that produces results
            parts = None
            for bullet in bullets_to_try:
                if bullet in section_text:
                    parts = section_text.split(bullet)
                    if len(parts) > 2:  # Found multiple objectives
                        break
            
            if parts is None:
                parts = section_text.split(' o ')  # Default fallback
            
            for part in parts[1:]:  # Skip first part (before any objective)
                # Check for exam term markers
                if 'MIDTERM' in part.upper() and any(x in part.upper() for x in ['EXAM', 'TEST']):
                    if exam_term == "Midterm":
                        break
                    else:
                        passed_midterm = True
                        continue
                
                if 'FINAL' in part.upper() and any(x in part.upper() for x in ['EXAM', 'TEST']):
                    if exam_term == "Final":
                        # Continue collecting
                        pass
                
                # Stop at next section
                if 'V.' in part and any(x in part [:50].upper() for x in ['LEARNING', 'ASSESSMENT']):
                    break
                
                # Extract the objective text (take from start until we hit content from another column)
                # Usually objectives end before hitting text like "CO1" or "CO2" or "Introduction to"
                # which marks the "Aligned Outcomes" or "Content" columns
                
                # Take first ~300 characters as the objective
                objective_raw = part[:500]
                
                # Stop at markers that indicate we've left the objectives column
                stop_markers = ['CO1', 'CO2', 'CO3', 'CO4', 'CO5', '• ', 'Chapter', 'Preece', 'Introduction to']
                for marker in stop_markers:
                    if marker in objective_raw:
                        objective_raw = objective_raw[:objective_raw.find(marker)]
                        break
                
                # Clean up the objective
                cleaned = objective_raw.strip()
                # Remove any leading/trailing line breaks
                cleaned = re.sub(r'^[\s\n]+|[\s\n]+$', '', cleaned)
                # Normalize spaces
                cleaned = re.sub(r'\s+', ' ', cleaned)
                # Remove trailing punctuation from column overflow
                if cleaned.endswith('  '):
                    cleaned = cleaned.rstrip()
                
                # Validate
                if cleaned and len(cleaned) >= 15 and len(cleaned) <= 300:
                    # Make sure it looks like an objective (not just random text)
                    action_verbs = [
                        'explain', 'understand', 'analyze', 'design', 'create', 'apply', 'evaluate',
                        'develop', 'identify', 'describe', 'summarize', 'define', 'compare', 'demonstrate',
                        'implement', 'recognize', 'solve', 'use', 'write', 'make', 'interpret', 'assess',
                        'examine', 'discuss', 'present', 'construct', 'build', 'model', 'compute', 'learn',
                        'acquire', 'master', 'practice', 'perform', 'achieve', 'gain', 'know', 'outline',
                        'differentiate', 'determine', 'distinguish'
                    ]
                    
                    starts_with_verb = any(cleaned.lower().startswith(verb) for verb in action_verbs)
                    
                    if starts_with_verb and cleaned not in outcomes:
                        # Apply exam term filtering
                        if exam_term == "Final" and not passed_midterm:
                            continue
                        outcomes.append(cleaned)
            
            result["learning_outcomes"] = outcomes[:50]
        
        return result
    
    except Exception as e:
        return {
            "error": str(e),
            "course_code": "",
            "course_title": "",
            "semester": "",
            "academic_year": "",
            "instructor": "",
            "learning_outcomes": []
        }

