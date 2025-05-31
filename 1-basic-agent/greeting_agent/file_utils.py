def get_instruction(file_path_param):
    """
    Reads the content of a specified file.
    Prints the content if read successfully, or an error message otherwise.
    Returns the file content as a string, or None if an error occurs.
    """
    instruction_content = None  # Initialize to ensure a value is always returned
    try:
        with open(file_path_param, 'r') as file:
            instruction_content = file.read()
            # The print statements below are side effects.
            # You might consider moving them to the calling code (agent.py)
            # if you want this function purely to fetch data.
            print(f"--- Content loaded from {file_path_param} ---")
            print(instruction_content)
            print("------------------------------------------")
    except FileNotFoundError:
        print(f"Error: The file at {file_path_param} was not found.")
    except Exception as e:
        print(f"An error occurred while reading {file_path_param}: {e}")
    return instruction_content

