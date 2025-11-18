# Quick Reference Guide

## Running the Application

```bash
python class_roster_ui.py
```

The UI will show two independent sections:

## STAGE 1: Data Cleaning & Standardization

**Purpose:** Convert raw school data (various formats) → Standard Excel format

**Steps:**
1. Enter school format name (e.g., "School A", "School B", "Default")
2. Click "Browse..." next to "Raw Data File" → select your raw data
3. Click "Save As..." next to "Standardized Output" → choose where to save
4. Click "→ Clean & Standardize Data" button

**Output:**
- Standard Excel file with columns: CLASS, Teacher, Name
- All data normalized (trimmed, proper case)
- Ready for Stage 2

**Auto-Population:**
- When Stage 1 completes, it automatically fills Stage 2 input
- Suggests a filename for Stage 2 output

## STAGE 2: Split by Class

**Purpose:** Take standardized Excel file → Create separate sheet per class

**Steps:**
1. Use file from Stage 1 OR select any compatible Excel file
2. Click "Browse..." next to "Input File"
3. Click "Save As..." next to "Output File" → choose where to save
4. Click "→ Split by Class" button

**Output:**
- Excel file with one sheet per class
- Each sheet contains:
  - Students sorted alphabetically
  - Class name in column B
  - Teacher info in footer
  - Advisor row

## File Requirements

### Stage 1 Input (Raw School Data)
- Any format (the cleaning stage handles it)
- Just needs to have class, teacher, and student information

### Stage 2 Input (Standardized Data)
- Excel file with columns like:
  - "CLASS" or "Class" or "Class ID" etc.
  - "Teacher" or "TEACHER"
  - "Name" or "Student" or "STUDENT"
  - Column names are flexible (auto-detected)

## Adding New School Formats

### Quick Steps:

1. **Look at your data** in the raw file to understand what needs cleaning

2. **Open** `cleaning_stages.py` and add a new class:
   ```python
   class YourSchoolCleaningStage(DataCleaningStage):
       def process(self, data):
           ws = data.get("worksheet")
           # Your cleaning code here
           return data
       
       def get_stage_name(self):
           return "Your School Name"
   ```

3. **Register it** in `get_cleaning_only_pipeline()`:
   ```python
   if school_format.lower() == "your school":
       return ProcessingPipeline(stages=[YourSchoolCleaningStage()])
   ```

4. **Test** - Type "Your School" in the School Format field and use Stage 1

5. **Refine** - Adjust cleaning logic as needed

### Cleaning Examples

See `cleaning_examples.py` for templates and examples:
- ALL CAPS to Title Case
- Remove extra whitespace
- Remove special characters
- Custom header mapping
- And more...

## Troubleshooting

### "Could not find any of headers: ..."
**Problem:** Stage 2 can't find the required columns
**Solution:** 
- Check that your data has columns for: Class, Teacher, Name
- Check column spelling and capitalization
- Use Stage 1 to standardize the column names first

### File already exists error
**Problem:** Output file exists
**Solution:** Click "Yes" to overwrite OR choose a different filename

### No data in output sheets
**Problem:** Students aren't appearing in output
**Solution:**
- Check that Class and Name columns have data
- Make sure data starts from row 2 (row 1 should be headers)
- Run Stage 1 cleaning first

### Application crashes
**Problem:** Unexpected error
**Solution:**
- Check the error message in the Status Log
- Make sure your input file is valid Excel (.xlsx or .xls)
- Try a simpler test file first

## File Structure

```
pythonConverter/
├── class_roster_ui.py          ← Main application (run this)
├── cleaning_stages.py          ← Add your school formats here
├── cleaning_examples.py        ← Examples for reference
├── ARCHITECTURE.md             ← Full technical documentation
├── REFACTORING_SUMMARY.md      ← What changed and why
├── requirements.txt            ← Dependencies
└── README.md                   ← Setup instructions
```

## Key Features

✅ **Two Independent Stages**
- Use together: Raw data → Standardized → Split by class
- Use separately: Skip Stage 1 if you have standardized data

✅ **Auto-Population**
- Stage 1 output → automatically becomes Stage 2 input

✅ **Flexible Column Detection**
- Works with many variations: "CLASS" or "Class ID" or "Section", etc.

✅ **Duplicate Removal**
- Automatically removes duplicate students in each class

✅ **Sorted Output**
- Students automatically sorted alphabetically per class

✅ **Safe Overwrite Protection**
- Asks before overwriting existing files

✅ **Non-blocking UI**
- Progress updates in real-time
- Can't freeze the application

## Common Workflows

### Workflow 1: Clean raw data from School A
```
Raw Data File → [Browse] → school_a_data.xlsx
School Format → "School A"
Standardized Output → [Save As] → school_a_clean.xlsx
[Click Clean & Standardize]
✓ Done
```

### Workflow 2: Split standardized file by class
```
Input File → [Browse] → any_standardized.xlsx
Output File → [Save As] → output_by_class.xlsx
[Click Split by Class]
✓ Done (one sheet per class)
```

### Workflow 3: Full pipeline (raw → standardized → split)
```
Stage 1: Clean raw data
→ Output: data_clean.xlsx

Stage 2: Auto-populated with data_clean.xlsx
→ Click Split by Class
→ Output: data_by_class.xlsx
✓ Complete pipeline done
```

## Tips & Tricks

💡 **Test First**
- Start with a small test file before processing large files
- Verify output is correct

💡 **Check Output Immediately**
- Click "Open File?" after processing to review results
- Catch any issues early

💡 **Save Smart**
- Use descriptive filenames: `school_a_raw.xlsx`, `school_a_clean.xlsx`
- This helps track data through the pipeline

💡 **When in Doubt**
- Check `cleaning_examples.py` for examples
- Read `ARCHITECTURE.md` for technical details
- Look at error messages in Status Log

## Command Line Usage (Advanced)

For automation, you can use the pipeline directly:

```python
from class_roster_ui import ProcessingPipeline, ClassSplittingStage
from cleaning_stages import SchoolACleaningStage

# Just cleaning
pipeline = ProcessingPipeline(stages=[SchoolACleaningStage()])
success, msg, data = pipeline.execute("raw.xlsx", "clean.xlsx")

# Just splitting
pipeline = ProcessingPipeline(stages=[ClassSplittingStage()])
success, msg, data = pipeline.execute("clean.xlsx", "split.xlsx")

# Both stages
from class_roster_ui import DataCleaningStage
pipeline = ProcessingPipeline(stages=[
    SchoolACleaningStage(),
    ClassSplittingStage()
])
success, msg, data = pipeline.execute("raw.xlsx", "split.xlsx")
```

## Support

- **Error:** Check Status Log at the bottom of the application
- **Questions:** See `ARCHITECTURE.md` for technical details
- **Examples:** See `cleaning_examples.py` for implementation examples
- **Issues:** Review file format and error messages
