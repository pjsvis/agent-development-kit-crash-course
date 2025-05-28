# config_loader.py
import os
from pathlib import Path
from dotenv import load_dotenv # To install: pip install python-dotenv

def load_app_config():
    """
    Loads application configuration from a .env file located in the project root.

    Raises:
        ValueError: If any of the required environment variables are not set.
        FileNotFoundError: If the .env file is not found at the expected path.

    Returns:
        dict: A dictionary containing the loaded configuration values.
    """
    # Assumes .env file is in the parent directory of this script's directory
    # (i.e., at the project root `14-github-agent/`)
    env_path = Path(__file__).resolve().parent.parent / '.env'

    if not env_path.exists():
        error_message = f"Configuration error: .env file not found at {env_path}"
        print(error_message)
        raise FileNotFoundError(error_message)

    try:
        load_dotenv(dotenv_path=env_path)
    except Exception as e:
        # This catches errors during the loading of the .env file itself
        error_message = f"Error loading .env file from {env_path}: {e}"
        print(error_message)
        raise  # Re-raise the exception as this is a critical failure

    REQUIRED_KEYS = ['GITHUB_PAT', 'GOOGLE_API_KEY', 'GITHUB_REPO_URL']
    config_values = {}

    for key in REQUIRED_KEYS:
        value = os.getenv(key)
        if value is None:
            error_message = f"Configuration error: Environment variable '{key}' not found. Expected in {env_path}."
            print(error_message)
            raise ValueError(error_message)
        config_values[key] = value

    return config_values

if __name__ == "__main__":
    print("Testing config_loader.py...")
    try:
        config = load_app_config()
        print("\nConfiguration loaded successfully:")
        print(f"  GITHUB_PAT: {config.get('GITHUB_PAT', '')[:4]}...")
        print(f"  GOOGLE_API_KEY: {config.get('GOOGLE_API_KEY', '')[:4]}...")
        print(f"  GITHUB_REPO_URL: {config.get('GITHUB_REPO_URL')}")
    except (ValueError, FileNotFoundError) as e:
        print(f"Failed to load application configuration: {e}")