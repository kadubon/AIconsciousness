import os
import time
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import agent_graph
from src.swarm import swarm_environment
from src.memory import memory_system

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def main():
    """
    Main function to run the interactive cognitive agent.

    This function initializes the agent, handles user input via a command-line
    interface, and manages the agent's interaction loop. It also periodically
    triggers pheromone evaporation in the swarm environment.
    """
    # Load environment variables from .env file. This should be done early.
    load_dotenv()
    
    # Ensure the GOOGLE_API_KEY is set for LLM interactions.
    if not os.getenv("GOOGLE_API_KEY"):
        logging.error("GOOGLE_API_KEY environment variable not set. Please set it in a .env file.")
        logging.info("Example: GOOGLE_API_KEY='YourActualGoogleAPIKey'")
        return

    logging.info("Cognitive Agent Initialized. Type 'exit' to quit the session.")
    
    # Configuration for the agent's state. 'thread_id' is used by the checkpointer
    # to uniquely identify and persist the conversation state for this session.
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
                logging.info("Pheromones evaporated.")

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
        logging.info("Exiting...")
    finally:
        # Ensure Neo4j connection is closed on exit
        memory_system.close()

if __name__ == "__main__":
    main()
