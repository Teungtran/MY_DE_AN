from typing import Any, Dict

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from langchain_core.messages import ToolMessage, SystemMessage
from langgraph.types import Command
from utils import tiktoken_counter
from factories.chat_factory import create_chat_model
from utils.handle_tool_err import create_tool_node_with_fallback
from utils.get_time import get_vietnam_time
from utils.cut_messages import cut_messages
from .configuration import TourAgentConfiguration
from .state import TourAgentState
from orchestrator.tools.tour_tools import (
    search_tour_program,
    tour_program_detail,
    tour_available_date,
    book_tour,
    cancel_tour,
)
from schemas.tour_schemas import CompleteOrEscalate


tour_safe_tools = [search_tour_program, tour_program_detail, tour_available_date]
tour_sensitive_tools = [book_tour, cancel_tour]
tour_tools = tour_safe_tools + tour_sensitive_tools + [CompleteOrEscalate]


async def tour_agent(state: TourAgentState, *, config: RunnableConfig) -> Dict[str, Any]:
    """Processes the user's request and determines if tools should be used.

    Args:
        state (AgentState): The current state of the agent.

    Returns:
        dict[str, list[str]]: A dictionary with 'documents' containing the retrieval results.
    """
    configuration = TourAgentConfiguration.from_runnable_config(config)
    model = create_chat_model(configuration.chat_model_config).bind_tools(tour_tools)
    messages = [
        SystemMessage(
            content=configuration.system_prompt.format(time=get_vietnam_time())
        ),
    ] + cut_messages(state["messages"], max_n_mess=20)
    prompt_token = tiktoken_counter(messages)
    
    state["prompt_token"] = state.get("prompt_token", 0) + prompt_token
    
    print(f"prompt_token: {state['prompt_token']}")
    
    response = await model.ainvoke(messages)    
    completion_token = tiktoken_counter([response])
    
    state["completion_token"] = state.get("completion_token", 0) + completion_token
    
    print(f"completion_token: {state['completion_token']}")
    print("\n---call_tour_agent")
    state["messages"] = [response]
    return state


def route_after_llm(
    state: TourAgentState,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in tour_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "tour_safe_tools"
    return "tour_sensitive_tools"


def pop_dialog_state(state: TourAgentState) -> dict:
    """Pop the dialog stack and return to the main assistant.

    This lets the full graph explicitly track the dialog flow and delegate control
    to specific sub-graphs.
    """
    if state["messages"][-1].tool_calls:
        # Note: Doesn't currently handle the edge case where the llm performs parallel tool calls
        tool_message = ToolMessage(
            content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
            tool_call_id=state["messages"][-1].tool_calls[0]["id"],
        )
    
    return Command(
        goto="agentic_agent",
        graph=Command.PARENT,
        update={
            "dialog_state": "pop",
            "messages": state["messages"] + [tool_message],
            "prompt_token": state.get("prompt_token", 0),
            "completion_token": state.get("completion_token", 0),
        },
    )


builder = StateGraph(TourAgentState)

builder.add_node("tour_agent", tour_agent)
builder.add_node(
    "tour_safe_tools",
    create_tool_node_with_fallback(tour_safe_tools),
)
builder.add_node(
    "tour_sensitive_tools",
    create_tool_node_with_fallback(tour_sensitive_tools),
)
builder.add_node("leave_skill", pop_dialog_state)

builder.add_edge(START, "tour_agent")
builder.add_edge("leave_skill", END)
builder.add_edge("tour_sensitive_tools", "tour_agent")
builder.add_edge("tour_safe_tools", "tour_agent")

builder.add_conditional_edges(
    "tour_agent",
    route_after_llm,
    ["tour_sensitive_tools", "tour_safe_tools", "leave_skill", END],
)

graph = builder.compile(interrupt_before=["tour_sensitive_tools"])
graph.name = "tour_agent"
