import re
from typing import Annotated

from langgraph.types import Command
from langchain_core.messages import ToolMessage
from langgraph.prebuilt import InjectedState
from langchain_core.tools import BaseTool, InjectedToolCallId, tool


def create_handoff_tool(*, agent_name: str, description: str | None = None) -> BaseTool:
    """Create a tool that can handoff control to the requested agent.

    Args:
        agent_name: The name of the agent to handoff control to, i.e.
            the name of the agent node in the multi-agent graph.
            Agent names should be simple, clear and unique, preferably in snake_case,
            although you are only limited to the names accepted by LangGraph
            nodes as well as the tool names accepted by LLM providers
            (the tool name will look like this: `transfer_to_<agent_name>`).
        description: Optional description for the handoff tool.
    """
    # precessed_name = re.compile(r'\s+').sub('_', agent_name.strip()).lower()
    # name = f"transfer_to_{precessed_name}"
    if description is None:
        description = f"Ask agent '{agent_name}' for help"

    @tool(agent_name, description=description)
    def handoff_to_agent(
        state: Annotated[dict, InjectedState],
        tool_call_id: Annotated[str, InjectedToolCallId],
    ):
        tool_message = ToolMessage(
            content=f"The assistant is now the {agent_name}. Reflect on the above conversation between the host assistant and the user."
            f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {agent_name},"
            " and the booking, update, other other action is not complete until after you have successfully invoked the appropriate tool."
            " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
            " Do not mention who you are - just act as the proxy for the assistant.",
            name=agent_name,
            tool_call_id=tool_call_id,
        )
        return Command(
            goto=agent_name,
            update={"messages": state["messages"] + [tool_message], "dialog_state": agent_name},
        )

    return handoff_to_agent