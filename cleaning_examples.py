"""
EXAMPLES: How to implement cleaning for different school formats

Copy and adapt these examples for your actual school data.
"""

from class_roster_ui import DataCleaningStage


# ============================================================================
# EXAMPLE 1: School with ALL CAPS names and leading spaces
# ============================================================================

class SchoolCapitalizedCleaningStage(DataCleaningStage):
    """
    Example: School sends data with:
    - Names in ALL CAPS (needs title case)
    - Leading/trailing spaces
    - Teacher field sometimes empty/null
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Process all cells starting from row 2 (skip header)
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Strip whitespace and convert to title case
                    cell.value = cell.value.strip().title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Capitalized Format)"


# ============================================================================
# EXAMPLE 2: School with extra whitespace and special characters
# ============================================================================

class SchoolMessy CleaningStage(DataCleaningStage):
    """
    Example: School sends data with:
    - Multiple spaces between words
    - Special characters: @, #, etc.
    - Inconsistent quotes around names
    - Extra tabs/newlines
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    value = cell.value
                    
                    # Remove special characters (keep only letters, numbers, spaces, hyphens)
                    import re
                    value = re.sub(r"[^\w\s'-]", '', value)
                    
                    # Normalize whitespace (remove extra spaces, tabs, newlines)
                    value = " ".join(value.split())
                    
                    # Strip quotes and convert to title case
                    value = value.strip("'\"").title()
                    
                    cell.value = value
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Messy Format)"


# ============================================================================
# EXAMPLE 3: School with duplicate detection and removal
# ============================================================================

class SchoolDuplicateCleaningStage(DataCleaningStage):
    """
    Example: School sends data with:
    - Many duplicate student records
    - Need to keep only first occurrence of each student
    
    WARNING: This is complex because openpyxl doesn't make it easy to delete rows.
    Better to handle duplicates during the splitting stage (which we already do!).
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # First, normalize all names
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell.value = cell.value.strip().title()
        
        # In this example, we just normalize. Deduplication happens
        # automatically in ClassSplittingStage using a set.
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Deduplication Ready)"


# ============================================================================
# EXAMPLE 4: School with merged cells and complex structure
# ============================================================================

class SchoolComplexStructureCleaningStage(DataCleaningStage):
    """
    Example: School sends data with:
    - Merged cells for class names
    - Multiple header rows
    - Extra columns with metadata
    
    For this, you'd want to:
    1. Unmerge cells
    2. Fill down values from merged cells
    3. Remove extra columns
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Unmerge all cells and fill down
        # Note: Be careful with this - it modifies the structure
        if ws.merged_cells:
            for merged_range in list(ws.merged_cells.ranges):
                ws.unmerge_cells(str(merged_range))
        
        # Now normalize all text
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell.value = cell.value.strip().title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Complex Structure)"


# ============================================================================
# EXAMPLE 5: School with comma-separated names that need splitting
# ============================================================================

class SchoolCSVNameCleaningStage(DataCleaningStage):
    """
    Example: School sends data where names are in format "LAST, FIRST"
    Need to convert to "First Last"
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    value = cell.value.strip()
                    
                    # Check if it's in "LAST, FIRST" format
                    if ',' in value:
                        parts = [p.strip() for p in value.split(',')]
                        # Reverse: FIRST LAST
                        value = ' '.join(reversed(parts))
                    
                    # Convert to title case
                    cell.value = value.title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (CSV Name Format)"


# ============================================================================
# EXAMPLE 6: Custom mapping - School uses different column headers
# ============================================================================

class SchoolCustomHeadersCleaningStage(DataCleaningStage):
    """
    Example: School sends data with different column names
    - Column "PUPIL ID" -> rename to "Name"
    - Column "INSTRUCTOR" -> rename to "Teacher"
    - Column "SECTION" -> rename to "CLASS"
    
    This preprocessing makes the data compatible with ClassSplittingStage
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Get first row (headers)
        header_row = list(ws.iter_rows(min_row=1, max_row=1))[0]
        
        # Map old headers to new headers
        header_map = {
            "PUPIL ID": "Name",
            "INSTRUCTOR": "Teacher",
            "SECTION": "CLASS",
            # Add more as needed
        }
        
        # Update header cells
        for cell in header_row:
            if cell.value in header_map:
                cell.value = header_map[cell.value]
        
        # Also normalize all data cells
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    cell.value = cell.value.strip().title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Custom Headers)"


# ============================================================================
# HOW TO USE THESE EXAMPLES
# ============================================================================

"""
1. Choose the example that matches your school format (or combine multiple)

2. Copy to cleaning_stages.py:

    class YourSchoolCleaningStage(DataCleaningStage):
        def process(self, data):
            # Your logic here
            return data
        
        def get_stage_name(self):
            return "Your School Name"

3. Register in get_cleaning_only_pipeline():

    def get_cleaning_only_pipeline(school_format: str):
        if school_format.lower() == "your school":
            return ProcessingPipeline(stages=[YourSchoolCleaningStage()])

4. Test with a sample file:

    from cleaning_stages import YourSchoolCleaningStage
    from class_roster_ui import ProcessingPipeline
    
    pipeline = ProcessingPipeline(stages=[YourSchoolCleaningStage()])
    success, msg, data = pipeline.execute("raw.xlsx", "cleaned.xlsx")

5. Debug if needed:
    - Print out sample cell values to see what you're working with
    - Use Python string methods: .strip(), .title(), .lower(), .replace(), etc.
    - Use regex if you need complex string manipulation
"""


# ============================================================================
# DEBUG HELPER - See what data you're working with
# ============================================================================

class DebugCleaningStage(DataCleaningStage):
    """
    Use this to understand your school's data format.
    Run this first to see what you're working with, then create a proper stage.
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        print("\n" + "="*60)
        print("DEBUGGING: First 10 rows of data")
        print("="*60)
        
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=10, values_only=True)):
            print(f"Row {i}: {row}")
        
        print("\n" + "="*60)
        print("Raw cell values (with types):")
        print("="*60)
        
        for i, row in enumerate(ws.iter_rows(min_row=1, max_row=5)):
            print(f"\nRow {i}:")
            for j, cell in enumerate(row):
                print(f"  Column {j}: {repr(cell.value)} (type: {type(cell.value).__name__})")
        
        # Don't modify the data, just return it
        return data
    
    def get_stage_name(self) -> str:
        return "Debug: Print Data"


# ============================================================================
# TEMPLATE - Start with this and customize
# ============================================================================

class YourSchoolTemplateCleaningStage(DataCleaningStage):
    """
    Template to customize for your school format.
    
    Modify the docstring to describe what this school sends:
    - Column names
    - Data quality issues
    - Formatting problems
    - Anything else that needs fixing
    """
    
    def process(self, data: dict) -> dict:
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Step 1: Handle header rows if needed
        # (Most schools have headers in row 1, skip to row 2)
        
        # Step 2: Process each data row
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Step 3: Clean the value
                    value = cell.value
                    
                    # Common operations:
                    value = value.strip()           # Remove leading/trailing spaces
                    value = value.title()           # Convert to Title Case
                    # value = value.upper()         # Or convert to UPPER
                    # value = value.lower()         # Or convert to lower
                    
                    cell.value = value
        
        # Step 4: Save and return
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (Your School)"
