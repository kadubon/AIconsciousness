import logging
from src.memory import memory_system

class SwarmEnvironment:
    """
    Manages the shared environment for stigmergic communication between agents.
    This uses the SQLite backend for storing and decaying "pheromones" on concepts.
    """
    def __init__(self):
        self.conn = memory_system.sqlite_conn
        if not self.conn:
            logging.warning("SQLite connection not available for SwarmEnvironment.")

    def reinforce_concept(self, concept: str, weight: float = 1.0) -> str:
        """
        Increases the 'pheromone' strength of a concept in the shared environment.
        If the concept doesn't exist, it's created or its strength is updated.
        
        Args:
            concept (str): The name of the concept to reinforce.
            weight (float): The amount by which to increase the pheromone level. Defaults to 1.0.
        
        Returns:
            str: A message indicating the result of the operation.
        """
        if not self.conn:
            logging.error("SQLite connection not available for reinforce_concept.")
            return "Error: SQLite not connected."
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO concepts (name, pheromone, last_reinforced)
                VALUES (?, ?, CURRENT_TIMESTAMP)
                ON CONFLICT(name) DO UPDATE SET
                    pheromone = pheromone + ?, 
                    last_reinforced = CURRENT_TIMESTAMP
            """, (concept, weight, weight))
            self.conn.commit()
            logging.info(f"Reinforced concept '{concept}' with weight {weight}.")
            return f"Concept '{concept}' reinforced."
        except sqlite3.Error as e:
            logging.error(f"Error reinforcing concept '{concept}': {e}")
            return f"Error reinforcing concept: {e}"

    def get_strongest_concepts(self, limit: int = 5) -> list[dict]:
        """
        Retrieves the concepts with the highest pheromone levels from the shared environment.
        
        Args:
            limit (int): The maximum number of strongest concepts to retrieve. Defaults to 5.
            
        Returns:
            list[dict]: A list of dictionaries, each containing 'concept' (name) and 'strength' (pheromone level).
        """
        if not self.conn:
            logging.error("SQLite connection not available for get_strongest_concepts.")
            return []
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                SELECT name, pheromone FROM concepts
                WHERE pheromone > 0
                ORDER BY pheromone DESC
                LIMIT ?
            """, (limit,))
            return [{"concept": row["name"], "strength": row["pheromone"]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error retrieving strongest concepts: {e}")
            return []

    def evaporate(self, decay_rate: float = 0.1) -> str:
        """
        Reduces the pheromone level of all concepts by a decay rate.
        Removes concepts with pheromone levels below a threshold to keep the environment clean.
        
        Args:
            decay_rate (float): The rate at which pheromone levels decay (e.g., 0.1 for 10% decay). Defaults to 0.1.
            
        Returns:
            str: A message indicating the result of the operation.
        """
        if not self.conn:
            logging.error("SQLite connection not available for evaporate.")
            return "Error: SQLite not connected."

        cursor = self.conn.cursor()
        try:
            # Decay all pheromones
            cursor.execute("""
                UPDATE concepts
                SET pheromone = pheromone * ?
            """, (1 - decay_rate,))

            # Remove concepts with negligible pheromone
            cursor.execute("""
                DELETE FROM concepts
                WHERE pheromone < 0.01
            """,)
            self.conn.commit()
            logging.info(f"Evaporated all pheromones with decay rate {decay_rate}.")
            return "Pheromones evaporated successfully."
        except sqlite3.Error as e:
            logging.error(f"Error evaporating pheromones: {e}")
            return f"Error evaporating pheromones: {e}"

    def add_fact(self, fact: str, source_agent_id: str) -> str:
        """
        Adds a discovered fact to the shared environment's facts table.
        
        Args:
            fact (str): The content of the discovered fact.
            source_agent_id (str): The ID of the agent that discovered the fact.
            
        Returns:
            str: A message indicating the result of the operation.
        """
        if not self.conn:
            logging.error("SQLite connection not available for add_fact.")
            return "Error: SQLite not connected."
        
        cursor = self.conn.cursor()
        try:
            cursor.execute("""
                INSERT INTO facts (content, source_agent_id, timestamp)
                VALUES (?, ?, CURRENT_TIMESTAMP)
            """, (fact, source_agent_id))
            self.conn.commit()
            logging.info(f"Agent {source_agent_id} added fact: '{fact}'.")
            return f"Fact added by {source_agent_id}."
        except sqlite3.Error as e:
            logging.error(f"Error adding fact '{fact}': {e}")
            return f"Error adding fact: {e}"

    def get_facts(self, query: str = None, limit: int = 5) -> list[dict]:
        """
        Retrieves facts from the shared environment's facts table, optionally filtered by a query.
        
        Args:
            query (str, optional): A keyword or phrase to search for within the facts. Defaults to None.
            limit (int): The maximum number of facts to retrieve. Defaults to 5.
            
        Returns:
            list[dict]: A list of dictionaries, each containing 'content' (fact text) and 'source_agent_id'.
        """
        if not self.conn:
            logging.error("SQLite connection not available for get_facts.")
            return []
        
        cursor = self.conn.cursor()
        try:
            if query:
                # Simple LIKE search for demonstration. For production, consider full-text search (FTS).
                cursor.execute("""
                    SELECT content, source_agent_id FROM facts
                    WHERE content LIKE ?
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (f"%{query}%", limit))
            else:
                cursor.execute("""
                    SELECT content, source_agent_id FROM facts
                    ORDER BY timestamp DESC
                    LIMIT ?
                """, (limit,))
            return [{"content": row["content"], "source_agent_id": row["source_agent_id"]} for row in cursor.fetchall()]
        except sqlite3.Error as e:
            logging.error(f"Error retrieving facts with query '{query}': {e}")
            return []

# Singleton instance for the swarm environment
swarm_environment = SwarmEnvironment()