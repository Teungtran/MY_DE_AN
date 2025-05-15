from typing import Any, Dict

from langchain_core.messages import SystemMessage
from langchain_core.runnables import RunnableConfig
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition

from factories.chat_factory import create_chat_model
from orchestrator.graphs.rag_graph.graph import graph as rag_graph
from orchestrator.graphs.tour_graph.graph import graph as tour_graph
from utils.create_tool import create_handoff_tool
from utils.get_time import get_vietnam_time
from utils.handle_tool_err import create_tool_node_with_fallback
from utils.cut_messages import cut_messages

from .configuration import AgenticConfiguration
from .state import AgenticState


tools = [
    create_handoff_tool(
        agent_name=tour_graph.name,
        description="Tour booking specialist that handles ALL inquiries about FINDING or BOOKING travel packages and tours. ANY request containing 'tour', 'travel package', 'sightseeing', specific destinations with dates/timeframes ('Thailand in June'), or phrases like 'find tour', 'book tour', 'tour prices', 'tour itinerary' MUST be routed here. This tool exclusively manages tour searches, tour comparisons, tour availability, and tour booking operations.",
    ),
    create_handoff_tool(
        agent_name=rag_graph.name,
        description="General travel information assistant that ONLY handles factual queries about company policies, regulations, and reference information. Use EXCLUSIVELY for questions about baggage allowances, company contact information, general travel tips, and other informational inquiries that DON'T involve booking or searching for specific tours or flights.",
    ),
    # Future flight agent - included for reference
    # create_handoff_tool(
    #     agent_name=flight_graph.name,
    #     description="Flight booking and management specialist that handles ALL inquiries about FINDING, BOOKING or MANAGING flights. ANY request containing 'flight', 'airplane', 'airport', or phrases like 'fly to', 'book flight', 'flight status', 'check-in', 'boarding pass', 'flight schedule', 'flight prices' MUST be routed here. This tool exclusively manages flight searches, bookings, check-ins, and flight status information.",
    # ),
]


# Each delegated workflow can directly respond to the user
# When the user responds, we want to return to the currently active workflow
def route_to_workflow(
    state: AgenticState,
):
    """If we are in a delegated state, route directly to the appropriate assistant."""
    dialog_state = state["dialog_state"]
    if not dialog_state:
        return "agentic_agent"
    return dialog_state[-1]


def propagate_tokens_from_subgraph(state, subgraph_state):
    state["prompt_token"] = subgraph_state.get("prompt_token", 0)
    state["completion_token"] = subgraph_state.get("completion_token", 0)
    state["messages"] = subgraph_state["messages"]
    return state

async def tour_graph_with_token_propagation(state, *args, **kwargs):
    subgraph_state = await tour_graph.ainvoke(state, *args, **kwargs)
    return propagate_tokens_from_subgraph(state, subgraph_state)

async def rag_graph_with_token_propagation(state, *args, **kwargs):
    subgraph_state = await rag_graph.ainvoke(state, *args, **kwargs)
    return propagate_tokens_from_subgraph(state, subgraph_state)

async def agentic_agent(state: AgenticState, *, config: RunnableConfig) -> Dict[str, Any]:
    """Analyze the user's query and determine the appropriate routing.

    This function uses a language model to classify the user's query and decide how to route it
    within the conversation flow.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used for query analysis.

    Returns:
        dict[str, Router]: A dictionary containing the 'router' key with the classification result (classification type and logic).
    """

    configuration = AgenticConfiguration.from_runnable_config(config)
    model = create_chat_model(configuration.chat_model_config).bind_tools(tools)
    messages = [
        SystemMessage(content=configuration.system_prompt.format(time=get_vietnam_time())),
    ] + cut_messages(state["messages"], max_n_mess=20)
    response = await model.ainvoke(messages)

    return {"messages": response}


def route_after_llm(
    state: AgenticState,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    if tool_calls:
        return "tool_node"
    raise ValueError("Invalid route")


builder = StateGraph(AgenticState)

# Primary assistant
builder.add_node("agentic_agent", agentic_agent)
builder.add_node("tool_node", create_tool_node_with_fallback(tools))

builder.add_node(tour_graph.name, tour_graph_with_token_propagation)
builder.add_node(rag_graph.name, rag_graph_with_token_propagation)

builder.add_conditional_edges(
    START,
    route_to_workflow,
    ["agentic_agent", tour_graph.name, rag_graph.name],
)

builder.add_conditional_edges(
    "agentic_agent",
    route_after_llm,
    [
        "tool_node",
        END,
    ],
)

# Compile graph
memory = MemorySaver()
graph = builder.compile(checkpointer=memory)
