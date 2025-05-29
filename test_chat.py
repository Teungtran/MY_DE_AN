import uuid
from typing import Set, Dict, Any, Optional
from langchain_core.messages import ToolMessage, HumanMessage

from app.orchestrator.graphs.main_graph.graph import setup_agentic_graph

def clear_screen():
    """Clear the console screen."""
    print("\n" + "-" * 80 + "\n")

def format_message(message):
    """Format a message for display."""
    if hasattr(message, "content") and message.content:
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(message)

def print_event(event, printed_set: Set[str]):
    """Print new messages from an event."""
    if "messages" in event:
        for message in event["messages"]:
            msg_content = format_message(message)
            msg_hash = hash(msg_content)
            
            if msg_hash not in printed_set:
                if hasattr(message, "type") and message.type == "human":
                    print(f"\nYou: {msg_content}")
                else:
                    print(f"\nAssistant: {msg_content}")
                printed_set.add(msg_hash)
                
                # Check for tool calls
                if hasattr(message, "tool_calls") and message.tool_calls:
                    for tool_call in message.tool_calls:
                        print(f"\n[Tool Call] {tool_call['name']}: {tool_call.get('args', {})}")

def main():
    """Run the chat test interface."""
    print("Initializing FPT Shop Assistant Chat Test...")
    
    # Initialize the graph
    graph = setup_agentic_graph()
    
    # Create a thread ID for this conversation
    thread_id = str(uuid.uuid4())
    print(f"Session ID: {thread_id}")
    
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    
    printed = set()
    conversation_active = True
    
    print("\nWelcome to the FPT Shop Assistant! Type 'exit' to end the conversation.")
    
    while conversation_active:
        # Get user input
        user_message = input("\nYou: ")
        
        if user_message.lower() in ["exit", "quit", "bye"]:
            print("Thank you for using FPT Shop Assistant! Goodbye.")
            conversation_active = False
            continue
        
        # Start or continue the conversation
        if "messages" not in config.get("state", {}):
            # First message in conversation
            events = graph.stream(
                {"messages": [HumanMessage(content=user_message)]}, 
                config, 
                stream_mode="values"
            )
        else:
            # Continuing conversation
            events = graph.stream(
                {"messages": [HumanMessage(content=user_message)]}, 
                config, 
                stream_mode="values"
            )
            
        # Process and print events
        last_event = None
        for event in events:
            print_event(event, printed)
            last_event = event
        
        # Check if we need user approval for a tool call
        snapshot = graph.get_state(config)
        while snapshot.next:
            # There's a pending tool call that needs approval
            if last_event and "messages" in last_event and last_event["messages"] and hasattr(last_event["messages"][-1], "tool_calls"):
                tool_call = last_event["messages"][-1].tool_calls[0]
                user_approval = input("\nDo you approve this tool call? (y/n): ")
                
                if user_approval.lower() == "y":
                    # Approve and continue
                    result = graph.invoke(None, config)
                else:
                    # User rejected, provide feedback
                    user_feedback = input("\nPlease explain why you rejected or what changes you want: ")
                    result = graph.invoke(
                        {
                            "messages": [
                                ToolMessage(
                                    tool_call_id=tool_call["id"],
                                    content=f"API call denied by user. Reasoning: '{user_feedback}'. Continue assisting, accounting for the user's input.",
                                )
                            ]
                        },
                        config,
                    )
                
                # Print the result
                if "messages" in result:
                    for message in result["messages"]:
                        msg_content = format_message(message)
                        msg_hash = hash(msg_content)
                        if msg_hash not in printed:
                            print(f"\nAssistant: {msg_content}")
                            printed.add(msg_hash)
                
                snapshot = graph.get_state(config)

if __name__ == "__main__":
    main() 