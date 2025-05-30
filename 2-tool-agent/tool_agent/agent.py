import datetime
from google.adk.agents import Agent
from google.adk.tools import google_search

def get_current_time() -> dict:
    """
    Get the current time in the format YYYY-MM-DD HH:MM:SS
    Get the day of the week
    """
    return {
        "current_time": datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "day_of_week" : datetime.datetime.now().weekday(),
    }

root_agent = Agent(
    name="tool_agent",
    model="gemini-1.5-flash-latest",
    # model="gemini-2.5-flash",
    description="Tool agent",
    instruction="""
    You are a helpful assistant that can use the following tools:
    - get-current-time
    """,
    # tools=[google_search],
    tools=[get_current_time],
    # tools=[google_search, get_current_time], # <--- Doesn't work
)
