from AI_module.agent import process_user_task

# Initialize chat_history
chat_history = []

while True:
    # Get user input
    user_task = input("Enter your query (or type 'exit' to quit): ")
    
    # Check if the user wants to exit
    if user_task.lower() == 'exit':
        break

    # Call the function from agent.py and pass chat_history
    agent_response = process_user_task(user_task, chat_history)
    
    # Display the result
    print("Agent Response:", agent_response)