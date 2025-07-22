# Project Superorganism: Self-Improving Superintelligence and Autonomous Swarm Intelligence System

## Overview

Project Superorganism is an ambitious endeavor to develop a self-improving superintelligence and autonomous swarm intelligence system. Inspired by biological superorganisms, this project aims to create a collective intelligence from the interaction of multiple individual cognitive agents. Each agent operates on a Reason-Act-Observe loop, leveraging tools to interact with its environment and a shared memory system for long-term learning and stigmergic communication.

## Architecture

The system's architecture is modular, comprising several key components:

*   **Cognitive Agents:** Individual agents built using `langgraph`, each possessing its own state, reasoning capabilities (powered by LLMs), and a set of tools.
*   **Tools:** Functions that allow agents to interact with the external world (e.g., `web_search`) and internal systems (e.g., `add_long_term_memory`, `add_fact_to_swarm`).
*   **Long-Term Memory:** A SQLite database (`memory.db`) used by individual agents to store significant learnings and recall past experiences. It also stores facts discovered by agents.
*   **Swarm Environment:** A shared SQLite database (`memory.db` - specifically the `concepts` and `facts` tables) that facilitates stigmergic communication. Agents reinforce concepts (pheromones) and share discovered facts, influencing the collective behavior.
*   **StateGraph:** The core of each agent's control flow, defining the transitions between reasoning, tool execution, and reflection.
*   **Checkpointer:** `SqliteSaver` is used to persist the state of individual agent graphs, enabling multi-turn conversations and state restoration.

## Features

*   **Reason-Act-Observe Loop:** Agents continuously reason, act using tools, and observe the outcomes.
*   **Tool Use:** Extensible toolset for diverse interactions.
*   **Long-Term Memory:** Agents can store and retrieve information from a persistent memory.
*   **Reflection:** Agents reflect on their performance to extract learnings and improve.
*   **Stigmergic Communication:** Agents communicate indirectly through modifications to a shared environment (concept reinforcement and fact sharing).
*   **Self-Healing (Conceptual):** The system can conceptually recover from individual agent failures by allowing other agents to pick up tasks or re-evaluate the swarm state.
*   **Continual Learning (Conceptual):** The system is designed to learn new skills and knowledge over time without forgetting previous learnings.
*   **Emergent Behavior (Conceptual):** The architecture supports the emergence of complex collective behaviors from simple local interactions.
*   **Logging & Visualization:** Basic logging is implemented, and a visualization script generates plots of concept strength over time.

## Setup and Installation

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/your-username/AIconsciousness.git
    cd AIconsciousness
    ```

2.  **Create and activate a Python virtual environment:**
    ```bash
    python -m venv .venv
    # On Windows:
    .venv\Scripts\activate
    # On macOS/Linux:
    source .venv/bin/activate
    ```

3.  **Install `uv` (if not already installed):**
    `uv` is a fast Python package installer and resolver. It's recommended for this project.
    ```bash
    pip install uv
    ```

4.  **Install dependencies using `uv`:**
    ```bash
    .venv\Scripts\uv pip install -r requirements.txt
    ```

5.  **Set up your Google API Key:**
    Create a `.env` file in the project root directory and add your Google API Key:
    ```
    GOOGLE_API_KEY='YourAPIKeyHere'
    ```
    Replace `'YourAPIKeyHere'` with your actual Google API Key. You can obtain one from the Google AI Studio.

## How to Run

### Running a Single Agent (Interactive)

To interact with a single cognitive agent:

```bash
.venv\Scripts\python src\main.py
```

Type your queries at the `You:` prompt. Type `exit` to quit.

### Running Multi-Agent Swarm Tests

To run the multi-agent collaborative task and observe swarm dynamics:

```bash
.venv\Scripts\python src\multi_agent_test.py
```

This script will:
1.  Run several agents to find fun facts about different topics.
2.  Have a summarization agent collect and summarize these facts.
3.  Generate a `concept_strength_over_time.png` file in the project root, visualizing the evolution of concept strengths in the shared environment.

### Running Self-Healing Tests (Conceptual)

To simulate a self-healing scenario where some agents are disabled, uncomment the relevant lines in `src/multi_agent_test.py`:

```python
# if __name__ == "__main__":
#     # Run a normal test
#     run_multi_agent_test()

#     # Run a self-healing test (e.g., disable agent_dog_fact)
#     # print("\n\n--- Running Self-Healing Test (agent_dog_fact disabled) ---")
#     # run_multi_agent_test(disabled_agents=["agent_dog_fact"])
```

Then run the script as usual:

```bash
.venv\Scripts\python src\multi_agent_test.py
```

Observe how the system attempts to complete the task despite disabled agents.

## Project Status and Future Work

This project is a work in progress. While core functionalities are implemented, further development is planned for:

*   **Robustness:** More sophisticated error handling and recovery mechanisms.
*   **Scalability:** Optimizing performance for a larger number of agents and more complex interactions.
*   **Emergence:** Deeper exploration and analysis of emergent behaviors.
*   **Advanced Tools:** Integration of more powerful and diverse tools for agents.
*   **User Interface:** A more intuitive interface for interacting with the swarm.

---
