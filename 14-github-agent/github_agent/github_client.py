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
        error_msg = f"A GitHub API error occurred while listing repository contents for path '{normalized_path if normalized_path else '/'}': {e.status} - {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
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
        error_msg = f"A GitHub API error occurred while reading file '{normalized_file_path}': {e.status} - {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return None, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while reading file '{normalized_file_path}': {str(e)}"
        print(error_msg)
        return None, error_msg

def create_repository_file(repository_object, file_path: str, commit_message: str, content: str, branch: str = None) -> tuple[bool, str | None]:
    """
    Creates a new file in a GitHub repository.

    Args:
        repository_object: An authenticated PyGithub Repository object.
        file_path (str): The full path for the new file within the repository.
        commit_message (str): The commit message for the file creation.
        content (str): The content of the new file.
        branch (str, optional): The name of the branch where the file will be created.
                                Defaults to None, which means PyGithub will use
                                the repository's default branch.

    Returns:
        tuple[bool, str | None]: A tuple containing:
            - bool: True if the file was created successfully, False otherwise.
            - str: An error message string if an error occurred, otherwise None.
    """
    if not repository_object:
        return False, "Repository object is not initialized."
    if not file_path:
        return False, "File path cannot be empty."
    if not commit_message:
        return False, "Commit message cannot be empty."
    # Content can be empty for an empty file.

    try:
        normalized_file_path = file_path.strip('/')
        ref_to_use = branch if branch else repository_object.default_branch

        print(f"Attempting to create file='{normalized_file_path}' with commit='{commit_message}' on branch='{ref_to_use}' in repo '{repository_object.full_name}'...")
        
        # The create_file method returns a dict with 'content' (ContentFile) and 'commit' (Commit)
        created_file_info = repository_object.create_file(
            path=normalized_file_path,
            message=commit_message,
            content=content,          
            branch=ref_to_use
        )
        
        print(f"Successfully created file '{normalized_file_path}' via commit {created_file_info['commit'].sha[:7]}.")
        return True, None
    except GithubException as e:
        # Common statuses: 422 (Unprocessable Entity - often if file exists or path issue)
        # 409 (Conflict - though create_file usually raises 422 if file exists)
        error_msg = f"A GitHub API error occurred while creating file '{normalized_file_path}': {e.status} - {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while creating file '{normalized_file_path}': {str(e)}"
        print(error_msg)
        return False, error_msg

def update_repository_file(repository_object, file_path: str, commit_message: str, new_content: str, sha: str, branch: str = None) -> tuple[bool, str | None]:
    """
    Updates an existing file in a GitHub repository.

    Args:
        repository_object: An authenticated PyGithub Repository object.
        file_path (str): The full path of the file to update.
        commit_message (str): The commit message for the file update.
        new_content (str): The new content for the file.
        sha (str): The blob SHA of the file being replaced.
        branch (str, optional): The name of the branch where the file will be updated.
                                Defaults to None, which means PyGithub will use
                                the repository's default branch.

    Returns:
        tuple[bool, str | None]: A tuple containing:
            - bool: True if the file was updated successfully, False otherwise.
            - str: An error message string if an error occurred, otherwise None.
    """
    if not repository_object:
        return False, "Repository object is not initialized."
    if not file_path:
        return False, "File path cannot be empty."
    if not commit_message:
        return False, "Commit message cannot be empty."
    if not sha:
        return False, "File SHA (blob SHA) is required for an update."

    try:
        normalized_file_path = file_path.strip('/')
        ref_to_use = branch if branch else repository_object.default_branch

        print(f"Attempting to update file='{normalized_file_path}' with commit='{commit_message}' on branch='{ref_to_use}' (SHA: {sha[:7]})...")
        
        updated_file_info = repository_object.update_file(
            path=normalized_file_path,
            message=commit_message,
            content=new_content,
            sha=sha,
            branch=ref_to_use
        )
        
        print(f"Successfully updated file '{normalized_file_path}' via commit {updated_file_info['commit'].sha[:7]}.")
        return True, None
    except GithubException as e:
        # Common statuses: 404 (Not Found - if file or SHA is wrong), 409 (Conflict - if SHA doesn't match current file state)
        error_msg = f"A GitHub API error occurred while updating file '{normalized_file_path}': {e.status} - {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while updating file '{normalized_file_path}': {str(e)}"
        print(error_msg)
        return False, error_msg

def delete_repository_file(repository_object, file_path: str, commit_message: str, sha: str, branch: str = None) -> tuple[bool, str | None]:
    """
    Deletes a file from a GitHub repository.

    Args:
        repository_object: An authenticated PyGithub Repository object.
        file_path (str): The full path of the file to delete.
        commit_message (str): The commit message for the file deletion.
        sha (str): The blob SHA of the file being deleted.
        branch (str, optional): The name of the branch from which the file will be deleted.
                                Defaults to None, which means PyGithub will use
                                the repository's default branch.

    Returns:
        tuple[bool, str | None]: A tuple containing:
            - bool: True if the file was deleted successfully, False otherwise.
            - str: An error message string if an error occurred, otherwise None.
    """
    if not repository_object:
        return False, "Repository object is not initialized."
    if not file_path:
        return False, "File path cannot be empty."
    if not commit_message:
        return False, "Commit message cannot be empty."
    if not sha:
        return False, "File SHA (blob SHA) is required for deletion."

    try:
        normalized_file_path = file_path.strip('/')
        ref_to_use = branch if branch else repository_object.default_branch

        print(f"Attempting to delete file='{normalized_file_path}' with commit='{commit_message}' on branch='{ref_to_use}' (SHA: {sha[:7]})...")
        
        deleted_file_info = repository_object.delete_file(
            path=normalized_file_path,
            message=commit_message,
            sha=sha,
            branch=ref_to_use
        )
        print(f"Successfully deleted file '{normalized_file_path}' via commit {deleted_file_info['commit'].sha[:7]}.")
        return True, None
    except GithubException as e:
        # Common statuses: 404 (Not Found - if file or SHA is wrong), 409 (Conflict - if SHA doesn't match current file state)
        error_msg = f"A GitHub API error occurred while deleting file '{normalized_file_path}': {e.status} - {e.data.get('message', str(e)) if hasattr(e, 'data') and isinstance(e.data, dict) else str(e)}"
        print(error_msg)
        return False, error_msg
    except Exception as e:
        error_msg = f"An unexpected error occurred while deleting file '{normalized_file_path}': {str(e)}"
        print(error_msg)
        return False, error_msg

if __name__ == "__main__":
    print("github_client.py module loaded.")
    print("This module provides functions to interact with GitHub.")
    print("To test functions here, you need an authenticated Repository object,")
    print("typically managed and passed by the GithubAgent.")
