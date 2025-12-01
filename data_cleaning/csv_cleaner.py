import pandas as pd
import re
from data_cleaning.mapping import create_room_lookup, create_teacher_lookup,resolve_teacher_names_to_ids, parse_student_class_string, resolve_room_to_ids, get_grade_sections

# data cleaning for curriculum sheet (teacher, studetn_class, room)
def clean_curriculum(
    df_curriculum: pd.DataFrame, 
    df_teacher: pd.DataFrame, 
    df_room: pd.DataFrame,
    df_student: pd.DataFrame,
) -> pd.DataFrame:
    if df_curriculum.empty:
        return df_curriculum
    
    print("\n--- Starting Curriculum Data Cleaning ---")
    
    # Process lookups
    teacher_lookup = create_teacher_lookup(df_teacher)
    room_lookup = create_room_lookup(df_room)
    grade_section_counts = get_grade_sections(df_student)
    
    # --- Main Iteration and Logic ---
    processed_rows = []
    current_grade_sections = [] 
    current_grade = None
    grade_marker_pattern = re.compile(r'ม\.\d+') 


    for index, row in df_curriculum.iterrows():
        # Get a dictionary representation of the current row (important for manipulation)
        row_dict = row.to_dict()
        first_col_value = str(row_dict[df_curriculum.columns[0]]).strip() 

        # Check for Grade Marker
        if grade_marker_pattern.match(first_col_value):
            current_grade = first_col_value
            current_grade_sections = grade_section_counts.get(current_grade, [])
            print(f"Detected Grade Marker: {current_grade}. Sections: {current_grade_sections}")

            processed_rows.append(row_dict) 
            continue 
            
        # --- Process Data Rows (Non-marker rows) ---
        # A. Clean 'teacher' column
        raw_teacher_name = row_dict.get('teacher')
        row_dict['teacher'] = resolve_teacher_names_to_ids(raw_teacher_name, teacher_lookup)
        
        # B. Clean 'student_class' column
        raw_section_str = row_dict.get('student_class')
        
        if pd.isna(raw_section_str) or raw_section_str == '':
            # Rule 1: NaN/Null means all sections for the current grade
            cleaned_sections = current_grade_sections
        else:
            # Rules 2, 3, 4: Specific/Range/Mixed (uses previously defined parse_student_class_string)
            cleaned_sections = parse_student_class_string(raw_section_str)
            
            # Validation: Filter sections to only those valid for the current grade
            valid_sections = [s for s in cleaned_sections if s in current_grade_sections]
            cleaned_sections = valid_sections
            
        row_dict['student_class'] = cleaned_sections
        
        # C. Clean 'room' column
        raw_room_str = row_dict.get('room')
        row_dict['room'] = resolve_room_to_ids(raw_room_str, room_lookup)
        
        # Append the fully cleaned data row
        processed_rows.append(row_dict)
        
    # Reconstruct the final DataFrame
    df_cleaned = pd.DataFrame(processed_rows)
    print("✅ Curriculum data cleaning complete.")
    return df_cleaned

# data cleaning for elective sheet (teacher, room)
def clean_elective(
    df_elective: pd.DataFrame, 
    df_teacher: pd.DataFrame, 
    df_room: pd.DataFrame
) -> pd.DataFrame:
    if df_elective.empty:
        print("⚠️ Elective DataFrame is empty. Skipping cleaning.")
        return df_elective
        
    print("\n--- Starting Elective Data Cleaning and Resolution ---")

    # Pre-process Lookups
    teacher_lookup = create_teacher_lookup(df_teacher)
    room_lookup = create_room_lookup(df_room) 
    
    # Apply Resolution to Columns
    # A. Resolve 'teacher' column (Name -> ID List)
    print("  - Resolving teacher names to IDs...")
    df_elective['teacher'] = df_elective['teacher'].apply(
        lambda x: resolve_teacher_names_to_ids(x, teacher_lookup)
    )

    # B. Resolve 'room' column (Tag/ID -> Room ID/List)
    print("  - Resolving room requirements...")
    df_elective['room'] = df_elective['room'].apply(
        lambda x: resolve_room_to_ids(x, room_lookup)
    )
    
    # Ensure subject ID and name are strings
    df_elective['subject_id'] = df_elective['subject_id'].astype(str).str.strip()
    df_elective['subject_name'] = df_elective['subject_name'].astype(str).str.strip()
            
    print("✅ Elective data cleaning complete.")
    return df_elective

# data cleaning for scout sheet (teacher)
def clean_scout(
    df_scout: pd.DataFrame, 
    df_teacher: pd.DataFrame
) -> pd.DataFrame:
    if df_scout.empty:
        print("⚠️ Scout DataFrame is empty. Skipping cleaning.")
        return df_scout
        
    print("\n--- Starting Scout Data Cleaning ---")

    # Create Teacher Name -> ID Lookup
    teacher_lookup = create_teacher_lookup(df_teacher)
    
    for col in df_scout.columns:
        print("  - Resolving teacher names to IDs...")
        df_scout[col] = df_scout[col].apply(
            lambda x: resolve_teacher_names_to_ids(x, teacher_lookup)
        )

    print("✅ Scout data cleaning complete.")
    return df_scout

# data cleaning for teacher sheet (marker rows)
def clean_teacher(df_teacher: pd.DataFrame) -> pd.DataFrame:
    if df_teacher.empty:
        print("⚠️ Teacher DataFrame is empty. Skipping cleaning.")
        return df_teacher
        
    print("\n--- Starting Teacher Data Cleaning---")

    marker_values = ['ครูในโรงเรียน', 'อาจารย์นอก']
    
    # 1. Identify rows to keep (where the first column does NOT contain the marker values)
    df_cleaned = df_teacher[
        ~df_teacher['teacher_id'].astype(str).str.strip().isin(marker_values)
    ].copy()
    
    # clean empty missing or invalid (marker) rows
    df_cleaned.dropna(subset=['teacher_id'], inplace=True)
    
    print(f"✅ Teacher marker and invalid rows removed.")
    
    return df_cleaned
