import os
from dotenv import load_dotenv
import google.generativeai as genai
from google.generativeai.tools import Tool
from github import Github, GithubException


# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GITHUB_TOKEN = os.getenv("GITHUB_TOKEN")

genai.configure(api_key=GOOGLE_API_KEY)

# Initialize PyGithub client
g = None
if GITHUB_TOKEN:
    g = Github(GITHUB_TOKEN)

# --- Define GitHub API Tools ---
# Example: Tool to list repositories for a user

def get_user_repos(username: str) -> str:
    """Fetches public repositories for a given GitHub username."""
    print(f"Tool: Fetching repos for user {username}")
    if not g:
        return "Error: GitHub client not initialized. Please check GITHUB_TOKEN."

    try:
        user = g.get_user(username)
        repos = user.get_repos()
        repo_names = [repo.name for repo in repos]
        
        if not repo_names:
            return f"No public repositories found for user {username}."
        return f"Repositories for {username}: {', '.join(repo_names)}"
    except GithubException as e:
        if e.status == 404:
            return f"Error: User '{username}' not found on GitHub."
        return f"Error fetching repositories for {username}: {e.data.get('message', str(e))}"
    except Exception as e: # Catch any other unexpected errors
        return f"An unexpected error occurred: {str(e)}"

def get_specific_repo_info(owner: str, repo_name: str) -> str:
    """Fetches basic information for a specific repository (e.g., description)."""
    print(f"Tool: Fetching info for repo {owner}/{repo_name}")
    if not g:
        return "Error: GitHub client not initialized. Please check GITHUB_TOKEN."
    try:
        repo_full_name = f"{owner}/{repo_name}"
        repo = g.get_repo(repo_full_name)
        return f"Successfully accessed repo: {repo.full_name}. Description: {repo.description}"
    except GithubException as e:
        if e.status == 404:
            return f"Error: Repository '{owner}/{repo_name}' not found on GitHub."
        return f"Error fetching repository {owner}/{repo_name}: {e.data.get('message', str(e))}"
    except Exception as e:
        return f"An unexpected error occurred while fetching {owner}/{repo_name}: {str(e)}"

# You would define more tools here:
# - get_repo_issues(owner: str, repo: str) -> str
# - get_repo_readme(owner: str, repo: str) -> str
# - etc.

# --- Create the ADK Agent ---
# Note: Add get_specific_repo_info to tools if you want the agent to use it.
github_tools = [
    Tool.from_function(
        name="GetUserRepositories",
        description="Get a list of public repositories for a specific GitHub user.",
        fn=get_user_repos,
        # Define input schema if needed, e.g., using Pydantic
    ),
    # Tool.from_function(
    #     name="GetSpecificRepositoryInfo",
    #     description="Get basic information about a specific GitHub repository, like its description.",
    #     fn=get_specific_repo_info,
    #     # Define input schema if needed
    # ),
    # Add other tools here
]

# Configure the generative model
# You might want to use a model that's good at function calling
model = genai.GenerativeModel(
    model_name="gemini-1.5-flash-latest", # Or another suitable model
    tools=github_tools
)

github_agent = model # In ADK, the model configured with tools acts as the agent

print("GitHub ADK Agent initialized.")

if __name__ == '__main__':
    print("--- Running GitHub Agent Direct Tool Tests ---")

    if not GITHUB_TOKEN:
        print("ERROR: GITHUB_TOKEN not found in environment variables.")
        print("Please ensure your .env file is set up correctly with a valid GitHub Personal Access Token.")
    elif not g:
        print("ERROR: PyGithub client 'g' was not initialized. This might be due to a missing GITHUB_TOKEN.")
    else:
        print("GitHub client initialized successfully with a token.")
        
        # Test 1: GetUserRepositories tool
        print("\n--- Test 1: GetUserRepositories tool ---")
        test_username = "octocat"  # A well-known GitHub user for testing
        print(f"Attempting to fetch repositories for user: '{test_username}'")
        user_repos_info = get_user_repos(username=test_username)
        print(f"Result for '{test_username}':")
        print(user_repos_info)
        if "Error" not in user_repos_info and "No public repositories found" not in user_repos_info and user_repos_info:
            print(f"SUCCESS: Test 1: Successfully fetched repositories for '{test_username}'.")
        else:
            print(f"INFO: Test 1: Could not fetch repositories for '{test_username}' or an error occurred. Check message above.")

        # Test 2: GetSpecificRepoInfo (direct repo access test)
        print("\n--- Test 2: GetSpecificRepoInfo (Direct Repo Access Test) ---")
        # For this test, use a known public repository.
        # Example: https://github.com/octocat/Spoon-Knife -> owner="octocat", repo_name="Spoon-Knife"
        test_repo_owner = "octocat"
        test_repo_name = "Spoon-Knife"
        print(f"Attempting to fetch info for repository: '{test_repo_owner}/{test_repo_name}'")
        repo_info = get_specific_repo_info(owner=test_repo_owner, repo_name=test_repo_name)
        print(f"Result for '{test_repo_owner}/{test_repo_name}':")
        print(repo_info)

        if "Successfully accessed repo" in repo_info:
            print(f"SUCCESS: Test 2: Successfully accessed repository '{test_repo_owner}/{test_repo_name}'. GitHub API communication for specific repo is working.")
        else:
            print(f"INFO: Test 2: Could not access repository '{test_repo_owner}/{test_repo_name}'. Check error message above.")
            print("This could be due to network issues, an invalid/revoked GITHUB_TOKEN, API rate limits, or the repo being private/non-existent.")

        print("\n--- General Test Instructions ---")
        print("To test with your own GitHub user or repository (from a URL like https://github.com/owner/repo):")
        print("1. Ensure your GITHUB_TOKEN in the .env file is valid and has appropriate permissions.")
        print("2. For GetUserRepositories: Modify 'test_username' or call `get_user_repos('your-repo-owner-username')`.")
        print("3. For GetSpecificRepoInfo: Modify 'test_repo_owner' and 'test_repo_name', or call `get_specific_repo_info('owner', 'repo')`.")

    print("\n--- GitHub Agent Direct Tool Tests Complete ---")
