# d:\dev\agent-development-kit-crash-course\14-github-agent\github_agent\github_agent.py
import logging
from typing import Optional # Import Optional
from google.adk.agents import Agent
from github import Github, GithubException, BadCredentialsException, UnknownObjectException

# Local module imports
from .config_loader import load_app_config
from . import github_client # Import the module to access its functions

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# --- Global variables for GitHub client and repository ---
github_instance = None
repository_object = None
app_config = {} # Initialize to empty dict

def initialize_github_services():
    """Initializes GitHub client and repository object if not already initialized."""
    global github_instance, repository_object, app_config
    if github_instance and repository_object:
        return True # Already initialized

    logger.info("Attempting to initialize GitHub services...")
    try:
        app_config = load_app_config()
        github_pat = app_config.get('GITHUB_PAT')
        repo_url_full = app_config.get('GITHUB_REPO_URL')

        if not github_pat or not repo_url_full:
            logger.error("GITHUB_PAT or GITHUB_REPO_URL not found in .env configuration.")
            app_config['EFFECTIVE_GITHUB_REPO_URL'] = "NOT_CONFIGURED_MISSING_PAT_OR_URL"
            return False

        if "github.com/" in repo_url_full:
            repo_name_part = repo_url_full.split("github.com/")[-1]
        else:
            repo_name_part = repo_url_full
        repo_name_part = repo_name_part.replace(".git", "")

        github_instance = Github(github_pat)
        user = github_instance.get_user()
        logger.info(f"Successfully authenticated with GitHub as user: {user.login}")

        repository_object = github_instance.get_repo(repo_name_part)
        logger.info(f"Successfully obtained repository object for: {repository_object.full_name}")
        app_config['EFFECTIVE_GITHUB_REPO_URL'] = repository_object.full_name
        return True
    except BadCredentialsException:
        logger.error("GitHub authentication failed: Bad credentials. Check your GITHUB_PAT.")
    except UnknownObjectException:
        logger.error(f"GitHub repository not found: {repo_url_full}. Check GITHUB_REPO_URL.")
    except GithubException as e:
        err_data = e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)
        logger.error(f"A GitHub API error occurred during initialization: {e.status} - {err_data}")
    except FileNotFoundError as e: # From load_app_config
        logger.error(f"Configuration file error: {e}")
    except ValueError as e: # From load_app_config
        logger.error(f"Configuration value error: {e}")
    except Exception as e:
        logger.error(f"An unexpected error occurred during GitHub services initialization: {e}")
    
    github_instance = None
    repository_object = None
    app_config['EFFECTIVE_GITHUB_REPO_URL'] = "NOT_CONFIGURED_ERROR_DURING_INIT"
    return False

# --- Tool Definitions ---
# These functions wrap your github_client calls and format outputs for the LLM.

def list_files_tool(path: str = "", branch: Optional[str] = None) -> dict:
    """Lists files and directories in a specified path of the configured GitHub repository.
    Args:
        path (str, optional): The directory path within the repository. Defaults to the root directory if empty.
        branch (Optional[str], optional): The name of the branch to query. If not provided, uses the repository's default branch.
    Returns:
        dict: A dictionary with 'status', 'result', and 'error_message'.
    """
    if not repository_object and not initialize_github_services():
        return {"status": "error", "error_message": "GitHub repository is not initialized. Please check server logs for configuration issues.", "result": None}
    
    items, error = github_client.list_repository_contents(repository_object, path, branch) # branch can be None here
    if error:
        return {"status": "error", "error_message": f"Error listing files at path '{path or '/'}': {error}", "result": None}
    if not items:
        return {"status": "success", "result": f"No items found in path '{path or '/'}' on branch '{branch or 'default'}'.", "error_message": None}
    
    return {"status": "success", "result": f"Files/directories in '{path or '/'}': {', '.join(items)}", "error_message": None}

def read_file_tool(file_path: str, branch: Optional[str] = None) -> dict:
    """Reads the content and SHA of a specific file in the configured GitHub repository.
    Args:
        file_path (str): The full path to the file within the repository.
        branch (Optional[str], optional): The name of the branch to query. If not provided, uses the repository's default branch.
    Returns:
        dict: A dictionary with 'status', 'result' (containing content and SHA), and 'error_message'.
    """
    if not repository_object and not initialize_github_services():
        return {"status": "error", "error_message": "GitHub repository is not initialized. Please check server logs for configuration issues.", "result": None}
    
    content, sha, error = github_client.read_repository_file(repository_object, file_path, branch) # branch can be None here
    if error:
        return {"status": "error", "error_message": f"Error reading file '{file_path}': {error}", "result": None}
    
    result_data = {
        "file_path": file_path,
        "sha": sha,
        "content": content
    }
    return {"status": "success", "result": result_data, "error_message": None}

def create_file_tool(file_path: str, commit_message: str, content: str, branch: Optional[str] = None) -> dict:
    """Creates a new file in the configured GitHub repository.
    Args:
        file_path (str): The full path for the new file.
        commit_message (str): The commit message for the file creation.
        content (str): The content of the new file. This must be the plain text content intended for the file.
        branch (Optional[str], optional): The branch where the file will be created. If not provided, uses the repository's default branch.
    Returns:
        dict: A dictionary with 'status', 'result', and 'error_message'.
    """
    if not repository_object and not initialize_github_services():
        return {"status": "error", "error_message": "GitHub repository is not initialized. Please check server logs for configuration issues.", "result": None}
    
    success, error = github_client.create_repository_file(repository_object, file_path, commit_message, content, branch) # branch can be None
    if error:
        return {"status": "error", "error_message": f"Error creating file '{file_path}': {error}", "result": None}
    
    if success:
        return {"status": "success", "result": f"Successfully created file '{file_path}'.", "error_message": None}
    else:
        return {"status": "error", "error_message": f"Failed to create file '{file_path}' (no specific error returned from client, check logs).", "result": None}

def update_file_tool(file_path: str, commit_message: str, new_content: str, sha: str, branch: Optional[str] = None) -> dict:
    """Updates an existing file in the configured GitHub repository.
    Args:
        file_path (str): The full path of the file to update.
        commit_message (str): The commit message for the file update.
        new_content (str): The new content for the file. This must be the new plain text content for the file.
        sha (str): The blob SHA of the file being replaced (obtained from read_file_tool).
        branch (Optional[str], optional): The branch where the file will be updated. If not provided, uses the repository's default branch.
    Returns:
        dict: A dictionary with 'status', 'result', and 'error_message'.
    """
    if not repository_object and not initialize_github_services():
        return {"status": "error", "error_message": "GitHub repository is not initialized. Please check server logs for configuration issues.", "result": None}
    
    success, error = github_client.update_repository_file(repository_object, file_path, commit_message, new_content, sha, branch) # branch can be None
    if error:
        return {"status": "error", "error_message": f"Error updating file '{file_path}': {error}", "result": None}

    if success:
        return {"status": "success", "result": f"Successfully updated file '{file_path}'.", "error_message": None}
    else:
        return {"status": "error", "error_message": f"Failed to update file '{file_path}' (no specific error returned from client, check logs).", "result": None}

def delete_file_tool(file_path: str, commit_message: str, sha: str, branch: Optional[str] = None) -> dict:
    """Deletes a file from the configured GitHub repository.
    Args:
        file_path (str): The full path of the file to delete.
        commit_message (str): The commit message for the file deletion.
        sha (str): The blob SHA of the file being deleted (obtained from read_file_tool).
        branch (Optional[str], optional): The branch from which the file will be deleted. If not provided, uses the repository's default branch.
    Returns:
        dict: A dictionary with 'status', 'result', and 'error_message'.
    """
    if not repository_object and not initialize_github_services():
        return {"status": "error", "error_message": "GitHub repository is not initialized. Please check server logs for configuration issues.", "result": None}
    
    success, error = github_client.delete_repository_file(repository_object, file_path, commit_message, sha, branch) # branch can be None
    if error:
        return {"status": "error", "error_message": f"Error deleting file '{file_path}': {error}", "result": None}

    if success:
        return {"status": "success", "result": f"Successfully deleted file '{file_path}'.", "error_message": None}
    else:
        return {"status": "error", "error_message": f"Failed to delete file '{file_path}' (no specific error returned from client, check logs).", "result": None}

# Attempt to initialize GitHub services when the module is loaded.
# The agent instruction will reflect the outcome of this initialization.
INITIALIZATION_SUCCESSFUL = initialize_github_services()
EFFECTIVE_REPO_URL = app_config.get('EFFECTIVE_GITHUB_REPO_URL', 'NOT_CONFIGURED_OR_INIT_FAILED')

_AGENT_INSTRUCTION = f"""
You are a helpful AI assistant that can interact with a specific GitHub repository: '{EFFECTIVE_REPO_URL}'.
Your primary functions are to list, read, create, update, and delete files in this repository.

Available Tools:
1. `list_files_tool(path: str = "", branch: Optional[str])`: Lists files and directories.
   - `path`: Optional. The directory path to list. Defaults to root if empty.
   - `branch`: Optional. The branch to query. If not provided, uses the repository's default branch.
2. `read_file_tool(file_path: str, branch: Optional[str])`: Reads a file's content and its SHA.
   - `file_path`: Required. The full path to the file.
   - `branch`: Optional. If not provided, uses the repository's default branch.
   - The SHA is crucial for updating or deleting the file. The tool returns a dictionary with 'file_path', 'sha', and 'content'.
3. `create_file_tool(file_path: str, commit_message: str, content: str, branch: Optional[str])`: Creates a new file.
   - `file_path`: Required.
   - `commit_message`: Required.
   - `content`: Required. This must be the plain text content intended for the file.
   - `branch`: Optional. If not provided, uses the repository's default branch.
4. `update_file_tool(file_path: str, commit_message: str, new_content: str, sha: str, branch: Optional[str])`: Updates an existing file.
   - `file_path`: Required.
   - `commit_message`: Required.
   - `new_content`: Required. This must be the new plain text content for the file.
   - `sha`: Required. The current SHA of the file (use `read_file_tool` to get this from the 'sha' field of its result).
   - `branch`: Optional. If not provided, uses the repository's default branch.
5. `delete_file_tool(file_path: str, commit_message: str, sha: str, branch: Optional[str])`: Deletes a file.
   - `file_path`: Required.
   - `commit_message`: Required.
   - `sha`: Required. The current SHA of the file (use `read_file_tool` to get this from the 'sha' field of its result).
   - `branch`: Optional. If not provided, uses the repository's default branch.

Interaction Flow:
- When a user asks to perform an action, first identify the correct tool.
- For the chosen tool, politely ask for any *required* parameters if they weren't provided. Be specific (e.g., "To create a file, I need the file path, a commit message, and the content.").
- For *optional* parameters (like 'path' for listing, or 'branch' for any tool), you can proactively ask for them. For example, if listing files, you could ask, "Which path would you like to list? (leave blank for root) And for which branch? (leave blank for the default branch)."
- For updates or deletions, explicitly state that you need the file's SHA. If the user doesn't provide it, suggest using `read_file_tool` first to obtain it. The SHA will be in the 'sha' field of the `read_file_tool` result.
- If an optional parameter like 'branch' is not provided by the user, you can omit it when calling the tool, and it will use the repository's default.
- Once all parameters are gathered, confirm the action and parameters before the system calls the tool.
- After the tool executes, the system will provide its output. This output will be a dictionary containing 'status' ('success' or 'error'), 'result' (the data if successful, which might be a string or a dictionary for `read_file_tool`), and 'error_message' (if an error occurred). Present this information clearly to the user.

{"If the GitHub repository is not configured correctly (current status: " + ("OK" if INITIALIZATION_SUCCESSFUL else "ERROR - " + EFFECTIVE_REPO_URL) + "), inform the user that you cannot perform GitHub actions due to a server-side configuration issue." if not INITIALIZATION_SUCCESSFUL else "The GitHub repository is configured and ready."}
Always be polite and helpful.
"""

agent = Agent(
    name="github_agent", # Must match the parent folder name for ADK discovery
    # model="gemini-1.5-flash-latest", # Or "gemini-1.0-pro", or other suitable model
    model="gemini-2.5-pro-preview-03-25",
    description="An agent that interacts with a pre-configured GitHub repository using specific tools.",
    instruction=_AGENT_INSTRUCTION,
    tools=[
        list_files_tool,
        read_file_tool,
        create_file_tool,
        update_file_tool,
        delete_file_tool
    ]
)

if __name__ == "__main__":
    logger.info("GitHub Agent (LLM-native style) script executed directly.")
    logger.info(f"GitHub services initialized: {INITIALIZATION_SUCCESSFUL}")
    logger.info(f"Effective Repo URL for agent: {EFFECTIVE_REPO_URL}")
    if not INITIALIZATION_SUCCESSFUL:
        logger.warning("Review .env configuration and server logs for initialization errors.")
