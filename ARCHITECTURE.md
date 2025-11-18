# Class Roster Generator - Architecture Guide

## Overview

The application uses a **two-stage pipeline architecture** with a clear separation between data cleaning and class splitting. This allows:
- Schools with various formats → Standardized Excel file (Stage 1)
- Standardized file → Split by class (Stage 2)

Each stage is **completely independent**, so you can use Stage 2 on any properly formatted Excel file.

## Architecture

```
STAGE 1: Data Cleaning & Standardization
─────────────────────────────────────────
Raw School Data (various formats)
        ↓
┌──────────────────────────────────────────┐
│  DataCleaningStage (school-specific)     │
│  ├─ Normalize names (title case, trim)   │
│  ├─ Remove duplicates                    │
│  ├─ Fix formatting issues                │
│  ├─ Handle missing data                  │
│  └─ Validate data integrity              │
└──────────────────────────────────────────┘
        ↓
Standard Excel Format Output
  (Columns: CLASS, Teacher, Name)


STAGE 2: Class Splitting
────────────────────────
Standardized Excel File
        ↓
┌──────────────────────────────────────────┐
│  ClassSplittingStage (generic, reusable) │
│  ├─ Parse columns (CLASS, Teacher, Name) │
│  ├─ Group by class                       │
│  ├─ Remove duplicate students            │
│  ├─ Sort students alphabetically         │
│  └─ Create sheet per class               │
└──────────────────────────────────────────┘
        ↓
Output Excel File (split by class, one sheet per class)
```

## File Structure

```
pythonConverter/
├── class_roster_ui.py              # Main UI + core pipeline classes
│   ├── PipelineStage (ABC)
│   ├── DataCleaningStage
│   ├── ClassSplittingStage
│   ├── ProcessingPipeline
│   ├── ProcessThread (QThread)
│   └── ClassRosterGUI (QMainWindow)
│
├── cleaning_stages.py               # School-specific implementations
│   ├── SchoolACleaningStage
│   ├── SchoolBCleaningStage
│   ├── get_cleaning_only_pipeline()
│   ├── get_cleaning_pipeline()     # (for future: both stages)
│   └── get_school_x_pipeline()
│
├── ARCHITECTURE.md                 # This file
└── requirements.txt
```

## User Interface Layout

### STAGE 1: Data Cleaning & Standardization
```
┌────────────────────────────────────────┐
│ School Format:      [Default          ]│
│ Raw Data File:      [Browse...        ]│
│ Standardized Output:[Browse...        ]│
│                                        │
│ [→ Clean & Standardize Data]           │
└────────────────────────────────────────┘
```

**Process:**
1. Select school format (e.g., "School A", "School B", "Default")
2. Select raw data file from school
3. Choose where to save standardized output
4. Click "Clean & Standardize Data"
5. Output is saved with standard format

**After Stage 1 completes:**
- Automatically populates Stage 2 input with Stage 1 output
- Suggests Stage 2 output filename
- Offers to open the standardized file

### STAGE 2: Split by Class
```
┌────────────────────────────────────────┐
│ Input File:         [Browse...        ]│
│ Output File:        [Browse...        ]│
│                                        │
│ [→ Split by Class]                     │
└────────────────────────────────────────┘
```

**Process:**
1. Select standardized Excel file (from Stage 1 or any compatible format)
2. Choose where to save split output
3. Click "Split by Class"
4. Output has separate sheets per class

**Expected Input Format:**
- Column "CLASS" or "Class" or "Class ID" or similar
- Column "Teacher" or "TEACHER"
- Column "Name" or "Student" or "STUDENT"

## How to Add a New School Format

### 1. Create Custom Cleaning Stage in `cleaning_stages.py`:

```python
class SchoolXCleaningStage(DataCleaningStage):
    """
    Custom cleaning for 'School X' format.
    
    School X sends data with:
    - [describe specific issues]
    - [specific quirks to handle]
    """
    
    def process(self, data: dict) -> dict:
        """Clean School X format data"""
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Your custom cleaning logic
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Example: normalize whitespace and case
                    cell.value = " ".join(cell.value.split()).title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (School X Format)"
```

### 2. Register in `get_cleaning_only_pipeline()`:

```python
def get_cleaning_only_pipeline(school_format: str) -> ProcessingPipeline:
    school_format = school_format.strip().lower()
    
    if school_format == "school x":
        return ProcessingPipeline(stages=[SchoolXCleaningStage()])
    elif school_format == "school a":
        return ProcessingPipeline(stages=[SchoolACleaningStage()])
    # ... etc
```

### 3. That's it! 
The UI will automatically support "School X" when entered in the School Format field.

## Data Flow & Formats

### Stage 1 Input → Output

**Input:** Raw school data (any format)
- May have extra columns
- May have data quality issues
- May have inconsistent formatting

**Output:** Standardized Excel format
```
Column A: CLASS      (e.g., "08/108", "070110")
Column B: Teacher    (e.g., "Jesika Rosen", "Iris Soling")
Column C: Name       (e.g., "Breanna Ortega", "Melton Barron")
```

### Stage 2 Input → Output

**Input:** Standardized Excel file (from Stage 1 or compatible)

**Output:** Split by class
```
Sheet 1: "Class 08/108"
  Column A: Student      Column B: Class
  ─────────────────────────────────────
  Breanna Ortega         08/108
  Daniel Akinade         08/108
  ... (sorted alphabetically)
  
  Teacher: Jesika Rosen
  Advisor:

Sheet 2: "Class 070110"
  Column A: Student      Column B: Class
  ─────────────────────────────────────
  Iris Soling            070110
  Reuben Soto            070110
  ... (sorted alphabetically)
```

## Key Features

✅ **Two Independent Stages** - Use them separately or together  
✅ **Auto-Population** - Stage 1 output → Stage 2 input  
✅ **School Format Support** - Easy to add new school formats  
✅ **Non-blocking UI** - Processing runs in separate thread  
✅ **Error Handling** - Graceful error reporting  
✅ **Duplicate Removal** - Automatic deduplication per class  
✅ **Sorted Output** - Students alphabetically sorted per class  
✅ **File Overwrite Protection** - Asks before overwriting  

## Pipeline Classes

### `PipelineStage` (Abstract Base Class)
```python
class PipelineStage(ABC):
    @abstractmethod
    def process(self, data: dict) -> dict:
        """Process data and return modified data"""
        pass
    
    @abstractmethod
    def get_stage_name(self) -> str:
        """Return human-readable name of this stage"""
        pass
```

### `DataCleaningStage`
- Base implementation (no-op, just passes data through)
- Override in `cleaning_stages.py` for specific schools
- Takes: `data["worksheet"]`
- Returns: Modified `data` with same structure

### `ClassSplittingStage`
- Generic, reusable implementation
- Groups students by class
- Creates output workbook with sheets per class
- Takes: `data["worksheet"]` with standard format
- Returns: `data` with `output_workbook`, `class_groups`, `row_count`

### `ProcessingPipeline`
- Orchestrates multiple `PipelineStage` instances
- `execute()` method runs all stages in sequence
- Handles file I/O and error handling

### `ProcessThread`
- `QThread` subclass
- Runs pipeline asynchronously
- Emits progress signals to UI
- Prevents UI blocking during processing

## Testing a New School Format

```python
from class_roster_ui import ProcessingPipeline
from cleaning_stages import SchoolXCleaningStage

# Test cleaning only
pipeline = ProcessingPipeline(stages=[SchoolXCleaningStage()])
success, message, data = pipeline.execute(
    source_path="raw_school_x_data.xlsx",
    output_path="standardized.xlsx"
)

print(f"Success: {success}")
print(f"Message: {message}")

# Test with splitting too
from class_roster_ui import ClassSplittingStage
pipeline_full = ProcessingPipeline(stages=[
    SchoolXCleaningStage(),
    ClassSplittingStage()
])
```

## Future Enhancements

- [ ] Add data validation stage
- [ ] Add preview of first N rows before processing
- [ ] Add batch processing for multiple files
- [ ] Configuration file for school formats (JSON/YAML)
- [ ] Undo/rollback capability
- [ ] Logging to file
- [ ] Custom column mapping UI
- [ ] Support for CSV input
- [ ] Progress bar instead of text log

