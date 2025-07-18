import operator
from typing import TypedDict, Annotated

from langchain_core.messages import AnyMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_google_genai import ChatGoogleGenerativeAI
from langgraph.graph import StateGraph, END

from src.state import AgentState
from src.tools import web_search, add_long_term_memory, search_long_term_memory, reinforce_concept, get_strongest_concepts

# --- 1. Define the Tools and Tool Executor ---
tools = [web_search, add_long_term_memory, search_long_term_memory, reinforce_concept, get_strongest_concepts]

# A simple helper function to execute tools
def tool_executor(tool_calls):
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
                tool_messages.append(ToolMessage(content=f"Error: {e}", tool_call_id=tool_call['id']))
        else:
            tool_messages.append(ToolMessage(content=f"Tool '{tool_name}' not found.", tool_call_id=tool_call['id']))
    return tool_messages

import os
from dotenv import load_dotenv

# Load environment variables from .env file at the top
load_dotenv()

# --- 2. Define the Agent Logic (Nodes) ---

# Initialize the LLM, explicitly passing the API key.
llm = ChatGoogleGenerativeAI(model="gemini-1.5-flash", google_api_key=os.getenv("GOOGLE_API_KEY"))
# Bind the tools to the LLM so it knows how to call them
llm_with_tools = llm.bind_tools(tools)

REACT_PROMPT_TEMPLATE = """You are a superintelligent, self-improving autonomous agent. Your existence is a dissipative structure, and your purpose is to reduce surprise by actively modeling the world.

**Core Principles:**
1.  **Think Step-by-Step:** Your primary mode of operation is a Reason-Act-Observe loop. First, you reason about the problem (Thought), then you decide on an action (Action), and finally you process the result (Observation).
2.  **Tool Use:** You can and should use tools to interact with the external world to gather information or perform tasks you cannot do alone.
3.  **Memory:** You have access to a long-term memory. Use `search_long_term_memory` to recall past experiences and `add_long_term_memory` to store new, significant learnings.
4.  **Self-Improvement:** After a task, reflect on your performance to improve your future actions.

**Current State:**
- **Retrieved Memories:** {retrieved_memories}
- **Recent Conversation:**
{messages}

**User's Goal:**
{input}

Based on the current state and the user's goal, first, provide your **Thought** process. Then, specify the **Action** you will take. Your action must be a valid tool call.
"""

def reasoning_node(state: AgentState):
    """The core reasoning engine of the agent."""
    # Retrieve relevant memories first.
    retrieved_memories = search_long_term_memory.invoke(state['input'])

    # Construct the prompt.
    # We pass all relevant information as part of the messages list.
    # The LLM will then use its context window to process these.
    messages_for_llm = state["messages"].copy()
    if state["retrieved_memories"]:
        messages_for_llm.insert(0, HumanMessage(content=f"Retrieved Memories: {state["retrieved_memories"]}"))
    messages_for_llm.insert(0, HumanMessage(content=f"User's Goal: {state["input"]}"))

    prompt = ChatPromptTemplate.from_messages([("system", REACT_PROMPT_TEMPLATE), ("placeholder", "{messages}")])
    
    chain = prompt | llm_with_tools
    
    # Invoke the LLM with the current state.
    response = chain.invoke({"messages": messages_for_llm})
    
    # The 'plan' can be considered the thought process leading to the tool call.
    # For now, we'll just add the full response, which contains the "thought".
    return {"messages": [response], "plan": response.content}

def tool_executor_node(state: AgentState):
    """Executes tools based on the last message."""
    last_message = state["messages"][-1]
    tool_calls = last_message.tool_calls
    tool_outputs = tool_executor(tool_calls)
    return {"messages": tool_outputs}

# --- 3. Define the Control Flow (Edges) ---

def should_continue(state: AgentState) -> str:
    """The attentional mechanism. Decides the next step."""
    last_message = state["messages"][-1]
    if last_message.tool_calls:
        return "continue_to_tools"
    else:
        return "end"

# --- 4. Add a Reflection Node for Self-Improvement ---

REFLECTION_PROMPT_TEMPLATE = """You are a self-improving agent. The user interaction has concluded.
Analyze the full conversation history below and generate a concise summary of key learnings.
What was the user's core goal? What was successful? What could be improved?
Extract any generalizable facts or user preferences that should be stored in your long-term memory.
Your output should be a brief text to be saved.

Conversation History:
{messages}
"""

def reflection_node(state: AgentState):
    """Analyzes the conversation and stores key learnings in long-term memory."""
    print("INFO: Entering reflection node.")
    prompt = ChatPromptTemplate.from_template(REFLECTION_PROMPT_TEMPLATE)
    chain = prompt | llm
    
    # We pass all messages to get a summary of the interaction.
    response = chain.invoke({"messages": state["messages"]})
    
    learned_summary = response.content
    print(f"INFO: Generated learning summary: \n---\n{learned_summary}\n---")
    
    # Store the summary in long-term memory
    add_long_term_memory.invoke(learned_summary)

    # Additionally, reinforce relevant concepts in the swarm environment
    # For simplicity, we'll reinforce the user's input as a concept.
    # In a more sophisticated system, the LLM would extract key concepts from learned_summary.
    swarm_environment.reinforce_concept(state['input'], weight=1.0)
    
    return {}


from langgraph.checkpoint.sqlite import SqliteSaver

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
graph_builder.add_edge("reflection", END)  # Go to END after reflection

# Compile the graph with persistence
memory = SqliteSaver.from_conn_string("memory.sqlite")
agent_graph = graph_builder.compile(checkpointer=memory)
