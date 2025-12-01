import json
import pandas as pd
from typing import get_type_hints, Optional, List, Dict
from langchain_core.tools import StructuredTool
from src.types import InitTimetableInput, PeriodItem, GetSheetInput, GetScheduleInput, PlaceSlotInput, PeriodItemData, ProcessPreplaceRowInput, FindPeriodInput, LoopProcessInput, ExportSchedulesInput, ParsePeriodRangeInput
from functools import wraps

def parse_structured_input(func):
    """Decorator to parse JSON string inputs into proper Python types"""
    @wraps(func)
    def wrapper(*args, **kwargs):
        # Get the first argument (usually the structured input)
        if args:
            first_arg = args[0]
            
            # If it's a JSON string, try to parse it
            if isinstance(first_arg, str) and first_arg.strip().startswith('{'):
                try:
                    parsed = json.loads(first_arg)
                    
                    # Get function hints to determine expected type
                    hints = get_type_hints(func)
                    first_param = list(hints.keys())[0] if hints else None
                    
                    # If expecting a List, extract from wrapper dict
                    if first_param and 'List' in str(hints.get(first_param, '')):
                        # Handle {"periods": [...]} -> [...]
                        if isinstance(parsed, dict):
                            # Get first value (the list)
                            parsed = list(parsed.values())[0] if parsed else []
                        
                        # Convert list of dicts to Pydantic models
                        param_type = hints[first_param]
                        if hasattr(param_type, '__args__'):
                            item_type = param_type.__args__[0]
                            if hasattr(item_type, 'model_validate'):
                                parsed = [item_type(**item) for item in parsed]
                    
                    args = (parsed,) + args[1:]
                except (json.JSONDecodeError, Exception) as e:
                    # If parsing fails, use original
                    pass
        
        return func(*args, **kwargs)
    return wrapper

# ============================================
# Tool Functions with Pydantic Validation
# ============================================
def create_tools(schedule_manager) -> List[StructuredTool]:
    """
    Create all tools with access to the schedule_manager instance.
    
    Args:
        schedule_manager: The ScheduleManager instance to use
    
    Returns:
        List of configured StructuredTool objects
    """
    @parse_structured_input
    def initialize_period_structure(periods: List[PeriodItem]) -> str:
        """Initialize the grid structure with periods"""
        try:
            # # Handle JSON string input
            # if periods.strip().startswith('{'):
            #     parsed = json.loads(periods)
            #     periods = parsed.get('periods', periods)
                
            # Convert Pydantic models to dataclass for internal use
            period_data = [PeriodItemData(label=p.label, time=p.time) for p in periods]
            
            result = schedule_manager.initialize_grids(period_data)
            return f"{result} Created template with {len(periods)} period columns."
        except Exception as e:
            return f"Error initializing periods: {str(e)}"

    @parse_structured_input
    def get_sheet_info(sheet_name: str) -> str:
        """Get information about a loaded sheet"""
        try:
            # # Handle JSON string input
            # if sheet_name.strip().startswith('{'):
            #     parsed = json.loads(sheet_name)
            #     sheet_name = parsed.get('sheet_name', sheet_name)
                
            print(f"[DEBUG] Available sheets: {list(schedule_manager.sheets.keys())}")
            print(f"[DEBUG] Requesting sheet: '{sheet_name}'")
            
            df = schedule_manager.get_sheet_data(sheet_name)
            if df is None:
                return f"Sheet '{sheet_name}' not found. Available sheets: {list(schedule_manager.sheets.keys())}"
            
            info = {
                "sheet_name": sheet_name,
                "rows": len(df),
                "columns": list(df.columns),
                "sample_data": df.head(3).to_dict('records')
            }
            return json.dumps(info, indent=2, default=str)
        except Exception as e:
            return f"Error getting sheet info: {str(e)}"

    @parse_structured_input
    def list_loaded_sheets() -> str:
        """List all loaded sheets"""
        sheets = list(schedule_manager.sheets.keys())
        return json.dumps({"loaded_sheets": sheets, "count": len(sheets)}, indent=2)

    @parse_structured_input
    def process_preplace_row(sheet_name: str, row_index: int) -> str:
        """Process a single row from preplace slots sheet"""
        try:
            df = schedule_manager.get_sheet_data(sheet_name)
            
            if df is None:
                return f"Error: Sheet '{sheet_name}' not loaded"
            
            if row_index >= len(df):
                return f"Error: Row index {row_index} out of range (max: {len(df)-1})"
            
            row = df.iloc[row_index]
            row_dict = dict(row)
            
            return json.dumps({
                "row_index": row_index,
                "data": row_dict,
                "status": "retrieved"
            }, indent=2, default=str)
        except Exception as e:
            return f"Error processing row: {str(e)}"

    @parse_structured_input
    def find_period_column(period_label: str) -> str:
        """Find the period column header for a given period label"""
        try:
            periods = schedule_manager.get_periods()
            
            # Find matching period
            matching_period = None
            for p in periods:
                if p.label == period_label:
                    matching_period = p
                    break
            
            if matching_period:
                period_col = f"{matching_period.label},{matching_period.time}"
                return json.dumps({
                    "period_label": period_label,
                    "period_column": period_col,
                    "time": matching_period.time,
                    "found": True
                }, indent=2)
            else:
                return json.dumps({
                    "period_label": period_label,
                    "found": False,
                    "available_periods": [p.label for p in periods]
                }, indent=2)
        except Exception as e:
            return f"Error finding period: {str(e)}"
    
    @parse_structured_input
    def place_schedule_slot(
        day: str, period_col: str, subject_id: str, 
        teacher_id: Optional[str] = None, room_id: Optional[str] = None, 
        class_id: Optional[str] = None, reason: str = "preplace"
    ) -> str:
        """Place a slot in the schedule"""
        try:
            result = schedule_manager.place_slot(
                day=day,
                period_col=period_col,
                subject_id=subject_id,
                teacher_id=teacher_id,
                room_id=room_id,
                class_id=class_id,
                reason=reason
            )
            
            return result
        except Exception as e:
            return f"Error placing slot: {str(e)}"

    @parse_structured_input
    def loop_process_preplace_sheet(
        sheet_name: str, 
        start_index: int = 0, end_index: Optional[int] = None
    ) -> str:
        """Loop through preplace sheet and process each row"""
        try:
            df = schedule_manager.get_sheet_data(sheet_name)
            if df is None:
                return f"Error: Sheet '{sheet_name}' not loaded"
            
            total_rows = len(df)
            end = end_index if end_index else total_rows
            
            results = []
            for i in range(start_index, min(end, total_rows)):
                row = df.iloc[i]
                results.append({
                    "row_index": i,
                    "data": dict(row),
                    "status": "processed"
                })
            
            summary = {
                "sheet": sheet_name,
                "processed_rows": len(results),
                "range": f"{start_index} to {end-1}",
                "sample_results": results[:3]  # Show first 3
            }
            
            return json.dumps(summary, indent=2, default=str)
        except Exception as e:
            return f"Error in loop processing: {str(e)}"

    @parse_structured_input
    def get_conflicts() -> str:
        """Get all scheduling conflicts"""
        conflicts = schedule_manager.conflicts
        return json.dumps({
            "total_conflicts": len(conflicts),
            "conflicts": conflicts
        }, indent=2)

    @parse_structured_input
    def get_entity_schedule(entity_type: str, entity_id: str) -> str:
        """Get schedule for a specific entity"""
        try:
            grid = schedule_manager._get_or_create_grid(entity_type, entity_id)
            
            # Convert to readable format
            schedule_dict = grid.to_dict('index')
            
            return json.dumps({
                "entity_type": entity_type,
                "entity_id": entity_id,
                "schedule": schedule_dict
            }, indent=2, default=str)
        except Exception as e:
            return f"Error getting entity schedule: {str(e)}"

    @parse_structured_input
    def export_all_schedules(output_path: str) -> str:
        """Export all schedules to JSON file"""
        try:
            export_data = {
                "students": {k: v.to_dict('index') for k, v in schedule_manager.student_grids.items()},
                "teachers": {k: v.to_dict('index') for k, v in schedule_manager.teacher_grids.items()},
                "rooms": {k: v.to_dict('index') for k, v in schedule_manager.room_grids.items()},
                "conflicts": schedule_manager.conflicts,
                "periods": [{"label": p.label, "time": p.time} for p in schedule_manager.periods]
            }
            
            with open(output_path, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            return f"Successfully exported all schedules to {output_path}"
        except Exception as e:
            return f"Error exporting schedules: {str(e)}"

    @parse_structured_input
    def parse_period_range(period_string: str) -> List[Dict[str, str]]:
        """
        Parse complex period range expressions into individual (day, period) pairs.
        
        Examples:
        - "MON_1-MON_3" → [{"day": "MON", "period": "1"}, {"day": "MON", "period": "2"}, {"day": "MON", "period": "3"}]
        - "Everyday_4" → [{"day": "MON", "period": "4"}, {"day": "TUE", "period": "4"}, ...]
        - "TUE_2,THU_2" → [{"day": "TUE", "period": "2"}, {"day": "THU", "period": "2"}]
        """
        weekdays = ["MON", "TUE", "WED", "THU", "FRI"]
        result = []
        
        # Split by comma for multiple ranges
        ranges = [r.strip() for r in period_string.split(',')]
        
        for range_expr in ranges:
            if 'Everyday' in range_expr:
                # Extract period number after underscore
                period = range_expr.split('_')[1]
                for day in weekdays:
                    result.append({"day": day, "period": period})
            
            elif '-' in range_expr:
                # Range format: DAY_START-DAY_END
                start_part, end_part = range_expr.split('-')
                start_day, start_period = start_part.split('_')
                end_day, end_period = end_part.split('_')
                
                # If same day, expand period range
                if start_day == end_day:
                    for p in range(int(start_period), int(end_period) + 1):
                        result.append({"day": start_day, "period": str(p)})
                else:
                    # Cross-day range - handle appropriately
                    # This is more complex and depends on your requirements
                    pass
            
            else:
                # Single slot: DAY_PERIOD
                day, period = range_expr.split('_')
                result.append({"day": day, "period": period})
        
        return result


# ============================================
# Create Structured Tools with Pydantic
# ============================================

    tools = [
        StructuredTool.from_function(
            func=initialize_period_structure,
            name="InitializePeriodStructure",
            description="Initialize the grid template with period structure. Must be called before placing any slots.",
            args_schema=InitTimetableInput
        ),
        StructuredTool.from_function(
            func=list_loaded_sheets,
            name="ListLoadedSheets",
            description="List all currently loaded sheets in memory"
        ),
        StructuredTool.from_function(
            func=get_sheet_info,
            name="GetSheetInfo",
            description="Get detailed information about a loaded sheet including columns and sample data",
            args_schema=GetSheetInput
        ),
        StructuredTool.from_function(
            func=process_preplace_row,
            name="ProcessPreplaceRow",
            description="Process a single row from the preplace sheet and return its data",
            args_schema=ProcessPreplaceRowInput
        ),
        StructuredTool.from_function(
            func=find_period_column,
            name="FindPeriodColumn",
            description="Find the period column header string for a given period label. Returns the format 'label,time' needed for PlaceScheduleSlot.",
            args_schema=FindPeriodInput
        ),
        StructuredTool.from_function(
            func=place_schedule_slot,
            name="PlaceScheduleSlot",
            description="Place a slot in the schedule grid. Checks for conflicts with existing slots. Returns SUCCESS or CONFLICT message.",
            args_schema=PlaceSlotInput
        ),
        StructuredTool.from_function(
            func=loop_process_preplace_sheet,
            name="LoopProcessPreplaceSheet",
            description="Loop through multiple rows in the preplace sheet and return their data for processing",
            args_schema=LoopProcessInput
        ),
        StructuredTool.from_function(
            func=get_conflicts,
            name="GetConflicts",
            description="Get all scheduling conflicts that occurred during slot placement"
        ),
        StructuredTool.from_function(
            func=get_entity_schedule,
            name="GetEntitySchedule",
            description="Get the complete schedule grid for a specific student, teacher, or room",
            args_schema=GetScheduleInput
        ),
        StructuredTool.from_function(
            func=export_all_schedules,
            name="ExportAllSchedules",
            description="Export all schedules (students, teachers, rooms) and conflicts to a JSON file",
            args_schema=ExportSchedulesInput
        ),
        StructuredTool.from_function(
            func=parse_period_range,
            name="ParsePeriodRange",
            description="Parse complex period range expressions into individual (day, period) pairs. Handles formats like 'MON_1-MON_3', 'Everyday_4', 'TUE_2,THU_2'.",
            args_schema=ParsePeriodRangeInput
        )
    ]
    
    return tools
