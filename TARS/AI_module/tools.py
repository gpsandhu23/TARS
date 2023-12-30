from langchain.agents import tool

# Create a simple custom tool to test the agent
@tool
def get_word_length(word: str) -> int:
    """Returns the length of a word."""
    return len(word)