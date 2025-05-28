# github_client.py
# This module will contain functions to interact with the GitHub API using PyGithub.

from github import UnknownObjectException, RateLimitExceededException, GithubException
# Note: The `Github` class itself (for client instantiation) and `BadCredentialsException`
# are typically handled in the agent.py where the client is initialized and managed.

def list_repository_contents(repository_object, path: str = "", branch: str = None):
    """
    Lists files and directories in a specified path of a GitHub repository.

    Args:
        repository_object: An authenticated PyGithub Repository object.
        path (str, optional): The directory path within the repository.
                              Defaults to the root directory ("").
                              Leading/trailing slashes are handled.
        branch (str, optional): The name of the branch to query.
                                Defaults to None, which means PyGithub will use
                                the repository's default branch.

    Returns:
        list: A list of strings, where each string is the name of a file
              or directory in the specified path.
        str: An error message string if an error occurred, otherwise None.
             Returns an empty list and an error message on failure.
    """
    if not repository_object:
        return [], "Repository object is not initialized."

    try:
        # Normalize path: remove leading/trailing slashes as get_contents handles it
        normalized_path = path.strip('/')
        ref_to_use = branch if branch else repository_object.default_branch

        print(f"Attempting to list contents for path='{normalized_path}' on branch='{ref_to_use}' in repo '{repository_object.full_name}'...")
        contents = repository_object.get_contents(normalized_path, ref=ref_to_use)
        
        item_names = [content_file.name for content_file in contents]
        
        print(f"Successfully listed {len(item_names)} items in '{normalized_path if normalized_path else '/'}' on branch '{ref_to_use}'.")
        return item_names, None
    except UnknownObjectException:
        error_msg = f"Error: Path '{normalized_path if normalized_path else '/'}' not found in repository on branch '{ref_to_use}'."
        print(error_msg)
        return [], error_msg
    except RateLimitExceededException:
        error_msg = "GitHub API rate limit exceeded. Please try again later."
        print(error_msg)
        return [], error_msg
    except GithubException as e: # Catch other PyGithub specific errors
        error_msg = f"A GitHub API error occurred while listing repository contents for path '{normalized_path if normalized_path else '/'}': {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return [], error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while listing repository contents for path '{normalized_path if normalized_path else '/'}': {str(e)}"
        print(error_msg)
        return [], error_msg

def read_repository_file(repository_object, file_path: str, branch: str = None) -> tuple[str | None, str | None]:
    """
    Reads the content of a specific file in a GitHub repository.

    Args:
        repository_object: An authenticated PyGithub Repository object.
        file_path (str): The full path to the file within the repository.
        branch (str, optional): The name of the branch to query.
                                Defaults to None, which means PyGithub will use
                                the repository's default branch.

    Returns:
        tuple[str | None, str | None]: A tuple containing:
            - str: The decoded content of the file if successful.
            - str: An error message string if an error occurred, otherwise None.
            Returns (None, error_message) on failure.
    """
    if not repository_object:
        return None, "Repository object is not initialized."
    if not file_path:
        return None, "File path cannot be empty."

    try:
        # Normalize path: remove leading/trailing slashes as get_contents handles it
        normalized_file_path = file_path.strip('/')
        ref_to_use = branch if branch else repository_object.default_branch

        print(f"Attempting to read file='{normalized_file_path}' on branch='{ref_to_use}' in repo '{repository_object.full_name}'...")
        content_file = repository_object.get_contents(normalized_file_path, ref=ref_to_use)

        if content_file.type == 'dir':
            error_msg = f"Error: Path '{normalized_file_path}' is a directory, not a file."
            print(error_msg)
            return None, error_msg
        
        decoded_content = content_file.decoded_content.decode('utf-8')
        print(f"Successfully read file '{normalized_file_path}'. Content length: {len(decoded_content)} bytes.")
        return decoded_content, None
    except UnknownObjectException:
        error_msg = f"Error: File '{normalized_file_path}' not found in repository on branch '{ref_to_use}'."
        print(error_msg)
        return None, error_msg
    except RateLimitExceededException:
        error_msg = "GitHub API rate limit exceeded. Please try again later."
        print(error_msg)
        return None, error_msg
    except GithubException as e: # Catch other PyGithub specific errors
        error_msg = f"A GitHub API error occurred while reading file '{normalized_file_path}': {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while reading file '{normalized_file_path}': {str(e)}"
        print(error_msg)
        return None, error_msg

if __name__ == "__main__":
    print("github_client.py module loaded.")
    print("This module provides functions to interact with GitHub.")
    print("To test list_repository_contents, you need an authenticated Repository object,")
    print("typically managed and passed by the GithubAgent. Same for read_repository_file.")
