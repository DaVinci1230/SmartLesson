# SmartLesson - AI-Powered Test Question Generator

An intelligent assessment generator that creates Table of Specifications (TOS) and Test Question Sets (TQS) using AI, aligned with Bloom's Taxonomy and learning outcomes.

## Features

- 📚 **Course & Syllabus Management** - Upload PDFs or input manually
- 🎯 **Learning Outcomes** - Define and manage course outcomes
- 📊 **Assessment Profile** - Configure exam parameters and question types
- 📋 **Generate TOS** - Auto-generate Table of Specifications with weighted distribution
- ❓ **Generate TQS** - AI-powered question generation (MCQ, Short Answer, Essay)
- 📥 **Export** - Export to DOCX, PDF, CSV with answer keys
- 🔀 **Shuffle & Versions** - Generate Version A & B with shuffled choices

## Tech Stack

- **Python 3.10+**
- **Streamlit** - Web interface
- **Google Gemini AI** - Question generation
- **python-docx** - DOCX export
- **reportlab** - PDF export
- **pandas** - Data processing

## Deployment

### Option 1: Streamlit Community Cloud (Recommended)

1. Push your code to GitHub
2. Go to [share.streamlit.io](https://share.streamlit.io)
3. Connect your GitHub account
4. Deploy from your repository
5. Add `GEMINI_API_KEY` in Secrets section

### Option 2: Local Installation

```bash
# Clone repository
git clone <your-repo-url>
cd SmartLesson

# Create virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
source venv/bin/activate  # Mac/Linux

# Install dependencies
pip install -r requirements.txt

# Set environment variable
# Windows:
set GEMINI_API_KEY=your-key-here
# Mac/Linux:
export GEMINI_API_KEY=your-key-here

# Run application
streamlit run app.py
```

## Usage

1. **Course Details** - Enter course code, title, instructor
2. **Learning Outcomes** - Add or upload learning outcomes
3. **Assessment Profile** - Set exam parameters and question distribution
4. **Generate TOS** - Review and edit the Table of Specifications
5. **Generate TQS** - Let AI create questions based on TOS
6. **Export** - Download in your preferred format

## Getting a Gemini API Key

1. Go to [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Click "Get API Key"
3. Create a new API key
4. Copy and save it securely

## License

Educational Project - MIT License

## Author

Developed as an educational tool for automated assessment generation.
