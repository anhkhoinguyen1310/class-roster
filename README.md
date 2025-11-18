# Class Roster Generator - Complete Documentation Index

## 📋 Project Overview

A two-stage Python application for processing school roster data:
1. **Stage 1:** Clean raw data from various school formats → standardized Excel
2. **Stage 2:** Split standardized Excel by class → separate sheets per class

Each stage is **completely independent** and can be used alone or together.

---

## 📁 Project Files

### Core Application Files
- **`class_roster_ui.py`** (28 KB)
  - Main application entry point
  - Contains all pipeline logic and UI
  - Run this to start the application: `python class_roster_ui.py`

- **`cleaning_stages.py`** (4.4 KB)
  - School-specific cleaning implementations
  - Add your school formats here

- **`requirements.txt`**
  - Dependencies: PyQt6, openpyxl

### Documentation Files

#### 🚀 Quick Start (Start Here!)
- **`QUICK_START.md`** (6.8 KB)
  - How to run the application
  - Step-by-step usage for both stages
  - Common workflows and troubleshooting
  - **Best for:** Learning how to use the application

#### 📚 Architecture & Design
- **`ARCHITECTURE.md`** (9.6 KB)
  - Complete technical architecture
  - Data flow and pipeline design
  - How to add new school formats
  - Testing examples
  - **Best for:** Understanding the system design

#### 🔄 Migration Guide
- **`REFACTORING_SUMMARY.md`** (6.4 KB)
  - What changed from the old version
  - Before/after comparison
  - Key improvements
  - **Best for:** Understanding the refactoring

#### 💡 Implementation Examples
- **`cleaning_examples.py`** (12 KB)
  - 6 complete examples of cleaning implementations
  - Template for your own implementations
  - Debug helper for understanding data
  - **Best for:** Learning how to implement school-specific cleaning

#### 📖 This File
- **`README.md`** (this file)
  - Overview and navigation guide

---

## 🎯 Quick Navigation

### I want to...

#### ...use the application
→ Read **QUICK_START.md** → Run `python class_roster_ui.py`

#### ...understand how it works
→ Read **ARCHITECTURE.md** (technical design)

#### ...add a new school format
→ Read **cleaning_examples.py** → Copy template → Customize

#### ...see what changed
→ Read **REFACTORING_SUMMARY.md**

#### ...debug my data
→ Use the "Debug: Print Data" stage in `cleaning_examples.py`

#### ...test the pipeline programmatically
→ See "Testing" section in **ARCHITECTURE.md**

---

## 🚀 Quick Start

### Installation

```bash
cd pythonConverter
pip install -r requirements.txt
```

### Running the Application

```bash
python class_roster_ui.py
```

### Using Stage 1 (Data Cleaning)

1. Enter school format: "School A" (or "Default")
2. Browse to raw data file
3. Choose output location for cleaned file
4. Click "→ Clean & Standardize Data"

### Using Stage 2 (Class Splitting)

1. Browse to standardized Excel file
2. Choose output location
3. Click "→ Split by Class"

---

## 📊 Architecture Overview

```
┌─────────────────────────────────────┐
│ STAGE 1: Data Cleaning              │
│                                     │
│ Raw School Data (any format)        │
│         ↓                           │
│ DataCleaningStage (customizable)    │
│         ↓                           │
│ Standardized Excel Output           │
│ (Columns: CLASS, Teacher, Name)     │
└─────────────────────────────────────┘
              ↓
     [Auto-populated to Stage 2]
              ↓
┌─────────────────────────────────────┐
│ STAGE 2: Class Splitting            │
│                                     │
│ Standardized Excel File             │
│         ↓                           │
│ ClassSplittingStage (generic)       │
│         ↓                           │
│ Output Excel (split by class)       │
│ (One sheet per class)               │
└─────────────────────────────────────┘
```

### Key Components

| Component | Purpose | Customizable |
|-----------|---------|--------------|
| `PipelineStage` | Base class for stages | No (abstract) |
| `DataCleaningStage` | Clean raw data | ✅ Yes (override per school) |
| `ClassSplittingStage` | Split by class | No (generic) |
| `ProcessingPipeline` | Orchestrates stages | No (auto-manages) |
| `ProcessThread` | Async processing | No (internal) |
| `ClassRosterGUI` | User interface | No (but extensible) |

---

## 📝 File Descriptions

### class_roster_ui.py (764 lines)

**Sections:**
1. **Pipeline Stages** (lines 15-175)
   - `PipelineStage` (abstract base)
   - `DataCleaningStage` (override for schools)
   - `ClassSplittingStage` (generic, reusable)

2. **Processing Pipeline** (lines 177-246)
   - `ProcessingPipeline` class
   - Orchestrates multiple stages
   - Handles file I/O

3. **UI Thread** (lines 248-268)
   - `ProcessThread` (QThread)
   - Async processing without freezing UI

4. **GUI** (lines 270-764)
   - `ClassRosterGUI` (QMainWindow)
   - Two independent stage sections
   - File browsing and processing

### cleaning_stages.py (169 lines)

**Contains:**
- `SchoolACleaningStage` (example)
- `SchoolBCleaningStage` (example)
- `get_cleaning_only_pipeline()` (factory for Stage 1)
- `get_cleaning_pipeline()` (factory for both stages)

### cleaning_examples.py (331 lines)

**Contains 6 examples:**
1. ALL CAPS and leading spaces
2. Extra whitespace and special characters
3. Duplicate detection
4. Merged cells and complex structure
5. Comma-separated names
6. Custom header mapping

Plus a **Debug helper** and **Template** for your own implementations.

---

## 🔧 Customization Guide

### Adding a New School Format

**Step 1:** Create cleaning stage in `cleaning_stages.py`
```python
class MySchoolCleaningStage(DataCleaningStage):
    def process(self, data):
        ws = data.get("worksheet")
        # Your cleaning logic here
        return data
    
    def get_stage_name(self):
        return "My School Name"
```

**Step 2:** Register in `get_cleaning_only_pipeline()`
```python
if school_format.lower() == "my school":
    return ProcessingPipeline(stages=[MySchoolCleaningStage()])
```

**Step 3:** Use in UI
- Enter "My School" in School Format field
- Follow Stage 1 workflow

### Understanding Your Data

Use `DebugCleaningStage` from `cleaning_examples.py`:
```python
pipeline = ProcessingPipeline(stages=[DebugCleaningStage()])
pipeline.execute("raw.xlsx", "debug.xlsx")
```

This prints:
- First 10 rows of data
- Raw cell values with types
- Helps you understand what to clean

---

## 💡 Common Workflows

### Workflow 1: Single School Format
```
Raw Data (School A) 
    → Stage 1 (SchoolACleaningStage)
    → Standardized.xlsx
    → Stage 2 (ClassSplittingStage)
    → Output_by_class.xlsx ✓
```

### Workflow 2: Already Standardized Data
```
Standardized.xlsx
    → Stage 2 (skip Stage 1)
    → Output_by_class.xlsx ✓
```

### Workflow 3: Multiple Schools
```
School A Data → Stage 1 (SchoolACleaningStage) → A_standardized.xlsx → Stage 2 → A_by_class.xlsx
School B Data → Stage 1 (SchoolBCleaningStage) → B_standardized.xlsx → Stage 2 → B_by_class.xlsx
```

---

## 🧪 Testing

### Test Stage 1 Only
```python
from class_roster_ui import ProcessingPipeline
from cleaning_stages import SchoolACleaningStage

pipeline = ProcessingPipeline(stages=[SchoolACleaningStage()])
success, msg, data = pipeline.execute("raw.xlsx", "clean.xlsx")
```

### Test Stage 2 Only
```python
from class_roster_ui import ProcessingPipeline, ClassSplittingStage

pipeline = ProcessingPipeline(stages=[ClassSplittingStage()])
success, msg, data = pipeline.execute("clean.xlsx", "split.xlsx")
```

### Test Both Stages
```python
from class_roster_ui import ProcessingPipeline
from cleaning_stages import SchoolACleaningStage, ClassSplittingStage

pipeline = ProcessingPipeline(stages=[
    SchoolACleaningStage(),
    ClassSplittingStage()
])
success, msg, data = pipeline.execute("raw.xlsx", "split.xlsx")
```

---

## 📋 Requirements

- Python 3.8+
- PyQt6 >= 6.6.0
- openpyxl >= 3.1.0

Install with:
```bash
pip install -r requirements.txt
```

---

## 🚨 Troubleshooting

### Common Issues

| Issue | Solution |
|-------|----------|
| "Could not find any of headers..." | Check column names in input file |
| No students in output | Verify data starts from row 2 (row 1 = headers) |
| Output file not created | Check file permissions and available disk space |
| Application freezes | Files are being processed in background; wait for completion |

### Debug Tips

1. **Check Status Log** - Error messages appear there
2. **Use DebugCleaningStage** - See what data looks like
3. **Test with small files** - Easier to debug
4. **Read ARCHITECTURE.md** - Understand the flow

---

## 📞 Getting Help

1. **Quick questions?** → Check **QUICK_START.md**
2. **How does it work?** → Read **ARCHITECTURE.md**
3. **How to add school?** → See **cleaning_examples.py**
4. **What changed?** → Read **REFACTORING_SUMMARY.md**
5. **Technical details?** → Review source code in `class_roster_ui.py`

---

## 🔐 Data Safety Features

✅ **File Overwrite Protection**
- Asks confirmation before overwriting existing files

✅ **Error Recovery**
- Detailed error messages in Status Log
- No partial outputs on error

✅ **Non-blocking UI**
- Can cancel/close during processing
- Progress updates in real-time

✅ **Data Validation**
- Auto-detects column names
- Handles missing/null values gracefully

---

## 🎓 Learning Resources

### For Beginners
1. Start with **QUICK_START.md**
2. Run the application with sample data
3. Review output to understand the transformation

### For Developers
1. Read **ARCHITECTURE.md** for design
2. Study `class_roster_ui.py` for implementation
3. Look at `cleaning_examples.py` for patterns
4. Implement your own school format

### For Troubleshooting
1. Check error message in Status Log
2. Use Debug stage to inspect data
3. Review relevant documentation section
4. Test with simplified sample data

---

## 📜 Version History

### Current Version (Refactored)
- Two independent stages (Cleaning + Splitting)
- Flexible UI with auto-population
- School-specific customization
- Improved error handling
- Non-blocking async processing

### Previous Version
- Single workflow (only splitting)
- Limited school format support
- Basic error handling

---

## 📄 License & Credits

Built for processing school roster data with extensible architecture for multiple school formats.

---

**Last Updated:** November 18, 2025

For the latest version and updates, check the project files.
