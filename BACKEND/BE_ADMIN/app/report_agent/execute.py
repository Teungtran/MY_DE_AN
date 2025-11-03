from langchain_core.messages import HumanMessage
from .main_agent import create_graph
from utils.logging.logger import get_logger
def format_message(message):
    """Format a message for display without modifying it too much."""
    if hasattr(message, "content") and message.content:
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(message)

logger = get_logger("AI Data Analyst")
graph = create_graph()

def trigger(user_message:str) -> str:
    initial_state = {
        "messages": [HumanMessage(content=user_message)]
    }

    config = {
        "configurable": {"thread_id": "333"}
    }

    events = graph.stream(
        initial_state,
        config=config,
        stream_mode="values",
    )

    processed_set = set()
    all_messages = []
    all_tool_calls = []

    for event in events:
        if "messages" in event:
            for message in event["messages"]:
                msg_content = format_message(message)
                msg_hash = hash(msg_content)
                if msg_hash not in processed_set:
                    processed_set.add(msg_hash)
                    all_messages.append({
                        "content": msg_content,
                        "message": message
                    })

                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            all_tool_calls.append({
                                "id": tool_call.get("id"),
                                "name": tool_call.get("name"),
                                "args": tool_call.get("args", {}),
                                "type": tool_call.get("type", "function")
                            })

    final_response = ""
    for msg_data in reversed(all_messages):
        content = msg_data["content"]
        message = msg_data["message"]
        message_type = type(message).__name__

        if (message_type == "AIMessage" and
            content and content.strip() and
            not content.startswith("content=''") and
            not content.startswith("The assistant is now")):
            final_response = content
            break

    final_tool_call = all_tool_calls[-1] if all_tool_calls else None
    if final_tool_call:
        logger.info("Tool Call Detected:")
        logger.info(f"Tool Call ID:   {final_tool_call['id']}")
        logger.info(f"Tool Call Name: {final_tool_call['name']}")
        logger.info(f"Tool Call Type: {final_tool_call['type']}")
        logger.info(f"Tool Call Args: {final_tool_call['args']}")
    else:
        logger.info("No tool call found.")

    return final_response
