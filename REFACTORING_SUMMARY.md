# Refactoring Summary: Two-Stage Independent Pipeline

## What Changed

### Before
- Single workflow: File → Process → Split by class
- UI had single "Browse Source" / "Browse Output" / "Process"
- Difficult to handle school-specific data formats
- Cleaning logic was mixed with splitting logic

### After
- **Two completely independent stages**
- **Stage 1 (Data Cleaning):** Raw school data → Standardized Excel
- **Stage 2 (Class Splitting):** Standardized Excel → Split by class
- **Separate UI sections** for each stage
- Auto-population from Stage 1 → Stage 2
- Easy to add school-specific cleaning without touching splitting logic

---

## UI Changes

### Old UI
```
┌─────────────────────────────┐
│ Source File     [Browse]    │
│ Output File     [Browse]    │
│ [Generate Class Rosters]    │
│                             │
│ Status Log                  │
└─────────────────────────────┘
```

### New UI
```
STAGE 1: Data Cleaning & Standardization
┌──────────────────────────────────────┐
│ School Format:   [Default         ]  │
│ Raw Data File:   [Browse]            │
│ Standardized:    [Browse]            │
│ [→ Clean & Standardize Data]         │
└──────────────────────────────────────┘
              ↓
STAGE 2: Split by Class
┌──────────────────────────────────────┐
│ Input File:      [Browse]            │
│ Output File:     [Browse]            │
│ [→ Split by Class]                   │
└──────────────────────────────────────┘

Status Log (both stages report here)
```

---

## Code Structure Changes

### New Pipeline Architecture

```python
PipelineStage (ABC)
├── DataCleaningStage (base implementation, override per school)
└── ClassSplittingStage (generic, always the same)

ProcessingPipeline
└── Orchestrates multiple stages in sequence

ProcessThread (QThread)
└── Runs pipeline asynchronously

ClassRosterGUI
├── Stage 1 handlers: browse_raw_source(), browse_std_output(), process_cleaning()
├── Stage 2 handlers: browse_split_source(), browse_split_output(), process_splitting()
└── Utilities: open_file(), log()
```

### New Files Structure

```
class_roster_ui.py
├── PIPELINE STAGES
│   ├── PipelineStage (abstract base)
│   ├── DataCleaningStage (override per school)
│   └── ClassSplittingStage (fixed, reusable)
├── PROCESSING PIPELINE
│   └── ProcessingPipeline (orchestrates stages)
├── UI THREAD
│   └── ProcessThread (QThread wrapper)
└── GUI
    └── ClassRosterGUI (main window with 2 sections)

cleaning_stages.py
├── SchoolACleaningStage (example)
├── SchoolBCleaningStage (example)
├── get_cleaning_only_pipeline() (for Stage 1)
├── get_cleaning_pipeline() (for future: both stages)
└── get_school_x_pipeline() (template for new schools)
```

---

## How to Add a New School

### 1. Create cleaning stage in `cleaning_stages.py`

```python
class SchoolXCleaningStage(DataCleaningStage):
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        # Your cleaning logic here
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (School X Format)"
```

### 2. Register in `get_cleaning_only_pipeline()`

```python
def get_cleaning_only_pipeline(school_format: str):
    if school_format.lower() == "school x":
        return ProcessingPipeline(stages=[SchoolXCleaningStage()])
```

### 3. Done!
Users can now enter "School X" in the School Format field.

---

## Key Improvements

✅ **Modularity** - Stages are independent and testable  
✅ **Extensibility** - Add school formats without touching core code  
✅ **Clarity** - Two distinct workflows clearly separated in UI  
✅ **Flexibility** - Use Stage 2 on any properly formatted Excel  
✅ **UX** - Auto-population from Stage 1 → Stage 2  
✅ **Non-blocking** - Processing in separate thread  
✅ **Error Handling** - Graceful error messages  
✅ **File Safety** - Confirmation before overwrite  

---

## Usage Examples

### Example 1: Clean raw data from School A
1. Enter "School A" in School Format field
2. Browse to `school_a_raw_data.xlsx`
3. Choose output location: `school_a_standardized.xlsx`
4. Click "Clean & Standardize Data"
5. ✓ File is cleaned and saved

### Example 2: Split standardized file by class
1. (Optional) Run Example 1 first
2. Browse to standardized file (or any compatible format)
3. Choose output location
4. Click "Split by Class"
5. ✓ File is split and saved with one sheet per class

### Example 3: Both stages in sequence
1. Run Example 1 (Stage 1 completes)
2. Click "Open File?" to verify standardized data
3. Stage 2 input is auto-populated
4. Click "Split by Class"
5. Done!

---

## Testing

### Test Stage 1 only (cleaning)
```python
from class_roster_ui import ProcessingPipeline
from cleaning_stages import SchoolACleaningStage

pipeline = ProcessingPipeline(stages=[SchoolACleaningStage()])
success, msg, data = pipeline.execute("raw.xlsx", "cleaned.xlsx")
```

### Test Stage 2 only (splitting)
```python
from class_roster_ui import ProcessingPipeline, ClassSplittingStage

pipeline = ProcessingPipeline(stages=[ClassSplittingStage()])
success, msg, data = pipeline.execute("standardized.xlsx", "split.xlsx")
```

### Test both stages
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

## Files Modified

- `class_roster_ui.py` - Complete refactor of UI and pipeline structure
- `cleaning_stages.py` - Updated with new pipeline helpers
- `ARCHITECTURE.md` - Complete documentation of new architecture

## Backward Compatibility

❌ **NOT backward compatible** - This is a major UI redesign  
✅ **But migration is simple** - Old single-workflow can still be done using both stages in sequence
