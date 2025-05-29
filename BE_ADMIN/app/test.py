import uuid
import asyncio
from langchain_core.messages import ToolMessage

from orchestrator.graphs.agentic_graph.graph import graph

# Update with the backup file so we can restart from the original place in each section
thread_id = str(uuid.uuid4())

config = {
    "configurable": {
        # The passenger_id is used in our flight tools to
        # fetch the user's flight information
        "passenger_id": "3442 587242",
        # Checkpoints are accessed by thread_id
        "thread_id": thread_id,
    }
}

_printed = set()
# Let's create an example conversation a user might have with the assistant
questions = [
    "Hi there, I want to find tour to Thailand on June.",
    # "It seem great. Can you book that tour for me for 2 people?",
    # "My departure location will be from Ha Noi. I will go on 25/6 and comeback on 27/6."
]

def _print_event(event: dict, _printed: set, max_length=1500):
    current_state = event.get("dialog_state")
    if current_state:
        print("Currently in: ", current_state[-1])
    message = event.get("messages")
    if message:
        if isinstance(message, list):
            message = message[-1]
        if message.id not in _printed:
            msg_repr = message.pretty_repr(html=True)
            if len(msg_repr) > max_length:
                msg_repr = msg_repr[:max_length] + " ... (truncated)"
            print(msg_repr)
            _printed.add(message.id)

# async def main():
#     for question in questions:
#         events = graph.astream(
#             {"messages": ("user", question)}, config, stream_mode="messages", subgraphs=True
#         )
#         async for k, event in events:
#             print(k, event, sep="\n\n")
#             print("="*80)
#         snapshot = graph.get_state(config)
#         while snapshot.next:
#             # We have an interrupt! The agent is trying to use a tool, and the user can approve or deny it
#             try:
#                 user_input = input(
#                     "Do you approve of the above actions? Type 'y' to continue;"
#                     " otherwise, explain your requested changed.\n\n"
#                 )
#             except:
#                 user_input = "y"
#             if user_input.strip() == "y":
#                 # Just continue
#                 result = await graph.ainvoke(
#                     None,
#                     config,
#                     subgraphs=True
#                 )
#                 print(1111, result)
#             else:
#                 # Satisfy the tool invocation by
#                 # providing instructions on the requested changes / change of mind
#                 result = await graph.ainvoke(
#                     {
#                         "messages": [
#                             ToolMessage(
#                                 tool_call_id=event["messages"][-1].tool_calls[0]["id"],
#                                 content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
#                             )
#                         ]
#                     },
#                     config,
#                 )
#             snapshot = graph.get_state(config)


async def main():
    for question in questions:
        # Initial query
        current_input = {"messages": ("user", question)}
        
        while True:
            # Stream the current part of the interaction
            events = graph.astream(
                current_input, config, stream_mode="messages", subgraphs=True
            )
            
            # Process output events
            last_event = None
            last_node = None
            async for node_name, event in events:
                print(f"Node: {node_name}")
                print(event)
                print("="*80)
                last_event = event
                last_node = node_name
            
            # Check if graph needs human input
            snapshot = graph.get_state(config)
            if not snapshot.next:
                # Conversation is complete for this question
                break
            
            # Get last message with tool calls directly from the snapshot
            last_message = None
            if "messages" in snapshot.values:
                messages = snapshot.values["messages"]
                for msg in reversed(messages):
                    if hasattr(msg, "tool_calls") and msg.tool_calls:
                        last_message = msg
                        break
            
            if not last_message:
                print("Could not find a message with tool calls to respond to.")
                break
            
            # Get human input
            try:
                user_input = input(
                    "Do you approve of the above actions? Type 'y' to continue;"
                    " otherwise, explain your requested changes.\n\n"
                )
            except:
                user_input = "y"
            
            if user_input.strip() == "y":
                # Continue with default execution
                current_input = None
            else:
                # Provide feedback through tool message
                current_input = {
                    "messages": [
                        ToolMessage(
                            tool_call_id=last_message.tool_calls[0]["id"],
                            content=f"API call denied by user. Reasoning: '{user_input}'. Continue assisting, accounting for the user's input.",
                        )
                    ]
                }
        
        # Add a separator between different questions
        print("\n" + "="*80 + "\n" + "Next question" + "\n" + "="*80 + "\n")


# Run the async function
if __name__ == "__main__":
    asyncio.run(main())