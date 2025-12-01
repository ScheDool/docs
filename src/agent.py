import os
from langchain_classic.agents import AgentExecutor, create_react_agent
from typing import Dict, List
from langchain_core.tools import StructuredTool
from langchain_core.prompts import ChatPromptTemplate
from langchain_ollama import ChatOllama

def load_agent1_prompts(files_path: Dict[str, str]) -> Dict[str, str]:
    preschedule_prompt = {}
    prompt_path = "scheduling_prompt/Agent1"
    print(files_path)
    for name, path in files_path.items():
        file_path = os.path.join(prompt_path, path)
        with open(file_path) as f:
            preschedule_prompt[name] = f.read()
    return preschedule_prompt


# ============================================
# Initialize Agent Function
# ============================================

def init_agent(tools: List[StructuredTool], system_prompt: str, temperature: float = 0.1, 
               base_url: str = "http://localhost:11434") -> AgentExecutor:
    """
    Initialize the preschedule processing agent with ChatOllama.
    
    Args:
        model: The Ollama model to use (default: "llama3")
        temperature: Sampling temperature 0.0-1.0 (default: 0.1 for consistent processing)
        base_url: Ollama server URL (default: "http://localhost:11434")
    
    Returns:
        AgentExecutor: Configured agent ready to process preschedule tasks
    """
    # Define Model
    model = "gpt-oss:120b-cloud"
    
    # Initialize ChatOllama
    llm = ChatOllama(
        model=model,
        temperature=temperature,
        base_url=base_url
    )
    
    prompt = ChatPromptTemplate.from_template(system_prompt)
    
    # Create agent
    agent = create_react_agent(llm, tools, prompt)
    
    # Create and return agent executor
    agent_executor = AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=25,
        handle_parsing_errors=True
    )
    
    return agent_executor
