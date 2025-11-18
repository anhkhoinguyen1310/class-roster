"""
School-specific data cleaning stages.

Extend this module with custom DataCleaningStage implementations for each school format.
Each school sends data in a different format, so we normalize it to a standard format:
- Columns: CLASS, Teacher, Name
- Clean data: trimmed, no duplicates, proper case
"""

from class_roster_ui import DataCleaningStage, ProcessingPipeline, ClassSplittingStage


class SchoolACleaningStage(DataCleaningStage):
    """
    Example: Custom cleaning for 'School A' format.
    
    School A sends data with:
    - Names in ALL CAPS
    - Leading/trailing spaces
    - Duplicate entries
    - Mixed case class names
    """
    
    def process(self, data: dict) -> dict:
        """Clean School A format data"""
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Example: Normalize names and classes in-place
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Normalize: trim, convert to title case
                    cell.value = cell.value.strip().title()
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (School A Format)"


class SchoolBCleaningStage(DataCleaningStage):
    """
    Example: Custom cleaning for 'School B' format.
    
    School B sends data with:
    - Extra whitespace columns
    - Merged cells
    - Special characters in names
    """
    
    def process(self, data: dict) -> dict:
        """Clean School B format data"""
        ws = data.get("worksheet")
        if not ws:
            return data
        
        # Example: Remove extra spaces, handle special characters
        for row in ws.iter_rows(min_row=2):
            for cell in row:
                if cell.value and isinstance(cell.value, str):
                    # Remove multiple spaces, normalize special chars
                    cell.value = " ".join(cell.value.split())
        
        return data
    
    def get_stage_name(self) -> str:
        return "Data Cleaning (School B Format)"


# ============================================================================
# CUSTOM PIPELINE EXAMPLES
# ============================================================================

def get_school_a_pipeline():
    """Create pipeline configured for School A data format"""
    return ProcessingPipeline(stages=[
        SchoolACleaningStage(),
        ClassSplittingStage()
    ])


def get_school_b_pipeline():
    """Create pipeline configured for School B data format"""
    return ProcessingPipeline(stages=[
        SchoolBCleaningStage(),
        ClassSplittingStage()
    ])


def get_default_pipeline():
    """Create default pipeline with minimal cleaning"""
    return ProcessingPipeline(stages=[
        DataCleaningStage(),  # Base stage does no transformation
        ClassSplittingStage()
    ])


def get_cleaning_pipeline(school_format: str) -> ProcessingPipeline:
    """
    Get appropriate pipeline based on school format name.
    
    Args:
        school_format: School name or format (e.g., "School A", "School B", "Default")
    
    Returns:
        ProcessingPipeline with appropriate cleaning stage
    """
    school_format = school_format.strip().lower()
    
    pipelines = {
        "school a": get_school_a_pipeline,
        "school b": get_school_b_pipeline,
        "default": get_default_pipeline,
    }
    
    # Get the pipeline factory function, default to 'default' if not found
    factory = pipelines.get(school_format, pipelines["default"])
    return factory()


# ============================================================================
# PIPELINE FACTORY FOR STAGE 1 ONLY (cleaning without splitting)
# ============================================================================

def get_cleaning_only_pipeline(school_format: str) -> ProcessingPipeline:
    """
    Get a pipeline that ONLY cleans data, does NOT split by class.
    Used for Stage 1 (Data Cleaning & Standardization).
    
    Args:
        school_format: School name or format
    
    Returns:
        ProcessingPipeline with only the cleaning stage
    """
    school_format = school_format.strip().lower()
    
    if school_format == "school a":
        return ProcessingPipeline(stages=[SchoolACleaningStage()])
    elif school_format == "school b":
        return ProcessingPipeline(stages=[SchoolBCleaningStage()])
    else:
        return ProcessingPipeline(stages=[DataCleaningStage()])
