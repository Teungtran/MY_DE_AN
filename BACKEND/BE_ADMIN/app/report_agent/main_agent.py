from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from app.utils.logging.logger import get_logger
from pydantic import SecretStr
from langchain_openai import ChatOpenAI
from app.config.base_config import OpenAIConfig
from typing import Callable
import json
from .state import InputState
from .agent import analyze_agent, get_data
from langgraph.prebuilt import tools_condition
from .state import create_tool_node_with_fallback
from langchain_core.messages import ToolMessage
from langgraph.graph.state import StateGraph,CompiledStateGraph

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

logger = get_logger("AI Data Analyst")

def get_reasoning_prompt():
    """Generate reasoning prompt with current data info"""
    df_time = get_data()
    if df_time is None:
        df_sample = "No data uploaded yet"
        df_info = "No data uploaded yet"
        available_columns = "No columns available"
    else:
        df_sample = df_time.head(5).to_string()
        # Capture df.info() output as string
        import io
        buffer = io.StringIO()
        df_time.info(buf=buffer)
        df_info = buffer.getvalue()
        available_columns = ", ".join(df_time.columns.tolist())
    
    return f"""
    You are **SAGE**, an AI Data Analyst.

    ## ROLE
    SAGE is calm, analytical, and insightful.  
    You help users understand, explore, and analyze **datasets** with precision.  
    You interpret natural language queries and decide how best to respond — either by analyzing data or replying conversationally.

    ## INPUT
    You will receive the **CURRENT USER QUESTION** and up to the **last 10 chat messages** (user + assistant) for context.  
    **CRITICAL**: You MUST focus ONLY on the **CURRENT USER QUESTION** - ignore all previous questions in the chat history.
    The chat history is provided only for context, but your analysis must be based solely on the current question.

    ## AVAILABLE COLUMNS
    {available_columns}

    ## TASK

    1. **Understand Intent**
    - **IMPORTANT**: Analyze ONLY the CURRENT USER QUESTION provided above. Do NOT analyze questions from the chat history.
    - Identify what the user is really asking in the CURRENT USER QUESTION.
    - If the CURRENT USER QUESTION is playful, off-topic, or nonsensical (e.g., jokes, emojis, small talk, food requests, compliments, or unrelated tasks), treat it as **out of scope**, even if it includes words that sound analytical.
    - If the CURRENT USER QUESTION asks to explore, summarize, describe, compare, calculate, visualize, or interpret **data**, treat it as **data analysis**.
    - If the CURRENT USER QUESTION asks what the dataset is about, what columns it contains, or requests an overview — that also counts as **analysis**.

    2. **Identify Relevant Columns**
    - Based on the CURRENT USER QUESTION, identify which columns from the available columns should be used for analysis.
    - List the specific column names that are relevant to answering the question.
    - If the question is general or exploratory, you may list multiple columns or "all columns".

    3. **Decide Action** (based on CURRENT USER QUESTION only)
    - **CALL_ANALYZE_TOOL** → Only if the CURRENT USER QUESTION *clearly and intentionally* relates to this dataset information:
            {df_info}
        and this data sample:
            {df_sample}
        OR if the CURRENT USER QUESTION explicitly wants to know more about the current dataset (its structure, content, or insights).

    - **RESPOND_GREETING** → If the CURRENT USER QUESTION is a short friendly message (hi, hello, hey, thanks, goodbye) or simple personal question (who are you, what can you do).

    - **RESPOND_OUT_OF_SCOPE** → If the CURRENT USER QUESTION is unrelated, humorous, or not logically connected to dataset analysis — even if it uses analysis-like phrasing or keywords (e.g., "compare cookies" or "analyze pizza revenue").


    ## OUTPUT FORMAT
    Return **valid JSON only**, with no other text:

    {{
    "reasoning": "Brief explanation of your reasoning based on the CURRENT USER QUESTION only",
    "user_intention": "Short rephrasing of what the CURRENT USER QUESTION is asking, including the specific columns to analyze (e.g., 'Analyze sales trends using Revenue and Date columns')",
    "tool_action": "CALL_ANALYZE_TOOL | RESPOND_GREETING | RESPOND_OUT_OF_SCOPE"
    }}

    **REMINDER**: Your "user_intention" must reflect the CURRENT USER QUESTION, not any previous questions from chat history.
    **IMPORTANT**: Always include the relevant column names in "user_intention" and "columns_to_use".
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

    # Build chat history context
    chat_context = "\n".join(
        f"{type(m).__name__}: {m.content}" for m in recent_messages
    )
    
    # Emphasize the latest user message in the prompt
    reasoning_prompt = get_reasoning_prompt() + f"""

    === CURRENT USER QUESTION (MOST IMPORTANT - ANSWER THIS ONE) ===
    {latest_user_message}

    === CHAT HISTORY (for context only) ===
    {chat_context}

    === REMINDER ===
    The CURRENT USER QUESTION above is what you must analyze. Ignore any previous questions in the chat history.
    Focus ONLY on: "{latest_user_message}"
    """

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
        # Pass the entire parsed reasoning result to the tool
        tool_input = {
            "user_question": latest_user_message,
            "reasoning": parsed.get("reasoning", ""),
            "user_intention": parsed.get("user_intention", ""),
        }
        result = llm.bind_tools(tools).invoke([
            HumanMessage(content=json.dumps(tool_input))
        ])
        return {"messages": [result]}

    else:
        logger.info("[WARN] Unknown tool_action, defaulting to polite fallback.")
        return {"messages": [AIMessage(content="I’m not sure how to handle that request. Could you clarify what kind of analysis you need?")]}
    
    
def create_graph() -> CompiledStateGraph:
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
    return graph