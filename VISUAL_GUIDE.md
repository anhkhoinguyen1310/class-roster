# Visual Architecture Guide

## UI Layout

```
╔════════════════════════════════════════════════════════════════════════════╗
║                  CLASS ROSTER GENERATOR - TWO STAGE PIPELINE               ║
╠════════════════════════════════════════════════════════════════════════════╣
║                                                                            ║
║  ┌─ STAGE 1: DATA CLEANING & STANDARDIZATION ──────────────────────────┐  ║
║  │                                                                     │  ║
║  │  School Format:        [Default                        ]           │  ║
║  │  Raw Data File:        [/path/to/raw.xlsx ] [Browse...]           │  ║
║  │  Standardized Output:  [/path/to/std.xlsx ] [Save As...]          │  ║
║  │                                                                     │  ║
║  │  ┌────────────────────────────────────────────────────────────┐   │  ║
║  │  │ → Clean & Standardize Data                                 │   │  ║
║  │  └────────────────────────────────────────────────────────────┘   │  ║
║  │                                                                     │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─────────────────────────────────────────────────────────────────────┐  ║
║  │                            ↓                                       │  ║
║  │                   Auto-populated to Stage 2                       │  ║
║  │                            ↓                                       │  ║
║  └─────────────────────────────────────────────────────────────────────┘  ║
║                                                                            ║
║  ┌─ STAGE 2: SPLIT BY CLASS ──────────────────────────────────────────┐   ║
║  │                                                                     │   ║
║  │  Input File:    [/path/to/std.xlsx ] [Browse...]                 │   ║
║  │  Output File:   [/path/to/split.xlsx] [Save As...]               │   ║
║  │                                                                     │   ║
║  │  Required columns: CLASS/Class ID, Teacher, Name/Student          │   ║
║  │                                                                     │   ║
║  │  ┌────────────────────────────────────────────────────────────┐   │   ║
║  │  │ → Split by Class                                           │   │   ║
║  │  └────────────────────────────────────────────────────────────┘   │   ║
║  │                                                                     │   ║
║  └─────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
║  ┌─ STATUS LOG ───────────────────────────────────────────────────────┐   ║
║  │                                                                     │   ║
║  │ Ready. Select files to begin processing.                          │   ║
║  │                                                                     │   ║
║  └─────────────────────────────────────────────────────────────────────┘   ║
║                                                                            ║
╚════════════════════════════════════════════════════════════════════════════╝
```

---

## Data Flow

### Option A: Full Pipeline (Raw → Standardized → Split by Class)

```
┌─────────────────────┐
│  Raw School Data    │
│  (various formats)  │
└──────────┬──────────┘
           │
           ├─── School A data
           ├─── School B data
           └─── etc...
           │
    ┌──────▼──────┐
    │   STAGE 1   │
    │             │
    │ DataCleaning│
    │  (Custom)   │
    │             │
    └──────┬──────┘
           │
    ┌──────▼──────────────────┐
    │  Standardized Excel     │
    │  ┌────────────────────┐ │
    │  │ CLASS │ Teacher │ │ │
    │  ├───────┼─────────┼─┤ │
    │  │08/108 │ Jesika  │ │ │
    │  │070110 │ Iris    │ │ │
    │  └────────────────────┘ │
    └──────┬──────────────────┘
           │
    ┌──────▼──────┐
    │   STAGE 2   │
    │             │
    │ClassSplitting
    │  (Generic)  │
    │             │
    └──────┬──────┘
           │
    ┌──────▼──────────────────────┐
    │ Output Excel (By Class)     │
    │ ┌──────────────────────────┐│
    │ │ Sheet: "Class 08/108"    ││
    │ │ ┌─────────────────────┐  ││
    │ │ │ Student  │ Class   │  ││
    │ │ ├──────────┼─────────┤  ││
    │ │ │ Breanna  │ 08/108  │  ││
    │ │ │ Daniel   │ 08/108  │  ││
    │ │ │ Iris     │ 08/108  │  ││
    │ │ └─────────────────────┘  ││
    │ │ Teacher: Jesika Rosen   ││
    │ │                         ││
    │ │ Sheet: "Class 070110"   ││
    │ │ [students for 070110]   ││
    │ └──────────────────────────┘│
    └─────────────────────────────┘
```

### Option B: Stage 2 Only (Already Standardized Data)

```
┌──────────────────────┐
│ Standardized Excel   │
│ (from Stage 1 or     │
│  external source)    │
└──────────┬───────────┘
           │
    ┌──────▼──────┐
    │   STAGE 2   │
    │             │
    │ClassSplitting
    │  (Generic)  │
    │             │
    └──────┬──────┘
           │
    ┌──────▼──────────────────┐
    │ Output Excel (By Class) │
    │ [one sheet per class]   │
    └─────────────────────────┘
```

---

## Code Architecture

### Class Hierarchy

```
PipelineStage (abstract base class)
├── DataCleaningStage
│   ├── SchoolACleaningStage (example)
│   ├── SchoolBCleaningStage (example)
│   └── [Your custom stages]
│
└── ClassSplittingStage (fixed, generic)

ProcessingPipeline
└── Orchestrates multiple PipelineStage instances
    └── Handles file I/O
        └── Manages error handling

ProcessThread (QThread)
└── Runs ProcessingPipeline asynchronously
    └── Emits progress signals to UI

ClassRosterGUI (QMainWindow)
├── Stage 1 Section
│   └── Handlers: browse_raw_source(), browse_std_output(), process_cleaning()
└── Stage 2 Section
    └── Handlers: browse_split_source(), browse_split_output(), process_splitting()
```

---

## File Organization

```
pythonConverter/
│
├── 📄 class_roster_ui.py (764 lines)
│   ├── [15-175]   Pipeline Stages
│   │   ├── PipelineStage
│   │   ├── DataCleaningStage
│   │   └── ClassSplittingStage
│   ├── [177-246]  ProcessingPipeline
│   ├── [248-268]  ProcessThread
│   └── [270-764]  ClassRosterGUI
│
├── 📄 cleaning_stages.py (169 lines)
│   ├── SchoolACleaningStage
│   ├── SchoolBCleaningStage
│   ├── get_cleaning_only_pipeline()
│   ├── get_cleaning_pipeline()
│   └── get_school_x_pipeline()
│
├── 📄 cleaning_examples.py (331 lines)
│   ├── 6 Example Implementations
│   ├── DebugCleaningStage
│   └── YourSchoolTemplate
│
├── 📚 Documentation
│   ├── README.md (overview & navigation)
│   ├── QUICK_START.md (how to use)
│   ├── ARCHITECTURE.md (technical details)
│   ├── REFACTORING_SUMMARY.md (what changed)
│   └── [THIS FILE] VISUAL_GUIDE.md
│
└── ⚙️ Configuration
    └── requirements.txt
```

---

## Data Structure in Pipeline

### Data Dictionary Flow

```
Input (raw Excel file)
        ↓
┌─────────────────────────────────────┐
│ data = {                            │
│   "workbook": Workbook,  (input)    │
│   "worksheet": Worksheet (input)    │
│ }                                   │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ DataCleaningStage.process(data)     │
│   [modifies worksheet in-place]     │
│   [returns same data structure]     │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ data = {                            │
│   "workbook": Workbook (modified),  │
│   "worksheet": Worksheet (modified) │
│ }                                   │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ ClassSplittingStage.process(data)   │
│   [reads worksheet]                 │
│   [creates new workbook]            │
│   [adds data to structure]          │
└─────────────────────────────────────┘
        ↓
┌─────────────────────────────────────┐
│ data = {                            │
│   "workbook": (original),           │
│   "worksheet": (original),          │
│   "output_workbook": Workbook (NEW) │
│   "class_groups": dict (NEW)        │
│   "row_count": int (NEW)            │
│ }                                   │
└─────────────────────────────────────┘
        ↓
ProcessingPipeline.execute() saves output_workbook to disk
```

---

## Processing Sequence

### Stage 1: Data Cleaning

```
Load raw file
    ↓
Read worksheet
    ↓
DataCleaningStage.process()
├─ Normalize whitespace
├─ Fix character encoding
├─ Validate data
└─ Handle missing values
    ↓
Save standardized file
    ↓
Done
```

### Stage 2: Class Splitting

```
Load standardized file
    ↓
Read headers (row 1)
    ↓
Find column indices
├─ CLASS/Class/Class ID
├─ Teacher/TEACHER
└─ Name/Student/STUDENT
    ↓
Group students by class
├─ Create new workbook
├─ Add sheet per class
├─ Add students to sheets
└─ Add teacher/advisor info
    ↓
Save split file
    ↓
Done
```

---

## Column Detection Logic

### Stage 2 Input Columns (Flexible Detection)

```
Input Columns Can Be:
├─ CLASS column: "CLASS", "Class", "Class Section ID", 
│               "Class Section", "Class ID", "Section"
├─ TEACHER column: "Teacher", "TEACHER", "Instructor",
│                 "Instructor Name"
└─ NAME column: "Name", "Student", "STUDENT", "Pupil",
               "Pupil ID", "Student Name"

Detection Algorithm:
├─ Normalize all headers to lowercase
├─ Strip whitespace
├─ Look for exact matches OR partial matches
└─ Raise error if not found
```

---

## Error Handling Flow

```
Pipeline Execution
    ↓
Try:
├─ Load input file
├─ Run each stage
├─ Save output
└─ Return success
    ↓
Except (any error):
├─ Capture exception
├─ Generate error message
├─ Return failure + message
└─ Display in Status Log
    ↓
UI catches result:
├─ If success: show info box, offer to open
└─ If failure: show error box with details
```

---

## Threading Model

```
User clicks button
    ↓
Main UI Thread (QMainWindow)
    ├─ Create ProcessThread
    ├─ Connect signals
    └─ Start thread
    ↓
Background Thread (ProcessThread)
├─ Run pipeline.execute()
├─ Emit progress signals
├─ Return result
└─ Stop thread
    ↓
Main UI Thread
├─ Receive finished signal
├─ Show result dialog
└─ Re-enable buttons

Result: UI stays responsive!
```

---

## Customization Points

### Add New School Format

```
1. Create cleaning stage:
   class YourSchoolCleaningStage(DataCleaningStage):
       def process(self, data):
           # Your logic here
           return data

2. Register in factory:
   if school_format.lower() == "your school":
       return ProcessingPipeline(stages=[YourSchoolCleaningStage()])

3. Use in UI:
   Enter "Your School" in School Format field
```

### Extend Pipeline with More Stages

```
# Add validation stage between cleaning and splitting
from class_roster_ui import DataCleaningStage, ClassSplittingStage

class DataValidationStage(PipelineStage):
    def process(self, data):
        ws = data.get("worksheet")
        # Check for data quality
        # Raise errors if validation fails
        return data
    
    def get_stage_name(self):
        return "Data Validation"

# Use custom pipeline:
pipeline = ProcessingPipeline(stages=[
    SchoolACleaningStage(),
    DataValidationStage(),
    ClassSplittingStage()
])
```

---

## Performance Considerations

### Input File Size

```
< 1,000 rows  → Instant (< 1 sec)
1,000-10,000 rows  → Fast (1-5 sec)
10,000-50,000 rows → Moderate (5-30 sec)
50,000+ rows → Slow (30+ sec)

Note: All processing happens in background thread
      UI remains responsive regardless of file size
```

### Memory Usage

```
In-memory storage:
├─ Input workbook: proportional to file size
├─ Class groups dict: O(n) where n = number of students
└─ Output workbook: proportional to output file size

Typical memory usage:
├─ 1,000 students: ~10 MB
├─ 10,000 students: ~50 MB
└─ 50,000 students: ~200 MB

(Plus base application overhead of ~100 MB)
```

---

**Created:** November 18, 2025
**Updated:** Real-time as application evolves
