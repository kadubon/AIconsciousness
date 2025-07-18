from langchain_core.tools import tool
from src.memory import memory_system
from src.swarm import swarm_environment

@tool
def web_search(query: str) -> str:
    """Simulates a web search for the given query and returns the results."""
    print(f"INFO: Simulating web search for query: '{query}'")
    return f"Here are the simulated search results for '{query}'."

@tool
def add_long_term_memory(content: str) -> str:
    """Adds important information to the agent's long-term memory (SQLite)."""
    if not memory_system.sqlite_conn:
        return "Error: SQLite connection not available."
    
    cursor = memory_system.sqlite_conn.cursor()
    cursor.execute("INSERT INTO memories (content) VALUES (?) ", (content,))
    memory_system.sqlite_conn.commit()
    
    print(f"INFO: Added the following content to SQLite: '{content}'")
    return "Successfully added content to long-term memory."

@tool
def search_long_term_memory(query: str) -> str:
    """Searches the agent's long-term memory (SQLite) for relevant information."""
    if not memory_system.sqlite_conn:
        return "Error: SQLite connection not available."

    cursor = memory_system.sqlite_conn.cursor()
    # A simple keyword search implementation.
    cursor.execute(
        "SELECT content FROM memories WHERE content LIKE ? ORDER BY timestamp DESC LIMIT 5",
        (f'%{query}%',)
    )
    memories = [row["content"] for row in cursor.fetchall()]
    
    if not memories:
        return f"No specific memories found in SQLite for '{query}'."
    
    print(f"INFO: Retrieved memories from SQLite for query '{query}': {memories}")
    return "\n".join(memories)

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