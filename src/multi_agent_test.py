import os
import time
import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import agent_graph
from src.state import AgentState # Import AgentState
from src.swarm import swarm_environment
from src.memory import memory_system

def run_multi_agent_test(agents_data: list, test_name: str, disabled_agents: list = None):
    """
    Runs a multi-agent test scenario with a given set of agents and tasks.

    This function orchestrates the execution of multiple cognitive agents,
    allowing for the simulation of collaborative tasks, self-healing behaviors,
    and the observation of swarm dynamics. It also generates a visualization
    of concept strengths over time.

    Args:
        agents_data (list): A list of dictionaries, where each dictionary defines
                            an agent's properties: 'id', 'input' (initial task),
                            and 'concept_to_reinforce'.
        test_name (str): A unique name for the test run, used for logging and
                         naming the output visualization file.
        disabled_agents (list, optional): A list of agent IDs to be disabled
                                          during the test run, simulating agent failures.
                                          Defaults to None (no agents disabled).
    """
    if disabled_agents is None:
        disabled_agents = []
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logging.error("GOOGLE_API_KEY environment variable not set. Please set it in a .env file.")
        logging.info("Example: GOOGLE_API_KEY='YourActualGoogleAPIKey'")
        return

    logging.info(f"Multi-Agent Swarm Test Initialized for {test_name}.")

    

    # Periodically evaporate pheromones
    evaporation_interval = 30 # seconds
    last_evaporation_time = time.time()

    # Run fact-finding agents sequentially
    for i, agent_info in enumerate(agents_data):
        agent_id = agent_info["id"]
        agent_input = agent_info["input"]
        concept_to_reinforce = agent_info["concept_to_reinforce"]
        config = {"configurable": {"thread_id": agent_id}}

        if agent_id in disabled_agents:
            logging.warning(f"Agent {agent_id} is disabled. Skipping task.")
            continue # Skip the agent's task

        logging.info(f"\n--- Agent {agent_id} starting task: '{agent_input}' ---")

        strongest_concepts = swarm_environment.get_strongest_concepts()
        logging.info(f"Agent {agent_id} observes strongest concepts: {strongest_concepts}")

        initial_state_input = {"messages": [HumanMessage(content=agent_input)], "input": agent_input}

        final_state = agent_graph.invoke(
            initial_state_input,
            config,
        )

        if final_state and "messages" in final_state and final_state["messages"]:
            logging.info(f"--- Agent {agent_id} Output ---")
            final_state["messages"][-1].pretty_print()
            # Extract the fact and add it to the swarm environment
            # This is a simplification; a more robust solution would parse the LLM's output
            # to reliably extract the fact. For now, we assume the last message contains it.
            fact_content = final_state["messages"][-1].content
            # Use the new tool to add the fact to the swarm
            swarm_environment.add_fact(fact_content, agent_id)

        current_time = time.time()
        if current_time - last_evaporation_time > evaporation_interval:
            swarm_environment.evaporate()
            last_evaporation_time = current_time
            logging.info("Pheromones evaporated.")

        logging.info(f"\n--- Current Swarm State after Agent {agent_id} --- ")
        current_concepts = swarm_environment.get_strongest_concepts()
        logging.info(current_concepts)

        


    # After all fact-finding agents have run, create a summarization agent
    logging.info("\n--- Summarization Agent starting task ---")
    summary_agent_id = "agent_summarizer"
    # Modify the summary_input to instruct the agent to use get_facts_from_swarm
    summary_input = "Summarize the fun facts found by other agents. Use the 'get_facts_from_swarm' tool to retrieve all facts, then provide a concise summary of them."
    summary_config = {"configurable": {"thread_id": summary_agent_id}}

    initial_summary_state_input = {"messages": [HumanMessage(content=summary_input)], "input": summary_input}
    final_summary_state = agent_graph.invoke(
        initial_summary_state_input,
        summary_config,
    )

    if final_summary_state and "messages" in final_summary_state and final_summary_state["messages"]:
        logging.info(f"--- Agent {summary_agent_id} Output ---")
        final_summary_state["messages"][-1].pretty_print()

    logging.info("\n--- Multi-Agent Swarm Test Completed ---")
    memory_system.close() # Close DB connections

    

    print(f"\n--- Test '{test_name}' Completed ---")

    if __name__ == "__main__":
        # Task Sequence 1: Fun Facts
        logging.info("\n--- Running Task Sequence 1: Fun Facts ---")
        run_multi_agent_test(
            agents_data=[
                {"id": "agent_cat_fact", "input": "Find a fun fact about cats.",
    "concept_to_reinforce": "cats"},
                {"id": "agent_dog_fact", "input": "Find a fun fact about dogs.",
    "concept_to_reinforce": "dogs"},
                {"id": "agent_bird_fact", "input": "Find a fun fact about birds.",
    "concept_to_reinforce": "birds"}
            ],
            test_name="fun_facts"
        )

        # Task Sequence 2: Historical Events
        logging.info("\n--- Running Task Sequence 2: Historical Events ---")
        run_multi_agent_test(
            agents_data=[
                {"id": "agent_ww1_fact", "input": "Summarize a key event from World War 1.",
    "concept_to_reinforce": "ww1"},
                {"id": "agent_moon_landing_fact", "input": "Describe the significance of the moon landing.", "concept_to_reinforce": "moon_landing"}
            ],
            test_name="historical_events"
        )

        # Run a self-healing test (e.g., disable agent_dog_fact)
        # logging.info("\n\n--- Running Self-Healing Test (agent_dog_fact disabled) ---")
        # run_multi_agent_test(
        #     agents_data=[
        #         {"id": "agent_cat_fact", "input": "Find a fun fact about cats.","concept_to_reinforce": "cats"},
        #         {"id": "agent_dog_fact", "input": "Find a fun fact about dogs.","concept_to_reinforce": "dogs"},
        #         {"id": "agent_bird_fact", "input": "Find a fun fact about birds.","concept_to_reinforce": "birds"},
        #     ],
        #     test_name="self_healing_test",
        #     disabled_agents=["agent_dog_fact"]
        # )