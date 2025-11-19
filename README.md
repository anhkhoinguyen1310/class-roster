# JSON-First Excel Processor

A smart Excel processing system that implements a **JSON-first approach** for handling complex, multi-format spreadsheet data.

## 🎯 Your Requested Workflow

The system now implements exactly what you requested:

1. **Scan all XLSX documents** (including multiple sheets) ✅
2. **Extract everything as JSON objects** ✅  
3. **Match to correct fields** ✅
4. **Return to correct XLSX file** ✅

## 🔄 How It Works

### Stage 1: JSON-First Data Processing
```
Raw Excel → JSON Extraction → Field Matching → Standardized Excel
```

1. **Universal Sheet Scanner**: Automatically processes all sheets in any Excel file
2. **Intelligent Field Detection**: Uses pattern matching to identify:
   - Student names (full name or first+last)
   - Class IDs/names
   - Teacher names
   - Grades
   - Advisors
3. **JSON Export**: Optionally saves intermediate JSON for inspection/debugging
4. **Standardized Output**: Creates clean Excel with consistent format

### Stage 2: Class Splitting (Optional)
```
Standardized Excel → Separate Sheets per Class
```

## 🚀 Quick Start

### Method 1: GUI Application
```bash
python class_roster_ui.py
```

1. Select "JSON-First Universal (Auto-detect fields)" mode
2. Choose your input Excel file
3. Optionally check "Export JSON for inspection"
4. Click "Clean & Standardize Data"

### Method 2: Demo Script
```bash
python json_processor_demo.py input_file.xlsx output_file.xlsx
```

### Method 3: Programmatic Usage
```python
from class_roster_ui import DataCleaningStage, ProcessingPipeline

# Create JSON-first pipeline
pipeline = ProcessingPipeline(stages=[
    DataCleaningStage(
        export_json=True,
        json_output_path="debug_output.json"
    )
])

# Process file
success, message, data = pipeline.execute(
    "input.xlsx", 
    "output.xlsx"
)
```

## 📊 Supported Input Formats

The JSON-first processor automatically handles:

- **Any Excel file structure** (no predefined format required)
- **Multiple sheets** (processes all data sheets automatically)
- **Various naming conventions** for:
  - Student names: "Name", "Student", "Full Name", "First Name" + "Last Name"
  - Classes: "Class", "Class ID", "Section", "Grade", "Homeroom"
  - Teachers: "Teacher", "Instructor", "Homeroom Teacher"

### Example Input Formats

#### Format 1: Simple Roster
| Name | Class | Teacher |
|------|-------|---------|
| John Doe | 6A | Ms. Smith |

#### Format 2: Split Names
| First Name | Last Name | Section | Instructor |
|------------|-----------|---------|------------|
| John | Doe | 7B | Mr. Johnson |

#### Format 3: Multi-Sheet (one sheet per grade)
- Sheet "6th Grade": Student data
- Sheet "7th Grade": Student data  
- Sheet "Schedule": Class-teacher mappings

## 📄 JSON Structure

When JSON export is enabled, you get detailed extraction data:

```json
{
  "extraction_summary": {
    "total_sheets": 3,
    "processed_sheets": ["6th Grade", "7th Grade"],
    "skipped_sheets": ["Instructions"]
  },
  "raw_data": {
    "6th Grade": {
      "headers": ["Name", "Class", "Teacher"],
      "rows": [["John Doe", "6A", "Ms. Smith"]],
      "metadata": {"total_rows": 25, "header_row": 1}
    }
  },
  "normalized_records": [
    {
      "student_name": "John Doe",
      "class_id": "6A", 
      "teacher": "Ms. Smith",
      "grade": "",
      "advisor": "",
      "source_sheet": "6th Grade"
    }
  ],
  "record_count": 150
}
```

## 🎛️ Processing Modes

### 1. JSON-First Universal ⭐ (Recommended)
- **Auto-detects** field types and formats
- Works with **any Excel structure**
- **Multi-sheet support**
- Smart field matching
- Optional JSON export

### 2. ROCL Fixed-Width
- Legacy support for ROCL format
- Fixed column positions
- Teacher schedule integration

### 3. Picture Day Format
- Multi-sheet grade-based structure
- Contact information handling
- Schedule mapping

### 4. Legacy ROCL + Advisor
- ROCL format with advisor column

## 🔧 Advanced Features

### Intelligent Field Matching
The system uses **two-pass matching**:
1. **Exact match**: "Name" matches "name"
2. **Substring match**: "Student Name" matches "name"

### Smart Name Processing
- **Title case conversion** for ALL CAPS names
- **Irish/Scottish name handling**: McDonald → McDonald
- **Apostrophe handling**: O'Connor → O'Connor

### Multi-Sheet Processing
- **Auto-detects** data vs non-data sheets
- Skips instruction/template sheets
- **Combines data** from multiple sheets
- Preserves source sheet information

### Error Handling
- **Graceful degradation**: Works even with missing fields
- **Validation**: Requires at least student name
- **Detailed logging**: Shows what was processed

## 📁 File Structure

```
pythonConverter/
├── class_roster_ui.py          # Main GUI application
├── cleaning_stages.py          # ROCL-specific processors  
├── picture_day_cleaning_stage.py  # Picture Day processor
├── json_processor_demo.py      # Standalone demo
├── requirements.txt           # Dependencies
└── README.md                 # This file
```

## 🛠️ Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Run GUI
python class_roster_ui.py

# Or run demo
python json_processor_demo.py sample_data.xlsx output.xlsx
```

## 🔍 Debugging

### Enable JSON Export
Check "Export JSON for inspection" in the GUI to save intermediate data for debugging.

### View Processing Details
The JSON file contains:
- **Raw extraction data** from each sheet
- **Field mapping results** 
- **Normalized records**
- **Processing statistics**

### Common Issues
1. **No records found**: Check if student name column exists
2. **Wrong field mapping**: Review JSON export to see detected headers
3. **Missing teachers**: May indicate no teacher column detected

## 🎯 Benefits of JSON-First Approach

1. **Universal Compatibility**: Works with any Excel structure
2. **Transparency**: Full visibility into data processing
3. **Debuggability**: JSON export shows exactly what happened
4. **Flexibility**: Easy to extend for new formats
5. **Reliability**: Graceful handling of missing/malformed data

## 🚀 Next Steps

The system is now ready for your **universal Excel processing workflow**. The JSON-first approach ensures that regardless of input format, you get:

- ✅ Complete data extraction
- ✅ Intelligent field matching  
- ✅ Standardized output
- ✅ Full debugging visibility

Try it with your Excel files and check the JSON output to see how it processes your specific data format!