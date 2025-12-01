from pydantic import BaseModel, Field
from typing import List, Optional
from dataclasses import dataclass

# ============================================
# Pydantic Input Models
# ============================================

class PeriodItem(BaseModel):
    """A single period with its label and time duration."""
    label: str = Field(description="The period name or number (e.g., '1', 'Lunch', 'Morning Break').")
    time: str = Field(description="The time or duration string (e.g., '08:30-09:20', '10' for 10 min).")

class InitTimetableInput(BaseModel):
    """The input schema for the init_timetable_structure tool."""
    periods: List[PeriodItem] = Field(description="A list of all period objects derived from the Period sheet.")

class GetSheetInput(BaseModel):
    """Input for retrieving a sheet's data."""
    sheet_name: str = Field(description="The name of the spreadsheet tab/sheet to retrieve (e.g., 'CURRICULUM', 'PRE-PLACE', 'TEACHER').")

class GetScheduleInput(BaseModel):
    """Input for retrieving an entity's schedule."""
    entity_type: str = Field(description="The type of entity: 'student', 'teacher', or 'room'.")
    entity_id: str = Field(description="The ID of the entity (e.g., 'M.1/1', 'T001', 'C102'). Reference from STUDENT, TEACHER and ROOM sheets.")

class PlaceSlotInput(BaseModel):
    """Input for placing a slot in the schedule."""
    day: str = Field(description="The weekday to schedule the slot ('MON', 'TUE', 'WED', 'THU', 'FRI').")
    period_col: str = Field(description="The full column header string which uniquely identifies the period (e.g., '1,08:30-09:20'). Constructed by concatenating 'label' and 'time' from PeriodItem.")
    subject_id: str = Field(description="The identifier of the subject/activity (e.g., 'ค10112', 'FREE', 'วิชาเลือก').")
    teacher_id: Optional[str] = Field(None, description="The ID of the teacher involved (e.g., 'T001'). Use None if no teacher.")
    room_id: Optional[str] = Field(None, description="The ID of the room used (e.g., 'C102'). Use None if no room.")
    class_id: Optional[str] = Field(None, description="The ID of the class/student group (e.g., 'M.1/1'). Use None if the slot is for a teacher/room only.")
    reason: str = Field("preplace", description="The reason for placement ('preplace', 'sched', 'constraint'). Default is 'preplace'.")

class ProcessPreplaceRowInput(BaseModel):
    """Input for processing a single preplace row."""
    sheet_name: str = Field(description="The sheet name containing preplace data.")
    row_index: int = Field(description="The zero-based index of the row to process.")

class FindPeriodInput(BaseModel):
    """Input for finding a period column."""
    period_label: str = Field(description="The period label to find (e.g., '1', '2', 'Lunch').")

class LoopProcessInput(BaseModel):
    """Input for loop processing preplace rows."""
    sheet_name: str = Field(description="The sheet name containing preplace data.")
    start_index: int = Field(0, description="Starting row index (default: 0).")
    end_index: Optional[int] = Field(None, description="Ending row index (exclusive). If None, process all rows.")

class ExportSchedulesInput(BaseModel):
    """Input for exporting schedules."""
    output_path: str = Field(description="Path to save the exported JSON file.")

# Add Pydantic input schema
class ParsePeriodRangeInput(BaseModel):
    """Input for parsing period range expressions."""
    period_string: str = Field(description="Period range expression to parse (e.g., 'MON_1-MON_3', 'Everyday_4')")


# ============================================
# Other Models
# ============================================

@dataclass
class PeriodItemData:
    """Data class for storing period information internally."""
    label: str
    time: str