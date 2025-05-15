from langchain_core.messages import trim_messages


def cut_messages(messages, max_n_mess=6):
    return trim_messages(
        messages,
        token_counter=len,
        # Keep the last <= n_count tokens of the messages.
        strategy="last",
        # When token_counter=len, each message
        # will be counted as a single token.
        # Remember to adjust for your use case
        max_tokens=max_n_mess,
        # Most chat models expect that chat history starts with either:
        # (1) a HumanMessage or
        # (2) a SystemMessage followed by a HumanMessage
        start_on="human",
        # Most chat models expect that chat history ends with either:
        # (1) a HumanMessage or
        # (2) a ToolMessage
        end_on=("human", "tool"),
        # Usually, we want to keep the SystemMessage
        # if it's present in the original history.
        # The SystemMessage has special instructions for the model.
        include_system=True,
    )