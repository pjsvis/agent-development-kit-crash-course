# d:\dev\agent-development-kit-crash-course\14-github-agent\github_agent\__init__.py

# This line imports the 'agent' variable from your github_agent.py file
# (which is in the same directory as this __init__.py) and makes it
# available when the 'github_agent' package is imported.
from .github_agent import agent

# You can also expose other elements if needed, for example:
# from .config_loader import load_app_config
# from .github_client import list_repository_contents

# This ensures that when the ADK does something like:
#   import github_agent as agent_module
#   actual_agent_instance = agent_module.agent
# it will find the 'agent' instance you defined in github_agent/github_agent.py.
