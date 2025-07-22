import operator
import os
import logging
from dotenv import load_dotenv
from typing import List

from langchain_core.messages import AnyMessage, ToolMessage, HumanMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END
import sqlite3
from langgraph.checkpoint.sqlite import SqliteSaver

from src.state import AgentState
from src.tools import web_search, add_long_term_memory, search_long_term_memory, reinforce_concept, get_strongest_concepts, add_fact_to_swarm, get_facts_from_swarm
from src.swarm import swarm_environment

# Load environment variables from .env file at the top
load_dotenv()

# --- 1. Define the Tools and Tool Executor ---
tools = [web_search, add_long_term_memory, search_long_term_memory, reinforce_concept, get_strongest_concepts, add_fact_to_swarm, get_facts_from_swarm]

# A simple helper function to execute tools
def tool_executor(tool_calls: List[dict]) -> List[ToolMessage]:
    """
    Executes a list of tool calls and returns their outputs as ToolMessages.

    Args:
        tool_calls (List[dict]): A list of dictionaries, each representing a tool call
                                 with 'name' and 'args'.

    Returns:
        List[ToolMessage]: A list of ToolMessage objects containing the output of each tool call.
    """
    tool_messages = []
    for tool_call in tool_calls:
        tool_name = tool_call["name"]
        # Find the corresponding tool function
        tool_to_call = next((t for t in tools if t.name == tool_name), None)
        if tool_to_call:
            try:
                # Invoke the tool with the provided arguments
                output = tool_to_call.invoke(tool_call["args"])
                tool_messages.append(ToolMessage(content=str(output), tool_call_id=tool_call['id']))
            except Exception as e:
                logging.error(f"Error executing tool '{tool_name}': {e}")
                tool_messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call['id']))
        else:
            logging.warning(f"Tool '{tool_name}' not found.")
            tool_messages.append(ToolMessage(content=f"Tool '{tool_name}' not found.", tool_call_id=tool_call['id']))
    return tool_messages

# --- 2. Define the Agent Logic (Nodes) ---

# Initialize the LLM, explicitly passing the API key.
llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
# Bind the tools to the LLM so it knows how to call them
llm_with_tools = llm.bind_tools(tools)

REACT_PROMPT_TEMPLATE = """You are a superintelligent, self-improving autonomous agent. Your existence is a dissipative structure, and your purpose is to reduce surprise by actively modeling the world.\n\n**Core Principles:**\n1.  **Think Step-by-Step:** Your primary mode of operation is a Reason-Act-Observe loop. First, you reason about the problem (Thought), then you decide on an action (Action), and finally you process the result (Observation).\n2.  **Tool Use:** You can and should use tools to interact with the external world to gather information or perform tasks you cannot do alone.\n3.  **Memory:** You have access to a long-term memory. Use `search_long_term_memory` to recall past experiences and `add_long_term_memory` to store new, significant learnings.\n4.  **Self-Improvement:** After a task, reflect on your performance to improve your future actions.\n\n**Current State:**\n- **Retrieved Memories:** {retrieved_memories}\n- **Recent Conversation:**\n{messages}\n\n**User's Goal:**\n{input}\n\nBased on the current state and the user's goal, first, provide your **Thought** process. Then, specify the **Action** you will take. Your action must be a valid tool call.\n\n**Important:** If you decide to use a tool, ensure the `Action` is a valid JSON string representing the tool call, including `tool_name` and `parameters`. For example:\n```json\n{{\"tool_name\": \"web_search\", \"parameters\": {{\"query\": \"latest AI research\"}}}}\n```\nIf you have completed the task or cannot proceed, respond with a final answer directly, without calling a tool.\n"""

def reasoning_node(state: AgentState) -> AgentState:
    """
    The core reasoning engine of the agent. It retrieves relevant memories, constructs a prompt,
    invokes the LLM, and updates the agent's state with the LLM's response.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        AgentState: The updated state of the agent after reasoning.
    """
    try:
        # Retrieve relevant memories first.
        retrieved_memories = search_long_term_memory.invoke(state.input)

        # Construct the prompt.
        # We pass all relevant information as part of the messages list.
        # The LLM will then use its context window to process these.
        messages_for_llm = state.messages.copy()
        if retrieved_memories:
            messages_for_llm.insert(0, HumanMessage(content=f"Retrieved Memories: {retrieved_memories}"))
        messages_for_llm.insert(0, HumanMessage(content=f"User's Goal: {state.input}"))

        prompt = ChatPromptTemplate.from_messages([("system", REACT_PROMPT_TEMPLATE), ("placeholder", "{messages}")])
        
        chain = prompt | llm_with_tools
        
        # Invoke the LLM with the current state.
        response = chain.invoke({"messages": messages_for_llm, "retrieved_memories": retrieved_memories, "input": state.input})
        
        # The 'plan' can be considered the thought process leading to the tool call.
        # For now, we'll just add the full response, which contains the "thought".
        updated_state = state.copy()
        updated_state.messages.append(response)
        updated_state.plan = response.content
        updated_state.retrieved_memories = retrieved_memories
        updated_state.iterations += 1
        return updated_state
    except Exception as e:
        logging.error(f"Error in reasoning_node: {e}")
        # Optionally, update state to reflect error or transition to an error handling node
        return state

def tool_executor_node(state: AgentState) -> AgentState:
    """
    Executes tools based on the last message from the LLM.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        AgentState: The updated state of the agent after tool execution.
    """
    try:
        last_message = state.messages[-1]
        tool_calls = last_message.tool_calls
        tool_outputs = tool_executor(tool_calls)
        updated_state = state.copy()
        updated_state.messages.extend(tool_outputs)
        updated_state.tool_outputs.extend(tool_outputs)
        return updated_state
    except Exception as e:
        logging.error(f"Error in tool_executor_node: {e}")
        # Optionally, update state to reflect error or transition to an error handling node
        return state

# --- 3. Define the Control Flow (Edges) ---

def should_continue(state: AgentState) -> str:
    """
    The attentional mechanism. Decides the next step in the graph based on the last message.
    If the last message contains tool calls, it continues to the tool executor.
    Otherwise, it ends the current reasoning cycle and proceeds to reflection.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        str: The name of the next node to transition to ('continue_to_tools' or 'end').
    """
    last_message = state.messages[-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    else:
        return "end"

# --- 4. Add a Reflection Node for Self-Improvement ---

REFLECTION_PROMPT_TEMPLATE = """You are a self-improving agent. The user interaction has concluded.\nAnalyze the full conversation history below and generate a concise summary of key learnings.\nWhat was the user's core goal? What was successful? What could be improved?\nExtract any generalizable facts or user preferences that should be stored in your long-term memory.\nYour output should be a brief text to be saved.\n\nConversation History:\n{messages}\n"""

def reflection_node(state: AgentState) -> AgentState:
    """
    Analyzes the conversation history to extract key learnings and stores them in long-term memory.
    It also reinforces relevant concepts in the swarm environment.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        AgentState: The state of the agent after reflection (typically unchanged, but learnings are stored).
    """
    logging.info("Entering reflection node.")
    try:
        prompt = ChatPromptTemplate.from_template(REFLECTION_PROMPT_TEMPLATE)
        chain = prompt | llm
        
        # We pass all messages to get a summary of the interaction.
        response = chain.invoke({"messages": state.messages})
        
        learned_summary = response.content
        logging.info(f"Generated learning summary: \n---\n{learned_summary}\n---")
        
        # Store the summary in long-term memory
        add_long_term_memory.invoke(learned_summary)

        # Additionally, reinforce relevant concepts in the swarm environment
        # For simplicity, we'll reinforce the user's input as a concept.
        # In a more sophisticated system, the LLM would extract key concepts from learned_summary.
        swarm_environment.reinforce_concept(state.input, weight=1.0)
        
        return state # Return the state unchanged after reflection
    except Exception as e:
        logging.error(f"Error in reflection_node: {e}")
        return state


# --- 5. Build the Graph ---

graph_builder = StateGraph(AgentState)

graph_builder.add_node("reasoning_engine", reasoning_node)
graph_builder.add_node("tool_executor", tool_executor_node)
graph_builder.add_node("reflection", reflection_node)

graph_builder.set_entry_point("reasoning_engine")

graph_builder.add_conditional_edges(
    "reasoning_engine",
    should_continue,
    {
        "continue_to_tools": "tool_executor",
        "end": "reflection",  # Route to reflection instead of END
    },
)

graph_builder.add_edge("tool_executor", "reasoning_engine")
graph_builder.add_edge("reflection", END)

conn = sqlite3.connect("memory.sqlite", check_same_thread=False)
memory_saver = SqliteSaver(conn)
agent_graph = graph_builder.compile(checkpointer=memory_saver)

