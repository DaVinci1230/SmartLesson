# TQS File Upload - Quick Start & Examples

## 5-Minute Quick Start

### Option A: Using Internally Generated TOS (Existing Flow)

1. Go to **Assessment Generator** tab
2. Fill Course/Syllabus info
3. Add Learning Outcomes
4. Set Bloom's Taxonomy profile
5. Click **Generate TOS** button
6. Go to **Generate TQS** tab
7. Select "Use Generated TOS (from system)"
8. Click "Generate Test Questions"
9. Review and export

**Time**: ~10 minutes (5 min setup + 5 min generation)

### Option B: Upload TOS File (New Flow)

1. Go to **Generate TQS** tab
2. Select "Upload TOS from File"
3. Click file uploader, choose `.json` file
4. ✅ System validates automatically
5. Select test type (e.g., "Multiple Choice")
6. Set points per item (default 1.0)
7. Click "Confirm TOS Source"
8. Click "Generate Test Questions"
9. Review and export

**Time**: ~5 minutes (1 min setup + 4 min generation)

**Advantage**: Skip TOS creation steps if you already have one!

---

## Example 1: Simple Biology Quiz (JSON Format)

### Create the TOS file

Save as `biology_101.json`:

```json
{
  "learning_outcomes": [
    {
      "id": 0,
      "text": "Understand the photosynthesis process"
    },
    {
      "id": 1,
      "text": "Explain cellular respiration"
    }
  ],
  "bloom_distribution": {
    "Remember": 30,
    "Understand": 40,
    "Apply": 20,
    "Analyze": 10,
    "Evaluate": 0,
    "Create": 0
  },
  "tos_matrix": {
    "Remember": {
      "0": 3,
      "1": 3
    },
    "Understand": {
      "0": 4,
      "1": 4
    },
    "Apply": {
      "0": 2,
      "1": 2
    },
    "Analyze": {
      "0": 1,
      "1": 1
    },
    "Evaluate": {
      "0": 0,
      "1": 0
    },
    "Create": {
      "0": 0,
      "1": 0
    }
  },
  "metadata": {
    "course_code": "BIO101",
    "course_title": "Biology Fundamentals",
    "exam_term": "Midterm"
  }
}
```

### Upload and Generate

1. Go to **Generate TQS** tab
2. Select "Upload TOS from File"
3. Upload `biology_101.json`

**System shows**:
- ✅ Learning Outcomes: 2
- ✅ Total Items: 20
- ✅ File: biology_101.json
- ✅ Bloom Distribution: Remember 30%, Understand 40%, etc.

4. Select test type: **"Multiple Choice"**
5. Set points per item: **1.0**
6. Click "Confirm TOS Source"
7. Click "Generate Test Questions"

**Result**: 20 multiple choice questions, each worth 1 point, distributed across outcomes and Bloom levels

---

## Example 2: Mixed Assessment (Advanced)

### TOS File with Multiple Question Types

For a more realistic exam with mixed question types:

```json
{
  "learning_outcomes": [
    {
      "id": 0,
      "text": "Identify mathematical formulas",
      "hours": 1.0
    },
    {
      "id": 1,
      "text": "Apply formulas to word problems",
      "hours": 2.5
    },
    {
      "id": 2,
      "text": "Analyze mathematical proofs",
      "hours": 2.0
    }
  ],
  "bloom_distribution": {
    "Remember": 20,
    "Understand": 30,
    "Apply": 30,
    "Analyze": 15,
    "Evaluate": 4,
    "Create": 1
  },
  "tos_matrix": {
    "Remember": {
      "0": 2,
      "1": 0,
      "2": 0
    },
    "Understand": {
      "0": 1,
      "1": 2,
      "2": 0
    },
    "Apply": {
      "0": 1,
      "1": 3,
      "2": 1
    },
    "Analyze": {
      "0": 0,
      "1": 1,
      "2": 2
    },
    "Evaluate": {
      "0": 0,
      "1": 0,
      "2": 1
    },
    "Create": {
      "0": 0,
      "1": 0,
      "2": 0
    }
  },
  "total_items": 15,
  "metadata": {
    "course_code": "MATH201",
    "course_title": "Calculus I",
    "exam_term": "Final"
  }
}
```

### Two Ways to Use This

#### Way 1: Single Question Type
1. Upload file
2. Select test type: **"Multiple Choice"**
3. Points per item: **1.0**
4. Generate → 15 MCQ questions, 15 points total

#### Way 2: Manual Mixed Format (Generate separately)
1. Upload file → 15 slots
2. Select "Multiple Choice", points 1.0 → Generate 10 MCQs
3. Upload again → Select "Essay", points 5.0 → Generate 5 essays
4. Combine in export

**Note**: For true mixed-type specification, use internal TOS generation with Question Type Distribution

---

## Example 3: From Excel/Word to JSON

### Starting With Excel TOS

You have Excel file like:

```
Learning Outcome          | Remember | Understand | Apply | Analyze | Evaluate | Create
Student Learning Skills   |     3    |     2      |   2   |    1    |     0    |   0
Content Mastery          |     2    |     3      |   2   |    1    |     1    |   0
Problem-Solving          |     1    |     1      |   3   |    2    |     1    |   1
```

### Convert to JSON

1. Open text editor or Python script
2. Create JSON structure:

```json
{
  "learning_outcomes": [
    {"id": 0, "text": "Student Learning Skills"},
    {"id": 1, "text": "Content Mastery"},
    {"id": 2, "text": "Problem-Solving"}
  ],
  "bloom_distribution": {
    "Remember": 27,
    "Understand": 27,
    "Apply": 27,
    "Analyze": 12,
    "Evaluate": 5,
    "Create": 2
  },
  "tos_matrix": {
    "Remember": {"0": 3, "1": 2, "2": 1},
    "Understand": {"0": 2, "1": 3, "2": 1},
    "Apply": {"0": 2, "1": 2, "2": 3},
    "Analyze": {"0": 1, "1": 1, "2": 2},
    "Evaluate": {"0": 0, "1": 1, "2": 1},
    "Create": {"0": 0, "1": 0, "2": 1}
  }
}
```

3. Save as `.json` file
4. Upload to SmartLesson TQS tab

**Tool Recommendation**: [JSON Online Editor](https://jsoncrack.com/) for visual validation

---

## Walkthrough: Step-by-Step (Screenshots Described)

### Step 1: Select TOS Source

**You See**:
```
Generate Test Questions (TQS)

Generate actual test questions from your exam blueprint using AI.
Each question is tailored to the learning outcome and Bloom's level.

📋 Step 1: Select TOS Source

( ) Use Generated TOS (from system)
( ) Upload TOS from File
```

**Choose**: ◉ Upload TOS from File

### Step 2: Upload File

**You See**:
```
📤 Upload TOS File
Supported formats: JSON, PDF, DOCX

[Choose TOS file] [Browse...]
```

**Action**: Click "Browse" → Select `biology_101.json` → Upload

### Step 3: File Validation

**If Successful**:
```
✅ TOS is valid for TQS generation

📊 TOS Details (expandable)

Learning Outcomes | 2
Total Items       | 20
File              | biology_101.json
Format            | json

Learning Outcomes:
- Understand the photosynthesis process (ID: 0)
- Explain cellular respiration (ID: 1)

Bloom Distribution:
Remember    Understand    Apply    Analyze    Evaluate    Create
   30%          40%         20%       10%         0%          0%
```

### Step 4: Select Test Type

**You See**:
```
🎯 Step 2: Select Test Type

Question Type for Generated Questions:
[Dropdown: ▼ Multiple Choice ]
[Options: Multiple Choice, Essay, Problem Solving, Mixed]

Points per Item:
[Text Input: 1.0]

[✅ Confirm TOS Source]
```

**Choose**: 
- Test Type: "Multiple Choice"
- Points: 1.0
- Click "Confirm TOS Source"

### Step 5: Confirmation

**You See**:
```
✅ Created 20 question slots from TOS

🚀 Step 3: Generate Test Questions

📌 Using TOS from: Uploaded TOS
Number of slots: 20

[🚀 Generate Test Questions]
```

### Step 6: Generation

**Click "Generate Test Questions"** → Spinner shows:
```
⏳ Generating test questions (this may take 1-2 minutes)...
```

**After completion**:
```
✅ Generated 20 test questions

📊 Test Question Summary

Total Questions | 20
Total Points    | 20.0
Question Types  | 1
Bloom Levels    | 4

By Question Type
Type              | Count | Points
Multiple Choice   |  20   |  20.0

By Bloom Level
Bloom Level   | Count | Points
Remember      |   6   |   6.0
Understand    |   8   |   8.0
Apply         |   4   |   4.0
Analyze       |   2   |   2.0
```

### Step 7: Preview & Export

**See**:
```
👀 Question Preview

Q1: MCQ (1 pts) - Understand the photosynthesis...
[Expanded previewing actual question]

[Download buttons]
📥 Export TQS as JSON
```

---

## Troubleshooting Common Issues

### "File Upload Fails"

**Symptom**: Upload button is grayed out or won't accept file

**Solution**:
- Check file extension: `.json`, `.pdf`, or `.docx`
- Ensure file is not corrupted
- Try re-saving file with correct extension

### "JSON Parse Error"

**Symptom**: ❌ Failed to parse TOS file: Invalid JSON

**Solution**:
1. Validate JSON online: https://jsonlint.com/
2. Check for:
   - Missing commas between fields
   - Unclosed brackets `{`, `}`
   - Special characters not escaped
3. Use UTF-8 encoding
4. Copy from validator and save

### "Missing Bloom Levels"

**Symptom**: ❌ Missing required fields: Missing Bloom levels

**Solution**:
- Ensure all 6 levels in `bloom_distribution`:
  - Remember
  - Understand
  - Apply
  - Analyze
  - Evaluate
  - Create

Example:
```json
"bloom_distribution": {
  "Remember": 30,
  "Understand": 30,
  "Apply": 20,
  "Analyze": 10,
  "Evaluate": 5,
  "Create": 5
}
```

### "TOS Contains No Items"

**Symptom**: ❌ TOS contains no items (total_items = 0)

**Solution**:
- Check TOS matrix has non-zero values
- Ensure at least one outcome has items in one Bloom level

Example:
```json
"tos_matrix": {
  "Remember": {
    "0": 2,    // ← At least one value > 0
    "1": 0
  }
}
```

### "Outcome Not Found"

**Symptom**: ⚠️ Bloom levels with no questions

**Solution**:
- Distribute items across multiple Bloom levels
- Avoid leaving upper levels empty
- Ensure `tos_matrix` has entries for multiple Bloom levels

---

## Advanced Usage

### Using Python to Generate JSON

```python
import json

tos_data = {
    "learning_outcomes": [
        {"id": i, "text": f"Learning Outcome {i+1}"}
        for i in range(5)
    ],
    "bloom_distribution": {
        "Remember": 30,
        "Understand": 30,
        "Apply": 20,
        "Analyze": 15,
        "Evaluate": 4,
        "Create": 1
    },
    "tos_matrix": {
        bloom: {str(i): 2 for i in range(5)}
        for bloom in ["Remember", "Understand", "Apply", "Analyze", "Evaluate", "Create"]
    }
}

# Save to file
with open("tos.json", "w") as f:
    json.dump(tos_data, f, indent=2)

print("✅ TOS JSON created: tos.json")
```

### Batch Processing

To process multiple TOS files:

```python
import os
from services.tos_file_parser import parse_tos_file

tos_folder = "./tos_files"
for filename in os.listdir(tos_folder):
    if filename.endswith(".json"):
        filepath = os.path.join(tos_folder, filename)
        with open(filepath, "rb") as f:
            success, result = parse_tos_file(
                f.read(),
                filename
            )
        if success:
            print(f"✅ {filename}: {result['total_items']} items")
        else:
            print(f"❌ {filename}: {result['error']}")
```

---

## Best Practices

### ✅ DO

- ✅ Use JSON format for production
- ✅ Validate JSON before uploading
- ✅ Keep outcome descriptions concise
- ✅ Distribute Bloom levels evenly
- ✅ Use sequential outcome IDs (0, 1, 2, ...)
- ✅ Test with small files first

### ❌ DON'T

- ❌ Don't use image-based PDFs (no OCR yet)
- ❌ Don't leave all upper Bloom levels empty
- ❌ Don't use special characters in outcome text
- ❌ Don't upload files >10MB
- ❌ Don't have gaps in outcome IDs (e.g., 0, 2, 5)

---

## FAQ

**Q: Can I upload a PDF TOS?**
A: Yes, if it contains a well-structured table. JSON is more reliable.

**Q: Can I edit TOS after uploading?**
A: Re-upload the corrected file. Previous upload is replaced.

**Q: Can I use both generated and uploaded TOS in one session?**
A: Yes, switch between tabs. They're separate operations.

**Q: How many questions will be generated?**
A: One per item in TOS matrix (sum of all cells).

**Q: Can I change points after upload?**
A: Yes, adjust "Points per Item" before clicking "Confirm TOS Source".

**Q: What happens to my uploaded TOS when I refresh?**
A: It's cleared. Refresh = fresh session.

**Q: Can I export both generated and uploaded TQS?**
A: Yes, both export to the same JSON format.

---

## Next Steps

1. **Try Example 1**: Download `biology_101.json` from this guide
2. **Upload to SmartLesson**: Go to Generate TQS tab
3. **Generate Questions**: Select "Multiple Choice", confirm, generate
4. **Review Output**: Check question quality, Bloom distribution
5. **Export**: Download as JSON
6. **Create Your Own**: Based on your course TOS

---

## Support

- **Issue?** Check [TOS_FILE_UPLOAD_GUIDE.md](TOS_FILE_UPLOAD_GUIDE.md) for detailed specifications
- **Integration details?** See [TQS_FILE_UPLOAD_INTEGRATION.md](TQS_FILE_UPLOAD_INTEGRATION.md)
- **Code examples?** Search `tos_file_parser.py`

**Happy question generating!** 🎉
