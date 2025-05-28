# agent.py
from .config_loader import load_app_config
from .github_client import list_repository_contents, read_repository_file # Ensure this import is present
from github import Github, UnknownObjectException, BadCredentialsException # To install: pip install PyGithub

class GithubAgent:
    """
    Core agent for interacting with GitHub.
    """
    def __init__(self, app_config: dict):
        """
        Initializes the GithubAgent.

        Args:
            app_config (dict): Application configuration containing GITHUB_PAT and GITHUB_REPO_URL.
        """
        self.app_config = app_config
        self.github_pat = app_config.get('GITHUB_PAT')
        self.repo_url = app_config.get('GITHUB_REPO_URL')
        self.github_client = None
        self.repository_object = None

    def initialize_client(self) -> bool:
        """
        Initializes the GitHub client and fetches the repository object.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        if not self.github_pat:
            print("Error: GITHUB_PAT not found in configuration. Cannot initialize client.")
            return False
        if not self.repo_url:
            print("Error: GITHUB_REPO_URL not found in configuration. Cannot initialize client.")
            return False

        try:
            print(f"Attempting to authenticate with GitHub PAT (starts with: {self.github_pat[:4]}...).")
            self.github_client = Github(self.github_pat)
            # Test authentication by getting the authenticated user
            _ = self.github_client.get_user().login 
            print("GitHub client authenticated successfully.")

            repo_path = self.repo_url.replace("https://github.com/", "")
            print(f"Attempting to access repository: {repo_path}")
            self.repository_object = self.github_client.get_repo(repo_path)
            print(f"Successfully accessed repository: {self.repository_object.full_name}")
            return True
        except BadCredentialsException:
            print("Error: GitHub authentication failed. Check your GITHUB_PAT.")
            self.github_client = None
            return False
        except UnknownObjectException:
            print(f"Error: GitHub repository not found at '{self.repo_url}'. Check the GITHUB_REPO_URL.")
            self.github_client = None # Client might be valid, but repo is not
            self.repository_object = None
            return False
        except Exception as e:
            print(f"An unexpected error occurred during GitHub client initialization: {e}")
            self.github_client = None
            self.repository_object = None
            return False

    def get_tools(self) -> list:
        """Returns a list of tools available to the agent."""
        return [] # Placeholder for ADK tools

    def process_request(self, user_input: str) -> str:
        """Processes a user request."""
        if not self.github_client or not self.repository_object:
            print("GitHub client or repository object not initialized. Attempting to initialize...")
            if not self.initialize_client():
                return "Error: GithubAgent client could not be initialized. Please check configuration and credentials."
        
        command_input = user_input.lower().strip()

        if command_input.startswith("list files"):
            # Simple parsing: "list files /path/to/dir" or "list files"
            parts = user_input.strip().split(maxsplit=2) 
            path_to_list = ""
            if len(parts) > 2:
                path_to_list = parts[2].strip()
                # Remove leading/trailing slashes for consistency, as get_contents handles it
                path_to_list = path_to_list.strip('/')

            # Branch selection can be added later if needed, for now uses default
            items, error = list_repository_contents(self.repository_object, path=path_to_list)

            if error:
                return f"Error listing files: {error}"
            if not items:
                return f"No items found in '{path_to_list if path_to_list else 'root directory'}' or path does not exist."
            
            response = f"Contents of '{path_to_list if path_to_list else 'root directory'}':\n"
            for item_name in items:
                response += f"- {item_name}\n"
            return response.strip()
        elif command_input.startswith("read file"):
            parts = user_input.strip().split(maxsplit=2)
            if len(parts) < 3:
                return "Error: Please specify a file path to read. Usage: read file <path/to/file>"
            
            file_path_to_read = parts[2].strip().strip('/')

            content, error = read_repository_file(self.repository_object, file_path=file_path_to_read)

            if error:
                return f"Error reading file: {error}"
            if content is None: # Should be caught by error, but as a safeguard
                return f"Error: Could not retrieve content for '{file_path_to_read}' for an unknown reason."
            
            # For now, return the full content. Consider truncation for very large files.
            # Max length for display can be added here.
            max_display_length = 2000 
            if len(content) > max_display_length:
                return f"Content of '{file_path_to_read}' (truncated to {max_display_length} chars):\n---\n{content[:max_display_length]}\n---\n... (file is longer)"
            return f"Content of '{file_path_to_read}':\n---\n{content}\n---"
        else:
            return f"GithubAgent (repo: {self.repo_url}) received: '{user_input}'. Command not recognized. Try 'list files [path]' or 'read file <filepath>'."

if __name__ == "__main__":
    print("Testing GithubAgent...")
    try:
        config = load_app_config()
        agent = GithubAgent(app_config=config)
        # The initialize_client() is called by process_request if needed,
        # or you can call it explicitly here for an initial check.
        # if agent.initialize_client():
        #     print("Agent client initialized successfully during test setup.")
        # else:
        #     print("Agent client failed to initialize during test setup.")

        # Test the "list files" command
        print("\n--- Test 1: List files in root ---")
        response_root = agent.process_request("list files")
        print(f"Agent Response (root): {response_root}")

        # Example: Test listing files in a specific directory if you know one exists
        # print("\n--- Test 2: List files in a specific directory (e.g., 'src') ---")
        # response_src = agent.process_request("list files src") # Replace 'src' with an actual directory
        # print(f"Agent Response (src): {response_src}")

        print("\n--- Test 3: List files in a non-existent directory ---")
        response_non_existent = agent.process_request("list files non_existent_dir_for_testing_123")
        print(f"Agent Response (non_existent_dir): {response_non_existent}")

        print("\n--- Test 4: Read a file (e.g., README.md if it exists) ---")
        # Replace 'README.md' with an actual file in your test repository
        response_read_readme = agent.process_request("read file README.md") 
        print(f"Agent Response (read README.md): {response_read_readme}")

        print("\n--- Test 5: Read a non-existent file ---")
        response_read_non_existent = agent.process_request("read file non_existent_file_for_testing_123.txt")
        print(f"Agent Response (read non_existent_file): {response_read_non_existent}")

    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to load configuration for agent testing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during agent testing: {e}")
