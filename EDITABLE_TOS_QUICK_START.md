# Quick Start: Enhanced Generate TQS with Editable TOS

**This guide shows you how to use the new editable TOS features in the Generate TQS tab.**

---

## 🚀 Quick Overview

### What's New?
You can now **upload a TOS file, edit it, and configure question types** all in one place!

### New Workflow:
```
1. Upload TOS file
2. ✨ Edit learning outcomes (NEW)
3. ✨ Configure test types flexibly (NEW)
4. Generate test questions
5. Review and export
```

---

## 📋 Step-by-Step Guide

### Step 1: Go to Generate TQS Tab

In the **Assessment Generator** section, click the **"Generate TQS"** sub-tab.

### Step 2: Select TOS Source

You have two options:

**Option A: Use Generated TOS (Original Workflow)**
- Select radio button: "Use Generated TOS (from system)"
- Jump to Step 5 (skip outcome editing)

**Option B: Upload TOS File (New Workflow)** ⭐
- Select radio button: "Upload TOS from File"
- Click the file upload area
- Choose your TOS file (JSON, XLSX, DOCX, or PDF)
- Wait for validation (takes 1-2 seconds)

### Step 3: Edit Learning Outcomes (NEW!)

After uploading, see your outcomes in an editable table:

```
Outcome Text                          | Hours | Delete
──────────────────────────────────────┼───────┼────────
Introduction to Python Basics         │   3   │  ❌
OOP and Design Patterns                │   4   │  ❌
Advanced Python Topics                │   2   │  ❌
```

**What you can do:**
- ✅ View all outcomes from your TOS
- ✅ Delete outcomes you want to exclude (click ❌)
- ✅ See total items update automatically
- ✅ Matrix is updated to maintain consistency

**Example:** If you delete "OOP and Design Patterns", the test matrix automatically removes that column and recalculates totals.

### Step 4: Configure Test Types (NEW!)

Choose how to structure your test:

#### Option A: Single Question Type
- Select one type: **MCQ**, **True or False**, **Essay**, **Short Answer**, or **Problem Solving**
- Set **Points per Item** (0.5 to 10 points)
- All questions will be this type

**Example:**
```
Question Type: [MCQ              ▼]
Points per Item: [1.0]

Result: 60 questions, all MCQ, 1 point each = 60 total points
```

#### Option B: Mixed Question Types ⭐
- Specify how many items of each type
- Set different points for each type
- System validates total matches your TOS

**Example:**
```
MCQ                    Items: [20]  Points/Item: [1.0]
Essay                  Items: [10]  Points/Item: [3.0]  
Short Answer           Items: [15]  Points/Item: [1.5]
True or False          Items: [10]  Points/Item: [0.5]
Problem Solving        Items: [5]   Points/Item: [4.0]

✅ Distribution valid: 60 items across 5 types
   Total: 107.5 points
```

**Validation:**
- ✅ Green: Distribution matches TOS total
- ❌ Red: Distribution doesn't match total
- ⚠️ Yellow: No items assigned yet

### Step 5: Generate Test Questions

Click the purple button: **"🚀 Generate Test Questions"**

**What happens:**
1. System converts your TOS to test slots
2. Assigns question types as configured
3. Sends to Gemini AI for generation
4. Shows progress (1-2 minutes)

**Success Message:**
```
✅ Generated 60 test questions from Uploaded TOS
```

### Step 6: Review and Export

After generation:
- **📊 View statistics** by type and Bloom level
- **👀 Preview questions** (first 3-5 questions shown)
- **💾 Export as JSON** for use in assessment tools
- **🖨️ Print or share** results

---

## 💡 Common Scenarios

### Scenario 1: Exclude Unnecessary Outcomes
```
1. Upload complete course TOS (30 outcomes)
2. Edit: Delete outcomes not needed for this exam
3. System updates matrix automatically
4. Configure single type: MCQ
5. Generate TQS with only relevant outcomes
```

### Scenario 2: Mixed Question Assessment
```
1. Upload TOS
2. Skip outcome editing
3. Configure mixed types:
   - 10 MCQ (quick knowledge check)
   - 5 Essay (deep understanding)
   - 3 Problem Solving (application)
4. Generate TQS with diverse question types
```

### Scenario 3: Weighted Assessment
```
1. Upload TOS (40 items total)
2. Delete 2 outcomes (now 35 items)
3. Configure mixed with different points:
   - Quick Quiz: 25 items × 0.5 pts = 12.5 pts
   - Concept Check: 7 items × 2.0 pts = 14 pts
   - Application: 3 items × 3.0 pts = 9 pts
   - Total: 35.5 points for weighted scoring
4. Generate and use in assessment
```

---

## ⚠️ Important Notes

### Understanding the Matrix Update
When you delete an outcome:
- ✅ It's removed from your learning outcomes list
- ✅ That column is removed from the Bloom matrix
- ✅ Total item count is recalculated
- ✅ All affected data stays consistent

### Distribution Must Match
For mixed types configuration:
- ❌ Total items in distribution MUST equal TOS total
- ❌ Can't have 60 items but only assign 55
- ✅ System validates in real-time and shows errors

### No API Key?
If you see: `❌ GEMINI_API_KEY environment variable is not set`
- Check your system configuration
- Ensure API key is set in your environment
- Restart the application

---

## 🎯 Best Practices

### 1. **Review Your TOS Before Editing**
   - Check outcomes in the "TOS Details" section
   - Understand your current matrix structure
   - Know what you want to include

### 2. **One Edit at a Time**
   - Delete one outcome at a time
   - Check that totals update correctly
   - Avoid deleting multiple outcomes at once

### 3. **Plan Your Distribution**
   - Know your total items first
   - Decide type split in advance
   - Test with small numbers first

### 4. **Use Single Type for Consistency**
   - Use Single Mode for uniform tests
   - All questions same type = easier grading
   - Use Mixed Mode only when needed

### 5. **Keep Points Consistent**
   - Round to nearest 0.5
   - Document your point scheme
   - Keep total points reasonable (30-100)

---

## 🔍 Troubleshooting

### Q: File Upload Shows No File Uploader
**A:** You selected "Use Generated TOS" instead of "Upload TOS from File"  
**Fix:** Click the "Upload TOS from File" radio button

### Q: After Deleting an Outcome, Totals Are Wrong
**A:** This shouldn't happen - system auto-recalculates
**Fix:** Refresh the page (F5) and try again

### Q: "Distribution items must equal TOS total"
**A:** Your item counts don't match  
**Fix:** Add up all items - should be exactly equal to TOS total

### Q: Items Added But Test Type Not Found
**A:** You configured but didn't save with button click
**Fix:** Ensure test type selection is completed before generating

### Q: Generation Keeps Failing
**A:** Multiple possible causes
**Fix:** 
1. Check API key is set
2. Verify TOS is valid
3. Check internet connection
4. Try with smaller number of items first

---

## 📚 More Information

- **Full Documentation**: See [EDITABLE_TOS_ENHANCEMENT.md](EDITABLE_TOS_ENHANCEMENT.md)
- **TOS Format Guide**: See [TOS_FILE_UPLOAD_GUIDE.md](TOS_FILE_UPLOAD_GUIDE.md)
- **Questions?**: Check troubleshooting section above

---

## ✨ Key Improvements Over Previous Version

| Feature | Before | After |
|---------|--------|-------|
| Edit outcomes | ❌ Not possible | ✅ Delete outcomes |
| Test types | Limited | ✅ 5 types available |
| Single vs Mixed | Not supported | ✅ Both supported |
| Point configuration | Fixed | ✅ Item-by-item |
| Validation | Basic | ✅ Real-time feedback |
| Error messages | Generic | ✅ Specific & helpful |

---

## 🎉 You're Ready!

You now have full control over:
1. ✅ Which outcomes to include
2. ✅ How to structure your test questions
3. ✅ How to weight different question types

**Start generating better assessments today!**

---

**Last Updated**: February 17, 2026  
**Status**: Ready for Use
