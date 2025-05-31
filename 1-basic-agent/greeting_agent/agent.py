from google.adk.agents import Agent
from .file_utils import get_instruction

# Define the path to your file
file_path = "instruction.md"  # Replace with the actual path to your file

instruction = get_instruction(file_path)

# It's good practice to handle cases where the instruction might not have loaded
if instruction is None:
    print("Warning: Instruction could not be loaded from file. Using a default.")
    # Provide a fallback or handle the error appropriately
    instruction = """
    You are a helpful assistant that greets the user.
    Ask for the user's name and greet them by name.
    """
    # If the instruction file is critical, you might want to exit:
    import sys
    sys.exit(f"Error: Could not load instruction file: {file_path}")

root_agent = Agent(
    # name must match parent folder name
    name="greeting_agent",
    # https://ai.google.dev/gemini-api/docs/models
    model="gemini-2.0-flash",
    description="Greeting agent",    
    # instruction=instruction,
    instruction="""
    You are a helpful assistant that greets the user. 
    Ask for the user's name and greet them by name.
    """,
    
)




