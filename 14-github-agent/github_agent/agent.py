# agent.py
from .config_loader import load_app_config
from .github_client import list_repository_contents, read_repository_file, create_repository_file, update_repository_file, delete_repository_file # Ensure all necessary imports are present
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
            
            max_display_length = 2000 
            if len(content) > max_display_length:
                return f"Content of '{file_path_to_read}' (truncated to {max_display_length} chars):\n---\n{content[:max_display_length]}\n---\n... (file is longer)"
            return f"Content of '{file_path_to_read}':\n---\n{content}\n---"
        elif command_input.startswith("create file"):
            # Command format: create file <filepath> <content for the file>
            parts = user_input.strip().split(maxsplit=3)
            if len(parts) < 4: # "create", "file", "<filepath>", "<content>"
                return "Error: Insufficient arguments. Usage: create file <filepath> <content>"
            
            file_path_to_create = parts[2].strip().strip('/')
            file_content = parts[3] # The rest of the string is content

            if not file_path_to_create:
                return "Error: File path for creation cannot be empty."

            commit_message = f"Agent: Create new file '{file_path_to_create}'"

            success, error = create_repository_file(
                self.repository_object, 
                file_path=file_path_to_create, 
                commit_message=commit_message, 
                content=file_content
            )
            if success:
                return f"Successfully created file: '{file_path_to_create}'"
            else:
                return f"Error creating file: {error}"
        elif command_input.startswith("update file"):
             # Command format: update file <filepath> <new content for the file>
            parts = user_input.strip().split(maxsplit=3)
            if len(parts) < 4: # "update", "file", "<filepath>", "<new content>"
                return "Error: Insufficient arguments. Usage: update file <filepath> <new content>"
            
            file_path_to_update = parts[2].strip().strip('/')
            new_file_content = parts[3] # The rest of the string is new content

            if not file_path_to_update:
                return "Error: File path for update cannot be empty."

            # To update, we first need the file's current SHA
            # We can reuse the read_repository_file logic to get the file object which contains the SHA
            try:
                file_object = self.repository_object.get_contents(file_path_to_update, ref=self.repository_object.default_branch)
                if file_object.type == 'dir':
                     return f"Error: Cannot update '{file_path_to_update}'. It is a directory, not a file."
                current_sha = file_object.sha
            except UnknownObjectException:
                return f"Error: File '{file_path_to_update}' not found. Cannot update."
            except Exception as e:
                return f"Error fetching file info for update: {e}"

            commit_message = f"Agent: Update file '{file_path_to_update}'"

            success, error = update_repository_file(
                self.repository_object, 
                file_path=file_path_to_update, 
                commit_message=commit_message, 
                new_content=new_file_content,
                sha=current_sha
            )
            if success:
                return f"Successfully updated file: '{file_path_to_update}'"
            else:
                return f"Error updating file: {error}"
        elif command_input.startswith("delete file"):
            # Command format: delete file <filepath>
            parts = user_input.strip().split(maxsplit=2)
            if len(parts) < 3: # "delete", "file", "<filepath>"
                return "Error: Please specify a file path to delete. Usage: delete file <filepath>"
            
            file_path_to_delete = parts[2].strip().strip('/')

            if not file_path_to_delete:
                return "Error: File path for deletion cannot be empty."

            # To delete, we first need the file's current SHA
            try:
                file_object = self.repository_object.get_contents(file_path_to_delete, ref=self.repository_object.default_branch)
                if file_object.type == 'dir':
                     return f"Error: Cannot delete '{file_path_to_delete}'. It is a directory, not a file."
                current_sha = file_object.sha
            except UnknownObjectException:
                return f"Error: File '{file_path_to_delete}' not found. Cannot delete."
            except Exception as e:
                return f"Error fetching file info for deletion: {e}"

            commit_message = f"Agent: Delete file '{file_path_to_delete}'"

            success, error = delete_repository_file(
                self.repository_object, 
                file_path=file_path_to_delete, 
                commit_message=commit_message, 
                sha=current_sha
            )
            if success:
                return f"Successfully deleted file: '{file_path_to_delete}'"
            else:
                return f"Error deleting file: {error}"
        else:
            return f"GithubAgent (repo: {self.repo_url}) received: '{user_input}'. Command not recognized. Try 'list files [path]', 'read file <filepath>', 'create file <filepath> <content>', 'update file <filepath> <new content>', or 'delete file <filepath>'."

if __name__ == "__main__":
    print("Testing GithubAgent...")
    try:
        config = load_app_config()
        agent = GithubAgent(app_config=config)

        print("\n--- Test 1: List files in root ---")
        response_root = agent.process_request("list files")
        print(f"Agent Response (root): {response_root}")

        print("\n--- Test 3: List files in a non-existent directory ---")
        response_non_existent = agent.process_request("list files non_existent_dir_for_testing_123")
        print(f"Agent Response (non_existent_dir): {response_non_existent}")

        print("\n--- Test 4: Read a file (e.g., README.md if it exists) ---")
        response_read_readme = agent.process_request("read file README.md") 
        print(f"Agent Response (read README.md): {response_read_readme}")

        print("\n--- Test 5: Read a non-existent file ---")
        response_read_non_existent = agent.process_request("read file non_existent_file_for_testing_123.txt")
        print(f"Agent Response (read non_existent_file): {response_read_non_existent}")

        # --- Tests for Create, Update, Delete ---
        # Define a unique file path for testing CUD operations
        test_cud_file_path = "agent_test_cud/temp_file_by_agent.txt"
        initial_content = "This is the initial content."
        updated_content = "This content has been updated by the agent."

        print(f"\n--- Test 6: Create a new file ('{test_cud_file_path}') ---")
        # Note: This will actually create a file in your test repository.
        # Ensure your GITHUB_PAT has write permissions.
        response_create_file = agent.process_request(f"create file {test_cud_file_path} {initial_content}")
        print(f"Agent Response (create file): {response_create_file}")
        
        # Only proceed with update/delete if creation was successful
        if "Successfully created file" in response_create_file:
            print(f"\n--- Test 7: Read the newly created file ('{test_cud_file_path}') ---")
            response_read_new_file = agent.process_request(f"read file {test_cud_file_path}")
            print(f"Agent Response (read new file): {response_read_new_file}")

            print(f"\n--- Test 8: Update the file ('{test_cud_file_path}') ---")
            response_update_file = agent.process_request(f"update file {test_cud_file_path} {updated_content}")
            print(f"Agent Response (update file): {response_update_file}")

            # Optional: Read again after update to verify
            if "Successfully updated file" in response_update_file:
                 print(f"\n--- Test 8b: Read the updated file ('{test_cud_file_path}') ---")
                 response_read_updated_file = agent.process_request(f"read file {test_cud_file_path}")
                 print(f"Agent Response (read updated file): {response_read_updated_file}")

            print(f"\n--- Test 9: Delete the file ('{test_cud_file_path}') ---")
            response_delete_file = agent.process_request(f"delete file {test_cud_file_path}")
            print(f"Agent Response (delete file): {response_delete_file}")

            # Optional: Try reading after delete to confirm it's gone
            if "Successfully deleted file" in response_delete_file:
                 print(f"\n--- Test 9b: Read the deleted file ('{test_cud_file_path}') ---")
                 response_read_deleted_file = agent.process_request(f"read file {test_cud_file_path}")
                 print(f"Agent Response (read deleted file): {response_read_deleted_file}")

        else:
            print(f"\nSkipping update and delete tests because file creation failed.")


    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to load configuration for agent testing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during agent testing: {e}")
