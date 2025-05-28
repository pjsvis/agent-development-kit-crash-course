# agent.py
from .config_loader import load_app_config
from .github_client import (
    list_repository_contents,
    read_repository_file,
    create_repository_file,
    update_repository_file,
    delete_repository_file
)
import google.generativeai as genai
from google.generativeai.types import HarmCategory, HarmBlockThreshold
from google.generativeai.tools import Tool
from github import Github, UnknownObjectException, BadCredentialsException # To install: pip install PyGithub

class GithubAgent:
    """
    Core agent for interacting with GitHub, powered by an LLM.
    """
    def __init__(self, app_config: dict):
        """
        Initializes the GithubAgent.

        Args:
            app_config (dict): Application configuration containing GITHUB_PAT, 
                               GITHUB_REPO_URL, and GOOGLE_API_KEY.
        """
        self.app_config = app_config
        self.github_pat = app_config.get('GITHUB_PAT')
        self.repo_url = app_config.get('GITHUB_REPO_URL')
        self.google_api_key = app_config.get('GOOGLE_API_KEY')

        self.github_client = None
        self.repository_object = None
        self.llm_model = None
        self.tools = []

        if not self.google_api_key:
            raise ValueError("GOOGLE_API_KEY not found in configuration. LLM features cannot be initialized.")
        genai.configure(api_key=self.google_api_key)


    def initialize_client(self) -> bool:
        """
        Initializes the GitHub client, fetches the repository object, and sets up LLM tools.

        Returns:
            bool: True if initialization was successful, False otherwise.
        """
        if not self.github_pat:
            print("Error: GITHUB_PAT not found in configuration. Cannot initialize GitHub client.")
            return False
        if not self.repo_url:
            print("Error: GITHUB_REPO_URL not found in configuration. Cannot initialize GitHub client.")
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
            
            # Initialize LLM and tools now that repository_object is available
            self._initialize_llm_and_tools()
            return True
        except BadCredentialsException:
            print("Error: GitHub authentication failed. Check your GITHUB_PAT.")
            self.github_client = None
            return False
        except UnknownObjectException:
            print(f"Error: GitHub repository not found at '{self.repo_url}'. Check the GITHUB_REPO_URL.")
            self.github_client = None 
            self.repository_object = None
            return False
        except Exception as e:
            print(f"An unexpected error occurred during GitHub client initialization: {e}")
            self.github_client = None
            self.repository_object = None
            return False

    def _initialize_llm_and_tools(self):
        """Initializes the LLM and defines tools based on github_client functions."""
        if not self.repository_object:
            print("Error: Cannot initialize LLM tools without a repository object.")
            return

        # --- Tool Wrapper Functions ---
        def list_contents_tool_wrapper(path: str = "", branch: str = None) -> str:
            """Lists files and directories in a specified path of the configured GitHub repository.
            Args:
                path (str, optional): The directory path within the repository. Defaults to the root.
                branch (str, optional): The branch to query. Defaults to the repository's default branch.
            """
            print(f"LLM Tool Invoked: list_repository_contents(path='{path}', branch='{branch}')")
            items, error = list_repository_contents(self.repository_object, path=path, branch=branch)
            if error:
                return f"Error listing files: {error}"
            if not items:
                return f"No items found in '{path if path else 'root directory'}'."
            return f"Contents of '{path if path else 'root directory'}':\n" + "\n".join([f"- {item}" for item in items])

        def read_file_tool_wrapper(file_path: str, branch: str = None) -> str:
            """Reads the content of a specific file in the configured GitHub repository.
            Args:
                file_path (str): The full path to the file within the repository.
                branch (str, optional): The branch to query. Defaults to the repository's default branch.
            """
            print(f"LLM Tool Invoked: read_repository_file(file_path='{file_path}', branch='{branch}')")
            content, error = read_repository_file(self.repository_object, file_path=file_path, branch=branch)
            if error:
                return f"Error reading file: {error}"
            if content is None:
                return "Error: Could not retrieve content for an unknown reason."
            max_display_length = 1500 
            if len(content) > max_display_length:
                return f"Content of '{file_path}' (truncated to {max_display_length} chars):\n---\n{content[:max_display_length]}\n---\n... (file is longer)"
            return f"Content of '{file_path}':\n---\n{content}\n---"
        
        def create_file_tool_wrapper(file_path: str, content: str, commit_message: str = None, branch: str = None) -> str:
            """Creates a new file in the configured GitHub repository.
            Args:
                file_path (str): The full path for the new file.
                content (str): The content of the new file.
                commit_message (str, optional): The commit message. Defaults to an agent-generated message.
                branch (str, optional): The branch where the file will be created. Defaults to the repository's default branch.
            """
            print(f"LLM Tool Invoked: create_repository_file(file_path='{file_path}', commit_message='{commit_message}', branch='{branch}')")
            if not commit_message:
                commit_message = f"Agent LLM: Create new file '{file_path}'"
            success, error = create_repository_file(self.repository_object, file_path=file_path, commit_message=commit_message, content=content, branch=branch)
            if error:
                return f"Error creating file: {error}"
            return f"Successfully created file: '{file_path}'"

        def update_file_tool_wrapper(file_path: str, new_content: str, commit_message: str = None, branch: str = None) -> str:
            """Updates an existing file in the configured GitHub repository.
            Args:
                file_path (str): The full path of the file to update.
                new_content (str): The new content for the file.
                commit_message (str, optional): The commit message. Defaults to an agent-generated message.
                branch (str, optional): The branch where the file will be updated. Defaults to the repository's default branch.
            """
            print(f"LLM Tool Invoked: update_repository_file(file_path='{file_path}', commit_message='{commit_message}', branch='{branch}')")
            try:
                file_object = self.repository_object.get_contents(file_path.strip('/'), ref=branch or self.repository_object.default_branch)
                if file_object.type == 'dir':
                     return f"Error: Cannot update '{file_path}'. It is a directory."
                current_sha = file_object.sha
            except UnknownObjectException:
                return f"Error: File '{file_path}' not found. Cannot update."
            except Exception as e:
                return f"Error fetching file SHA for update: {e}"

            if not commit_message:
                commit_message = f"Agent LLM: Update file '{file_path}'"
            success, error = update_repository_file(self.repository_object, file_path=file_path, commit_message=commit_message, new_content=new_content, sha=current_sha, branch=branch)
            if error:
                return f"Error updating file: {error}"
            return f"Successfully updated file: '{file_path}'"

        def delete_file_tool_wrapper(file_path: str, commit_message: str = None, branch: str = None) -> str:
            """Deletes a file from the configured GitHub repository.
            Args:
                file_path (str): The full path of the file to delete.
                commit_message (str, optional): The commit message. Defaults to an agent-generated message.
                branch (str, optional): The branch from which the file will be deleted. Defaults to the repository's default branch.
            """
            print(f"LLM Tool Invoked: delete_repository_file(file_path='{file_path}', commit_message='{commit_message}', branch='{branch}')")
            try:
                file_object = self.repository_object.get_contents(file_path.strip('/'), ref=branch or self.repository_object.default_branch)
                if file_object.type == 'dir':
                     return f"Error: Cannot delete '{file_path}'. It is a directory."
                current_sha = file_object.sha
            except UnknownObjectException:
                return f"Error: File '{file_path}' not found. Cannot delete."
            except Exception as e:
                return f"Error fetching file SHA for deletion: {e}"

            if not commit_message:
                commit_message = f"Agent LLM: Delete file '{file_path}'"
            success, error = delete_repository_file(self.repository_object, file_path=file_path, commit_message=commit_message, sha=current_sha, branch=branch)
            if error:
                return f"Error deleting file: {error}"
            return f"Successfully deleted file: '{file_path}'"

        self.tools = [
            Tool.from_function(fn=list_contents_tool_wrapper, name="list_repository_contents", description="Lists files and directories in a specified path of the configured GitHub repository."),
            Tool.from_function(fn=read_file_tool_wrapper, name="read_repository_file", description="Reads the content of a specific file in the configured GitHub repository."),
            Tool.from_function(fn=create_file_tool_wrapper, name="create_repository_file", description="Creates a new file in the configured GitHub repository. Requires file_path and content. Commit message is optional."),
            Tool.from_function(fn=update_file_tool_wrapper, name="update_repository_file", description="Updates an existing file in the configured GitHub repository. Requires file_path and new_content. Commit message is optional."),
            Tool.from_function(fn=delete_file_tool_wrapper, name="delete_repository_file", description="Deletes a file from the configured GitHub repository. Requires file_path. Commit message is optional."),
        ]
        
        self.llm_model = genai.GenerativeModel(
            model_name="gemini-1.5-flash-latest", 
            tools=self.tools,
            safety_settings={
                HarmCategory.HARM_CATEGORY_HARASSMENT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_HATE_SPEECH: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_SEXUALLY_EXPLICIT: HarmBlockThreshold.BLOCK_NONE,
                HarmCategory.HARM_CATEGORY_DANGEROUS_CONTENT: HarmBlockThreshold.BLOCK_NONE,
            },
            system_instruction=(
                "You are a helpful GitHub assistant. You can interact with a GitHub repository "
                "to list files, read files, create files, update files, and delete files. "
                "When creating, updating, or deleting files, if the user doesn't provide a commit message, "
                "you should generate a simple one like 'Agent LLM: [action] file [filename]'."
            )
        )
        print("LLM and tools initialized successfully.")

    def get_tools(self) -> list:
        """Returns a list of tools available to the agent."""
        return self.tools

    def process_request(self, user_input: str) -> str:
        """Processes a user request using the LLM and defined tools."""
        if not self.llm_model: 
            print("LLM model not initialized. Attempting to initialize GitHub client and LLM tools...")
            if not self.initialize_client(): # This will also call _initialize_llm_and_tools
                return "Error: GithubAgent client and LLM could not be initialized. Please check configuration and credentials."
            if not self.llm_model: # Check again if LLM init failed within initialize_client
                 return "Error: LLM model could not be initialized even after client setup."

        try:
            print(f"Sending to LLM: '{user_input}'")
            # For multi-turn conversations, you would use:
            # chat = self.llm_model.start_chat(enable_automatic_function_calling=True)
            # response = chat.send_message(user_input)
            # For single turn with automatic function calling:
            response = self.llm_model.generate_content(
                user_input,
                # generation_config=genai.types.GenerationConfig(
                #     # Only one candidate for now.
                #     candidate_count=1) # Optional: if you want to force one candidate
            )
            
            # The response.text should contain the final textual answer after tool calls.
            # The genai library handles the loop of calling tools and feeding results back to the model.
            if response.candidates and response.candidates[0].content.parts:
                final_response_text = "".join(part.text for part in response.candidates[0].content.parts if hasattr(part, 'text'))
                if final_response_text:
                    print(f"LLM Response Text: {final_response_text.strip()}")
                    return final_response_text.strip()
                else:
                    # This might happen if the LLM only made a function call and didn't provide subsequent text.
                    # The ADK usually ensures a textual response after tool calls.
                    # Let's check if there was a function call that might explain the empty text.
                    for part in response.candidates[0].content.parts:
                        if hasattr(part, 'function_call'):
                            return f"LLM initiated a tool call: {part.function_call.name}. The tool's output should have been processed and a summary provided by the LLM. If no summary, this might indicate an issue or the tool call itself was the final action."
                    return "LLM processed the request but returned no direct textual response. This might be normal if a tool was called and its output is the answer, or it could indicate an issue."
            else:
                # This could be due to safety settings blocking the response, or other issues.
                print(f"LLM did not return a valid response structure. Prompt feedback: {response.prompt_feedback}")
                return "LLM did not return a valid response. It might have been blocked or an error occurred."

        except Exception as e:
            print(f"Error during LLM processing or tool execution: {e}")
            import traceback
            traceback.print_exc() # For more detailed debugging
            return f"An error occurred while processing your request with the LLM: {str(e)}"

if __name__ == "__main__":
    print("Testing GithubAgent with LLM integration...")
    try:
        config = load_app_config()
        agent = GithubAgent(app_config=config)

        # Initialize client and LLM tools explicitly for testing if __name__ == "__main__"
        if not agent.llm_model:
            print("Initializing client and LLM for testing...")
            if not agent.initialize_client():
                print("Failed to initialize agent for testing. Exiting.")
                exit()
        
        print("\nAgent initialized. Run main.py to interact with the LLM-powered agent.")
        print("Example queries you can try when running main.py:")
        print("  - list files in the root directory")
        print("  - what is in the src folder")
        print("  - read the README.md file")
        print("  - create a file named 'todo.txt' with content 'Buy milk'")
        print("  - update the file 'todo.txt' and add 'Pay bills'")
        print("  - delete the file 'todo.txt'")
        
        # Example of a direct test if needed (though interactive via main.py is better)
        # print("\n--- Direct Test Example ---")
        # test_query = "list files in the root"
        # print(f"You: {test_query}")
        # test_response = agent.process_request(test_query)
        # print(f"CTX-GitHub: {test_response}")


    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to load configuration for agent testing: {e}")
    except Exception as e:
        print(f"An unexpected error occurred during agent testing: {e}")
        import traceback
        traceback.print_exc()
