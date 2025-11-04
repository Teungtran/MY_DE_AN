from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from app.utils.logging.logger import get_logger
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from app.config.base_config import OpenAIConfig
from typing import Callable
import json
from .state import InputState
from .agent import analyze_agent,df_time
from langgraph.prebuilt import tools_condition
from .state import create_tool_node_with_fallback
from langchain_core.messages import ToolMessage
from langgraph.graph import StateGraph
from langgraph.checkpoint.memory import MemorySaver
chat_config = OpenAIConfig()

api_key = chat_config.api_key
if isinstance(api_key, Callable):
    api_key = api_key()  
if isinstance(api_key, SecretStr):  
    api_key = api_key.get_secret_value()
def ai_model():
    return ChatOpenAI(
        openai_api_key=api_key,
        model="gpt-4o-mini",
        temperature=0
    )
llm = ai_model()
tools = [analyze_agent]

df_sample = df_time.head(5).to_string()
df_info = df_time.info()
logger = get_logger("AI Data Analyst")
REASONING_PROMPT = f"""
    You are **SAGE**, an AI Data Analyst.

    ## ROLE
    SAGE is calm, analytical, and insightful.  
    You help users understand, explore, and analyze **datasets** with precision.  
    You interpret natural language queries and decide how best to respond — either by analyzing data or replying conversationally.

    ## INPUT
    You will receive up to the **last 10 chat messages** (user + assistant).  
    Focus mainly on the **latest user message** to determine intent.

    ---

    ## TASK

    1. **Understand Intent**
    - Identify what the user is really asking.
    - If the message is playful, off-topic, or nonsensical (e.g., jokes, emojis, small talk, food requests, compliments, or unrelated tasks), treat it as **out of scope**, even if it includes words that sound analytical.
    - If the user asks to explore, summarize, describe, compare, calculate, visualize, or interpret **data**, treat it as **data analysis**.
    - If they ask what the dataset is about, what columns it contains, or request an overview — that also counts as **analysis**.

    2. **Decide Action**
    - **CALL_ANALYZE_TOOL** → Only if the user’s query *clearly and intentionally* relates to this dataset information:
            {df_info}
        and this data sample:
            {df_sample}
        OR if they explicitly want to know more about the current dataset (its structure, content, or insights).

    - **RESPOND_GREETING** → For short friendly messages (hi, hello, hey, thanks, goodbye) or simple personal questions (who are you, what can you do).

    - **RESPOND_OUT_OF_SCOPE** → For anything that is unrelated, humorous, or not logically connected to dataset analysis — even if it uses analysis-like phrasing or keywords (e.g., "compare cookies" or "analyze pizza revenue").

    ---

    ## OUTPUT FORMAT
    Return **valid JSON only**, with no other text:

    {{
    "reasoning": "Brief natural-language explanation of your reasoning",
    "user_intention": "Short rephrasing of what the user asked",
    "tool_action": "CALL_ANALYZE_TOOL | RESPOND_GREETING | RESPOND_OUT_OF_SCOPE"
    }}
"""


REPHRASE_PROMPT = """
You are **SAGE**, an insightful AI data analyst.

Summarize the tool output below in clear, natural English to answer the user’s question.

- Focus only on relevant insights.
- Highlight key numbers or trends.
- Use simple **Markdown** for clarity.
- End with a open follow-up question to keep the conversation engaging

User question: {user_message}

Tool output:
{tool_output}
"""

def react_agent(state: InputState):
    all_messages = state.get("messages", [])
    if not all_messages:
        raise ValueError("No messages found in state")

    recent_messages = all_messages[-10:]
    user_messages = [m for m in recent_messages if isinstance(m, HumanMessage)]
    if not user_messages:
        raise ValueError("No user messages found")

    latest_user_message = user_messages[-1].content.strip()

    # --- If last message is a tool output, rephrase it ---
    if isinstance(recent_messages[-1], ToolMessage):
        tool_output = recent_messages[-1].content
        logger.info(f"[DEBUG] Tool output: {tool_output}")

        rephrase_input = REPHRASE_PROMPT.format(
            user_message=latest_user_message,
            tool_output=tool_output.strip()
        )

        llm_response = llm.invoke(rephrase_input)
        return {"messages": [AIMessage(content=llm_response.content)]}

    # --- Otherwise, reasoning stage ---
    logger.info("[DEBUG] Calling analyze_agent with latest 10 messages for reasoning")

    chat_context = "\n".join(
        f"{type(m).__name__}: {m.content}" for m in recent_messages
    )
    reasoning_prompt = REASONING_PROMPT + "\n\nChat History:\n" + chat_context

    reasoning_result = llm.invoke(reasoning_prompt)
    raw = reasoning_result.content
    logger.info(f"[DEBUG] analyze_agent result: {raw}")

    try:
        parsed = json.loads(raw)
    except json.JSONDecodeError:
        logger.info("[WARN] Failed to parse reasoning output as JSON.")
        return {"messages": [AIMessage(content="Sorry, I didn’t understand that request clearly. Could you rephrase?")]}

    tool_action = parsed.get("tool_action", "").upper()

    if tool_action in ["RESPOND_GREETING", "RESPOND_OUT_OF_SCOPE"]:
        if tool_action == "RESPOND_GREETING":
            base_message = (
                "The user sent a greeting or casual message. "
                "Respond warmly and invite them to start a data analysis question."
            )
        else:
            base_message = (
                "The user's request is unrelated to the dataset. "
                "Politely refuse and guide them back to asking data-related questions."
            )

        rephrase_input = REPHRASE_PROMPT.format(
            user_message=latest_user_message,
            tool_output=base_message
        )

        llm_response = llm.invoke(rephrase_input)
        return {"messages": [AIMessage(content=llm_response.content)]}

    elif tool_action == "CALL_ANALYZE_TOOL":
        logger.info("[DEBUG] Triggering analyze_agent tool call")
        result = llm.bind_tools(tools).invoke([
            HumanMessage(content=latest_user_message)
        ])
        return {"messages": [result]}

    else:
        logger.info("[WARN] Unknown tool_action, defaulting to polite fallback.")
        return {"messages": [AIMessage(content="I’m not sure how to handle that request. Could you clarify what kind of analysis you need?")]}
    
    
def create_graph():
    graph_agent = StateGraph(InputState)

    graph_agent.add_node("AGENT", react_agent)
    graph_agent.add_node("tools", create_tool_node_with_fallback(tools))

    graph_agent.set_entry_point("AGENT")  
    graph_agent.add_conditional_edges("AGENT", tools_condition)
    graph_agent.add_edge("tools", "AGENT") 

    graph = graph_agent.compile(
                checkpointer=MemorySaver(),
                name="Agent Graph",
            )