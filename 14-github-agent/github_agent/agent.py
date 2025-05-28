# agent.py
from .config_loader import load_app_config
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
            print("GitHub client not initialized. Attempting to initialize...")
            if not self.initialize_client():
                return "Error: GithubAgent client could not be initialized. Please check configuration and credentials."
        
        return f"GithubAgent (repo: {self.repo_url}) received: '{user_input}'. Client initialized. (Processing logic TBD)"

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

        response = agent.process_request("list files in the root directory")
        print(f"\nAgent Response: {response}")

    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to load configuration for agent testing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during agent testing: {e}")