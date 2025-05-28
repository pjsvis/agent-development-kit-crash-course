# d:\dev\agent-development-kit-crash-course\14-github-agent\main.py
import sys
import inspect # To inspect function parameters

# It's important to adjust the Python path if main.py is outside the package
# and you're running it directly. This ensures it can find the 'github_agent' package.
# If '14-github-agent' is the project root and 'github_agent' is a sub-package,
# and you run `python main.py` from `14-github-agent`, this might be needed.
# However, if you run `python -m github_agent.main` (if main.py was moved inside),
# or if your PYTHONPATH is set up, this might not be strictly necessary.
# For simplicity, assuming you run `python main.py` from `14-github-agent/`
# and `github_agent` is a direct subdirectory.

# Add the project root to sys.path to allow importing from the github_agent package
# This assumes main.py is in the '14-github-agent' directory,
# and the 'github_agent' package is a subdirectory.
# If main.py is inside the github_agent package, this is not needed.
# For this example, let's assume main.py is at the root of 14-github-agent.
# If you move main.py into the github_agent package, you'd change imports.

try:
    from github_agent.github_agent import (
        initialize_github_services,
        list_files_tool,
        read_file_tool,
        create_file_tool,
        update_file_tool,
        delete_file_tool,
        INITIALIZATION_SUCCESSFUL, # To check if GitHub client initialized
        EFFECTIVE_REPO_URL
    )
except ModuleNotFoundError:
    print("Error: Could not import from 'github_agent.github_agent'.")
    print("Ensure you are running this script from the '14-github-agent' directory,")
    print("or that the 'github_agent' package is correctly in your PYTHONPATH.")
    sys.exit(1)


APP_NAME = "CTX_GitHub_Tool_Tester_v0.2"

def get_tool_params(tool_func):
    """Inspects a tool function and prompts user for its parameters."""
    params = inspect.signature(tool_func).parameters
    args = {}
    print(f"\nEnter parameters for '{tool_func.__name__}':")
    for name, param in params.items():
        prompt_text = f"  {name}"
        if param.default != inspect.Parameter.empty:
            prompt_text += f" (optional, default: '{param.default}')"
        else:
            prompt_text += " (required)"
        prompt_text += ": "
        
        while True:
            value_str = input(prompt_text).strip()
            if value_str:
                args[name] = value_str
                break
            elif param.default != inspect.Parameter.empty:
                # User pressed enter for an optional param, use default
                # Note: The tool functions themselves handle their defaults if None is passed
                # for string args. For this CLI, we'll pass None if empty for optional.
                args[name] = None # Or param.default if we want to be more explicit
                break
            else:
                print(f"  Parameter '{name}' is required. Please provide a value.")
    return args

def run_tool_tester():
    """
    Runs an interactive CLI to test the GitHub tool functions.
    """
    print(f"--- Welcome to {APP_NAME} ---")

    print("Attempting to initialize GitHub services...")
    if not initialize_github_services() or not INITIALIZATION_SUCCESSFUL:
        print(f"Warning: GitHub services failed to initialize. Effective Repo URL: {EFFECTIVE_REPO_URL}")
        print("Tool functions might return errors related to GitHub client initialization.")
        print("Please check your .env configuration (GITHUB_PAT, GITHUB_REPO_URL) and logs.")
    else:
        print(f"GitHub services initialized. Effective Repo URL: {EFFECTIVE_REPO_URL}")

    tools = {
        "1": ("List files/directories", list_files_tool),
        "2": ("Read a file", read_file_tool),
        "3": ("Create a file", create_file_tool),
        "4": ("Update a file", update_file_tool),
        "5": ("Delete a file", delete_file_tool),
    }

    print("\nAvailable tools to test:")
    for key, (desc, _) in tools.items():
        print(f"  {key}. {desc}")
    print("  exit - Quit the tester")

    try:
        while True:
            choice = input("\nChoose a tool to test (enter number or 'exit'): ").strip().lower()

            if choice == 'exit':
                break
            
            if choice in tools:
                description, tool_func = tools[choice]
                print(f"\n--- Testing: {description} ---")
                try:
                    tool_args = get_tool_params(tool_func)
                    # Filter out None values for optional args if the tool expects them to be omitted
                    # or handles None appropriately. For simplicity, we pass them as is.
                    # Some tools might have non-string args in a real scenario,
                    # this simple CLI assumes all inputs are strings that tools can handle.
                    
                    print(f"Calling {tool_func.__name__} with arguments: {tool_args}")
                    result = tool_func(**tool_args)
                    print("\nTool Result:")
                    print("----------------------------------------------------")
                    print(result)
                    print("----------------------------------------------------")
                except Exception as e:
                    print(f"An error occurred while preparing or running the tool '{tool_func.__name__}': {e}")
            else:
                print("Invalid choice. Please enter a valid number or 'exit'.")

    except KeyboardInterrupt:
        print("\nUser interrupted session.")
    finally:
        print(f"\n--- Exiting {APP_NAME} ---")

if __name__ == "__main__":
    try:
        run_tool_tester()
    except Exception as e:
        print(f"An unexpected critical error occurred in the application: {e}")
        print("Application terminated.")

