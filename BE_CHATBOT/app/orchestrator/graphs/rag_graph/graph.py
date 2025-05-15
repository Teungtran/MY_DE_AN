from typing import Any, Dict, List, Union

from langchain_core.messages import SystemMessage, ToolMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.prebuilt import tools_condition
from langgraph.types import Command

from factories.chat_factory import create_chat_model
from orchestrator.tools.retriever import retriever_tool
from schemas.tour_schemas import CompleteOrEscalate
from utils import measure_time, tiktoken_counter
from utils.get_time import get_vietnam_time
from utils.logging.logger import get_logger
from utils.cut_messages import cut_messages

from .configuration import RAGConfiguration
from .state import RAGAgentState

logger = get_logger(__name__)

rag_config = RAGConfiguration()


tools = [retriever_tool, CompleteOrEscalate]


# @title Default title text
class Agent:
    @measure_time  # Apply the decorator
    async def __call__(self, state: RAGAgentState, config: RunnableConfig) -> Dict[str, Union[List[Any], int]]:
        logger.info("\n---CALL AGENT---")
        configuration = RAGConfiguration.from_runnable_config(config)
        model = create_chat_model(configuration.chat_model_config).bind_tools(tools)
        messages = [
            SystemMessage(
                content=configuration.system_prompt.format(
                    time=get_vietnam_time(), max_tokens=configuration.chat_model_config.kwargs.get("max_tokens", 3000)
                )
            ),
        ] + state["messages"]

        print(f"tokens: {tiktoken_counter(messages)}")
        # filter_messages
        cuted_messages = cut_messages(messages)

        print(f"MSG LENGTH AFTER TRIMMING: {len(cuted_messages)}")
        prompt_token = tiktoken_counter(cuted_messages)

        state["prompt_token"] = state.get("prompt_token", 0) + prompt_token

        response = await model.ainvoke(cuted_messages, config)

        completion_token = tiktoken_counter([response])
        state["completion_token"] = state.get("completion_token", 0) + completion_token

        state["messages"] = [response]
        return state


def route_after_llm(
    state: RAGAgentState,
):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    if tool_calls:
        if tool_calls[0]["name"] == retriever_tool.name:
            return "run_tool_retriever"
    raise ValueError("Invalid route")


def pop_dialog_state(state: RAGAgentState) -> dict:
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
            "query": state.get("query", ""),
        },
    )


def convert_artifact(artifact: List[Dict]) -> List[str]:
    return list(set([x.get("source", None) for x in artifact if x.get("source", None)]))


@measure_time
async def run_tool_retriever(state: RAGAgentState):
    logger.info("\n---RUN TOOLS RETRIEVER---")
    new_messages = []
    tools = {"retrieve_information": retriever_tool}
    tool_calls = state["messages"][-1].tool_calls
    for tool_call in tool_calls:
        tool = tools[tool_call["name"]]
        content, artifact = await tool.ainvoke(tool_call["args"])
        new_messages.append(ToolMessage(
            content=content, 
            tool_call_id=tool_call["id"],
            artifact=convert_artifact(artifact),
            name=tool_call["name"],
        ))
    return {"messages": new_messages, "query": state["messages"][-1].tool_calls[0]["args"]["query"]}


async def generate_answer(state: RAGAgentState, *, config: RunnableConfig) -> Dict[str, Any]:
    """Generate a final response to the user's query based on the conducted research.

    This function formulates a comprehensive answer using the conversation history and the documents retrieved by the retriever.

    Args:
        state (AgentState): The current state of the agent, including retrieved documents and conversation history.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = RAGConfiguration.from_runnable_config(config)
    model = create_chat_model(configuration.chat_model_config)
    prompt = configuration.generate_prompt.format(context=state["messages"][-1].content)
    messages = [{"role": "system", "content": prompt}] + [state["query"]]
    response = await model.ainvoke(messages)
    return {"messages": response}


builder = StateGraph(RAGAgentState)

builder.add_node("rag_agent", Agent())
builder.add_node("run_tool_retriever", run_tool_retriever)
builder.add_node("generate_answer", generate_answer)
builder.add_node("leave_skill", pop_dialog_state)

# Define the edges (connections between the nodes)
builder.add_edge(START, "rag_agent")
builder.add_edge("run_tool_retriever", "generate_answer")
builder.add_edge("generate_answer", END)
builder.add_edge("leave_skill", END)
builder.add_conditional_edges(
    "rag_agent",
    route_after_llm,
    [
        "run_tool_retriever",
        "leave_skill",
        END,
    ],
)
# Compile the workflow
graph = builder.compile()
graph.name = "rag_agent"
