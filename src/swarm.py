from src.memory import memory_system

class SwarmEnvironment:
    """
    Manages the shared environment for stigmergic communication between agents.
    This uses the SQLite backend for storing and decaying "pheromones" on concepts.
    """
    def __init__(self):
        self.conn = memory_system.sqlite_conn
        if not self.conn:
            print("Warning: SQLite connection not available for SwarmEnvironment.")

    def reinforce_concept(self, concept: str, weight: float = 1.0):
        """
        Increases the 'pheromone' strength of a concept in the shared environment.
        If the concept doesn't exist, it's created.
        """
        if not self.conn:
            return "Error: SQLite not connected."
        
        cursor = self.conn.cursor()
        cursor.execute("""
            INSERT INTO concepts (name, pheromone, last_reinforced)
            VALUES (?, ?, CURRENT_TIMESTAMP)
            ON CONFLICT(name) DO UPDATE SET
                pheromone = pheromone + ?, 
                last_reinforced = CURRENT_TIMESTAMP
        """, (concept, weight, weight))
        self.conn.commit()
        print(f"INFO: Reinforced concept '{concept}' with weight {weight}.")
        return f"Concept '{concept}' reinforced."

    def get_strongest_concepts(self, limit: int = 5) -> list[dict]:
        """
        Retrieves the concepts with the highest pheromone levels.
        """
        if not self.conn:
            return []
        
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT name, pheromone FROM concepts
            WHERE pheromone > 0
            ORDER BY pheromone DESC
            LIMIT ?
        """, (limit,))
        return [{"concept": row["name"], "strength": row["pheromone"]} for row in cursor.fetchall()]

    def evaporate(self, decay_rate: float = 0.1):
        """
        Reduces the pheromone level of all concepts by a decay rate.
        Removes concepts with pheromone levels below a threshold.
        """
        if not self.conn:
            return "Error: SQLite not connected."

        cursor = self.conn.cursor()
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
        print(f"INFO: Evaporated all pheromones with decay rate {decay_rate}.")

# Singleton instance for the swarm environment
swarm_environment = SwarmEnvironment()