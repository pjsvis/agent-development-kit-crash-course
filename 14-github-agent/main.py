# main.py
from github_agent.agent import GithubAgent
from github_agent.config_loader import load_app_config

APP_NAME = "CTX_GitHub_Assistant_v0.1"

def run_application():
    """
    Runs the main application loop for the GitHub Assistant.
    """
    print(f"--- Welcome to {APP_NAME} ---")

    try:
        print("Loading application configuration...")
        app_config = load_app_config()
        print("Configuration loaded successfully.")
    except (ValueError, FileNotFoundError) as e:
        print(f"Critical Error: Failed to load application configuration. {e}")
        print("Please ensure your .env file is correctly set up in the project root.")
        return

    print("Initializing GitHub Agent...")
    agent = GithubAgent(app_config=app_config)

    if not agent.initialize_client():
        print("Critical Error: Failed to initialize GitHub client in the agent.")
        print("Please check your GITHUB_PAT, GITHUB_REPO_URL, and network connectivity.")
        return
    print("GitHub Agent client initialized successfully.")

    print("\nStarting interactive session. Type 'exit' to quit.")
    try:
        while True:
            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break
            
            response = agent.process_request(user_input)
            print(f"CTX-GitHub: {response}")
    except KeyboardInterrupt:
        print("\nUser interrupted session.")
    finally:
        print(f"\n--- Shutting down {APP_NAME} ---")

if __name__ == "__main__":
    try:
        run_application()
    except Exception as e:
        print(f"An unexpected critical error occurred in the application: {e}")
        print("Application terminated.")
