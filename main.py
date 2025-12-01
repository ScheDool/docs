from src.agent import load_agent1_prompts, init_agent
from src.scheduleManager import ScheduleManager
from src.tools import create_tools
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()
    
def main():    
    
    # ============================================
    # Initialize Global State
    # ============================================

    schedule_manager = ScheduleManager()
    
    tools = create_tools(schedule_manager=schedule_manager)

    print("=== Preschedule Processing Agent with Pydantic Validation ===\n")
    
    agent1_prompt_files_path = {
        "system_prompt": "system_prompt.txt",
        "input_description": "input_description.txt",
        "task1": "task1.txt",
        "task2": "task2.txt",
        "task3": "task3.txt",
        "task4": "task4.txt",
        "task5": "task5.txt",
    }

    expected_file = [
        "curriculum.csv", "elective.csv", "teacher.csv", 
        "period.csv", "preplace.csv", "room.csv", 
        "student.csv", "scout.csv"
    ]

    OUTPUT_DIR = "output_processed"

    

    preschedule_prompt = load_agent1_prompts(files_path=agent1_prompt_files_path)

    for file_name in expected_file:
        key = file_name.replace(".csv", "").upper()
        file_name = file_name.replace(".csv", "_cleaned.csv")
        
        file_path = os.path.join(OUTPUT_DIR, file_name)
        try:
            df = pd.read_csv(file_path)
            schedule_manager.load_sheet_data(key, df)
            # print(f"load csv {key} to manager")
        except FileNotFoundError:
            print("Error: The CSV file was not found.")
            
    print(schedule_manager.sheets.keys())

    # Calling Agent 
    agent_executor = init_agent(tools=tools, system_prompt=preschedule_prompt['system_prompt']+preschedule_prompt['input_description'])
    user_input = preschedule_prompt['task1']
    response = agent_executor.invoke({"input": user_input})
    
    # debug state after task 1
    print(schedule_manager.periods)
    print(schedule_manager.student_grids)
    print(schedule_manager.teacher_grids)
    print(schedule_manager.room_grids)
            
if __name__ == "__main__":
    main()