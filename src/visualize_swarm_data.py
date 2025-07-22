import sqlite3
import matplotlib.pyplot as plt
import pandas as pd
import logging
import os

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def visualize_concept_strengths(db_path: str = "memory.db", output_filename: str = "concept_strength_over_time.png"):
    """
    Visualizes the concept strengths (pheromone levels) over time from the SQLite database.

    Args:
        db_path (str): The path to the SQLite database file.
        output_filename (str): The name of the output PNG file for the plot.
    """
    try:
        conn = sqlite3.connect(db_path)
        logging.info(f"Successfully connected to SQLite database at {db_path}.")

        # Read concepts data into a pandas DataFrame
        # Note: This assumes 'last_reinforced' can serve as a proxy for time steps.
        # For more accurate time series, a dedicated 'history' table would be better.
        df = pd.read_sql_query("SELECT name, pheromone, last_reinforced FROM concepts ORDER BY last_reinforced ASC", conn)
        
        if df.empty:
            logging.warning("No concept data found in the database to visualize.")
            return

        # Prepare data for plotting
        concept_strengths_over_time = {}
        time_steps = sorted(df['last_reinforced'].unique())
        time_step_map = {ts: i for i, ts in enumerate(time_steps)}

        for _, row in df.iterrows():
            concept_name = row['name']
            strength = row['pheromone']
            timestamp = row['last_reinforced']
            
            if concept_name not in concept_strengths_over_time:
                concept_strengths_over_time[concept_name] = [0] * len(time_steps)
            
            # Update the strength at the corresponding time step
            concept_strengths_over_time[concept_name][time_step_map[timestamp]] = strength

        # Plotting the concept strengths over time
        plt.figure(figsize=(12, 7))
        for concept_name, strengths in concept_strengths_over_time.items():
            plt.plot(range(len(time_steps)), strengths, label=concept_name)

        plt.xlabel("Time Step (Reinforcement Event Index)")
        plt.ylabel("Concept Strength (Pheromone Level)")
        plt.title("Concept Strength Over Time in Swarm Environment")
        plt.legend()
        plt.grid(True)
        plt.tight_layout()
        
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_filename)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)

        plt.savefig(output_filename) # Save the plot
        logging.info(f"Concept strength plot saved to {output_filename}")

    except sqlite3.Error as e:
        logging.error(f"SQLite error: {e}")
    except Exception as e:
        logging.error(f"An unexpected error occurred: {e}")
    finally:
        if 'conn' in locals() and conn:
            conn.close()
            logging.info("SQLite connection closed.")

if __name__ == "__main__":
    # Ensure the script is run from the project root or provide absolute path
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    db_path = os.path.join(project_root, "memory.db")
    output_path = os.path.join(project_root, "concept_strength_over_time.png")
    visualize_concept_strengths(db_path=db_path, output_filename=output_path)
