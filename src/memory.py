import os
import sqlite3
import redis
from dotenv import load_dotenv

class LongTermMemorySystem:
    """
    Manages the connection to the long-term memory backends (Redis and SQLite).
    Acts as a singleton to provide a consistent connection across the application.
    """
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(LongTermMemorySystem, cls).__new__(cls)
            cls._instance._initialize_connections()
        return cls._instance

    def _initialize_connections(self):
        """Initializes connections to Redis and SQLite using environment variables."""
        load_dotenv()
        self.redis_client = None
        self.sqlite_conn = None

        # Connect to Redis
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            self.redis_client = redis.Redis(host=redis_host, port=redis_port, db=0, decode_responses=True)
            self.redis_client.ping()
            print("INFO: Successfully connected to Redis.")
        except redis.exceptions.ConnectionError as e:
            print(f"Warning: Could not connect to Redis. Check your settings. Error: {e}")

        # Connect to SQLite
        try:
            db_path = os.getenv("SQLITE_DB_PATH", "memory.db")
            self.sqlite_conn = sqlite3.connect(db_path, check_same_thread=False) # check_same_thread=False for multi-threading
            self.sqlite_conn.row_factory = sqlite3.Row # Access columns by name
            self._initialize_sqlite_tables()
            print(f"INFO: Successfully connected to SQLite database at {db_path}.")
        except Exception as e:
            print(f"Error: Could not connect to SQLite. Error: {e}")

    def _initialize_sqlite_tables(self):
        """Creates necessary tables in the SQLite database if they don't exist."""
        cursor = self.sqlite_conn.cursor()
        # Table for long-term memories (replacing Neo4j's Memory nodes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS memories (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                content TEXT NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        # Table for swarm concepts/pheromones (replacing Neo4j's Concept nodes)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS concepts (
                name TEXT PRIMARY KEY,
                pheromone REAL NOT NULL DEFAULT 0.0,
                last_reinforced DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)
        self.sqlite_conn.commit()

    def close(self):
        """Closes the database connections gracefully."""
        if self.sqlite_conn:
            self.sqlite_conn.close()
            print("INFO: SQLite connection closed.")

# Instantiate the memory system so it can be imported and used elsewhere
memory_system = LongTermMemorySystem()