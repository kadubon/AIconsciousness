import logging
from langchain_core.tools import tool
from src.memory import memory_system
from src.swarm import swarm_environment

@tool
def web_search(query: str) -> str:
    """Simulates a web search for the given query and returns the results."""
    logging.info(f"Simulating web search for query: '{query}'")
    return f"Here are the simulated search results for '{query}'."

@tool
def add_long_term_memory(content: str) -> str:
    """Adds important information to the agent's long-term memory (SQLite)."""
    if not memory_system.sqlite_conn:
        logging.error("SQLite connection not available for add_long_term_memory.")
        return "Error: SQLite connection not available."
    
    cursor = memory_system.sqlite_conn.cursor()
    try:
        cursor.execute("INSERT INTO memories (content) VALUES (?) ", (content,))
        memory_system.sqlite_conn.commit()
        
        logging.info(f"Added the following content to SQLite: '{content}'")
        return "Successfully added content to long-term memory."
    except Exception as e:
        logging.error(f"Error adding content to long-term memory: {e}")
        return f"Error adding content to long-term memory: {e}"

@tool
def search_long_term_memory(query: str) -> str:
    """Searches the agent's long-term memory (SQLite) for relevant information."""
    if not memory_system.sqlite_conn:
        logging.error("SQLite connection not available for search_long_term_memory.")
        return "Error: SQLite connection not available."

    cursor = memory_system.sqlite_conn.cursor()
    try:
        # A simple keyword search implementation.
        cursor.execute(
            "SELECT content FROM memories WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 5",
            (f'%{query}%',)
        )
        memories = [row["content"] for row in cursor.fetchall()]
        
        if not memories:
            return f"No specific memories found in SQLite for '{query}'."
        
        logging.info(f"Retrieved memories from SQLite for query '{query}': {memories}")
        return "\n".join(memories)
    except Exception as e:
        logging.error(f"Error searching long-term memory for query '{query}': {e}")
        return f"Error searching long-term memory: {e}"

@tool
def add_fact_to_swarm(fact: str, source_agent_id: str) -> str:
    """Adds a discovered fact to the shared swarm environment."""
    return swarm_environment.add_fact(fact, source_agent_id)

@tool
def get_facts_from_swarm(query: str = None, limit: int = 5) -> str:
    """Retrieves facts from the shared swarm environment, optionally filtered by a query."""
    facts = swarm_environment.get_facts(query, limit)
    if not facts:
        return "No facts found in the shared environment."
    return "Discovered facts: " + ", ".join([f"{f['content']} (by {f['source_agent_id']})" for f in facts])

@tool
def reinforce_concept(concept: str, weight: float = 1.0) -> str:
    """Reinforces a concept in the shared swarm environment, increasing its 'pheromone' level."""
    return swarm_environment.reinforce_concept(concept, weight)

@tool
def get_strongest_concepts(limit: int = 5) -> str:
    """Retrieves the concepts with the highest 'pheromone' levels from the shared swarm environment."""
    concepts = swarm_environment.get_strongest_concepts(limit)
    if not concepts:
        return "No concepts found in the shared environment."
    return "Strongest concepts: " + ", ".join([f"{c['concept']} (strength: {c['strength']:.2f})" for c in concepts])