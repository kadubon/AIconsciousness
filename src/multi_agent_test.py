import os
import time
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import agent_graph
from src.state import AgentState # Import AgentState
from src.swarm import swarm_environment

def run_multi_agent_test():
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        print("Error: GOOGLE_API_KEY environment variable not set.")
        return

    print("INFO: Multi-Agent Swarm Test Initialized.")

    # Define multiple agents and their initial tasks
    agents_data = [
        {"id": "agent_alpha", "input": "Find a fun fact about cats.", "concept_to_reinforce": "cats"},
        {"id": "agent_beta", "input": "Find a fun fact about dogs.", "concept_to_reinforce": "dogs"},
        {"id": "agent_gamma", "input": "Find a fun fact about birds.", "concept_to_reinforce": "birds"},
        {"id": "agent_delta", "input": "What are the strongest concepts in the swarm right now?", "concept_to_reinforce": "swarm_state"},
    ]

    # Periodically evaporate pheromones
    evaporation_interval = 30 # seconds
    last_evaporation_time = time.time()

    # Run agents sequentially for demonstration.
    # For true concurrency, this would involve threading/asyncio.
    for i, agent_info in enumerate(agents_data):
        agent_id = agent_info["id"]
        agent_input = agent_info["input"]
        concept_to_reinforce = agent_info["concept_to_reinforce"]
        config = {"configurable": {"thread_id": agent_id}}

        print(f"\n--- Agent {agent_id} starting task: '{agent_input}' ---")

        # Before starting, agent can check strongest concepts (simulating awareness of swarm state)
        strongest_concepts = swarm_environment.get_strongest_concepts()
        print(f"INFO: Agent {agent_id} observes strongest concepts: {strongest_concepts}")

        # Create an initial state dictionary with only messages
        initial_state = {
            "messages": [HumanMessage(content=agent_input)],
            "versions_seen": {"__start__": {}} # Explicitly add __start__ for langgraph
        }

        # Run the agent's graph
        events = agent_graph.stream(
            initial_state,
            config,
            stream_mode="values",
        )

        # Print agent's output
        for event in events:
            if "messages" in event:
                print(f"--- Agent {agent_id} Output --- ")
                event["messages"][-1].pretty_print()

        # After each agent's run, check for evaporation
        current_time = time.time()
        if current_time - last_evaporation_time > evaporation_interval:
            swarm_environment.evaporate()
            last_evaporation_time = current_time
            print("INFO: Pheromones evaporated.")

        # After each agent's run, show the current strongest concepts
        print(f"\n--- Current Swarm State after Agent {agent_id} --- ")
        print(swarm_environment.get_strongest_concepts())

    print("\n--- Multi-Agent Swarm Test Completed ---")
    swarm_environment.close() # Close Neo4j connection

if __name__ == "__main__":
    run_multi_agent_test()