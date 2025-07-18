import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import agent_graph
from src.swarm import swarm_environment

def main():
    """Main function to run the agent.
    
    This function sets up a simple command-line interface to interact with the
    cognitive agent. It maintains the conversation state for a single session.
    """
    # Load environment variables from .env file
    load_dotenv()
    
    # Check if the Google API key is set
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        print("Please create a .env file and add your key, e.g., GOOGLE_API_KEY='YourAPIKeyHere'")
        return

    print("INFO: Cognitive Agent Initialized. Type 'exit' to quit.")
    
    # A simple configuration to manage the conversation state. 
    # For multi-user or persistent scenarios, this would be more sophisticated.
    config = {"configurable": {"thread_id": "user_session_1"}}

    # Timer for pheromone evaporation
    last_evaporation_time = time.time()
    evaporation_interval = 60 # seconds

    try:
        while True:
            # Perform evaporation periodically
            current_time = time.time()
            if current_time - last_evaporation_time > evaporation_interval:
                swarm_environment.evaporate()
                last_evaporation_time = current_time
                print("INFO: Pheromones evaporated.")

            user_input = input("You: ")
            if user_input.lower() == 'exit':
                break

            # The event stream allows us to see the agent's internal steps
            events = agent_graph.stream(
                {"messages": [HumanMessage(content=user_input)], "input": user_input},
                config,
                stream_mode="values",
            )

            # Print the agent's internal steps and final response
            for event in events:
                if "messages" in event:
                    event["messages"][-1].pretty_print()

    except KeyboardInterrupt:
        print("\nExiting...")
        break
    finally:
        # Ensure Neo4j connection is closed on exit
        swarm_environment.close()

if __name__ == "__main__":
    main()
