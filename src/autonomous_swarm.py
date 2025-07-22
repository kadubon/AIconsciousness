import os
import time
import logging
from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.graph import agent_graph
from src.swarm import swarm_environment
from src.memory import memory_system
from src.tools import add_task_to_swarm, get_available_tasks_from_swarm, mark_task_completed_in_swarm

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def run_autonomous_swarm(num_agents: int = 3, max_iterations: int = 10):
    """
    Runs an autonomous multi-agent swarm simulation.

    Args:
        num_agents (int): The number of agents in the swarm.
        max_iterations (int): The maximum number of iterations for the swarm to run.
    """
    load_dotenv()
    if not os.getenv("GOOGLE_API_KEY"):
        logging.error("GOOGLE_API_KEY environment variable not set. Please set it in a .env file.")
        logging.info("Example: GOOGLE_API_KEY='YourActualGoogleAPIKey'")
        return

    logging.info(f"Autonomous Swarm Initialized with {num_agents} agents for {max_iterations} iterations.")

    # Initialize agents
    agent_ids = [f"agent_{i+1}" for i in range(num_agents)]
    agent_configs = {
        agent_id: {"configurable": {"thread_id": agent_id}} for agent_id in agent_ids
    }

    # Initial tasks (can be dynamically generated later)
    initial_tasks = [
        "Research the benefits of renewable energy.",
        "Find recent advancements in AI ethics.",
        "Summarize the history of space exploration.",
    ]
    for i, task_desc in enumerate(initial_tasks):
        add_task_to_swarm.invoke({"description": task_desc, "source_agent_id": "system_initializer"}) # System adds initial tasks

    # Main swarm loop
    for iteration in range(max_iterations):
        logging.info(f"\n--- Swarm Iteration {iteration + 1}/{max_iterations} ---")

        # Evaporate pheromones periodically
        swarm_environment.evaporate()

        # Each agent takes a turn
        for agent_id in agent_ids:
            logging.info(f"\n--- Agent {agent_id} turn ---")

            # Agent checks for available tasks
            available_tasks_str = get_available_tasks_from_swarm.invoke({"limit": 1})
            logging.info(f"Agent {agent_id} sees: {available_tasks_str}")

            # Simple task selection: if tasks available, pick one. Otherwise, generate a new one.
            if "No pending tasks" not in available_tasks_str:
                # Parse the task ID and description (simplistic parsing for now)
                try:
                    task_info_parts = available_tasks_str.split("Task ID: ")[1].split(", Description: ")
                    task_id = int(task_info_parts[0])
                    task_description = task_info_parts[1].split(" (from ")[0]
                    logging.info(f"Agent {agent_id} picked task {task_id}: {task_description}")
                except Exception as e:
                    logging.error(f"Error parsing task info: {e}. Skipping task selection.")
                    task_id = None
                    task_description = None
            else:
                task_id = None
                task_description = None

            current_task_input = ""
            if task_description:
                current_task_input = task_description
            else:
                # If no tasks, agent generates a new one (simplistic for now)
                # In a real system, LLM would generate a task based on swarm state/goals
                current_task_input = f"Generate a new research question related to current global challenges."
                logging.info(f"Agent {agent_id} generating new task: {current_task_input}")

            # Run the agent's graph
            initial_state_input = {"messages": [HumanMessage(content=current_task_input)], "input": current_task_input}
            final_state = agent_graph.invoke(
                initial_state_input,
                agent_configs[agent_id],
            )

            if final_state and "messages" in final_state and final_state["messages"]:
                logging.info(f"--- Agent {agent_id} Output ---")
                final_state["messages"][-1].pretty_print()

            # Mark task as completed if it was picked
            if task_id:
                mark_task_completed_in_swarm.invoke({"task_id": task_id, "assigned_agent_id": agent_id})

            # Reinforce concepts based on agent's input
            swarm_environment.reinforce_concept(current_task_input, weight=1.0)

            # Observe swarm state
            logging.info(f"--- Current Swarm State after Agent {agent_id} ---")
            logging.info(swarm_environment.get_strongest_concepts())
            logging.info(f"Discovered facts: {swarm_environment.get_facts()}")
            logging.info(f"Pending tasks: {swarm_environment.get_available_tasks()}")

    logging.info("\n--- Autonomous Swarm Simulation Completed ---")
    memory_system.close() # Close DB connections

if __name__ == "__main__":
    run_autonomous_swarm(num_agents=3, max_iterations=5)
