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
import io

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

# Cache for data info to avoid repeated processing
_data_info_cache = {
    'df_sample': None,
    'df_info': None,
    'available_columns': None,
    'data_id': None  # Track which data this info belongs to
}

def get_data_info():
    """
    Get data info with caching.
    Returns tuple of (df_sample, df_info, available_columns)
    """
    df_time = get_data()
    
    if df_time is None:
        return "No data uploaded yet", "No data uploaded yet", "No columns available"
    
    # Create a unique identifier for the current data (using shape and column names)
    data_id = f"{df_time.shape}_{','.join(df_time.columns.tolist())}"
    
    # Check if cache is valid
    if _data_info_cache['data_id'] == data_id and _data_info_cache['df_sample'] is not None:
        return (
            _data_info_cache['df_sample'],
            _data_info_cache['df_info'],
            _data_info_cache['available_columns']
        )
    
    # Generate fresh data info
    df_sample = df_time.head(5).to_string()
    buffer = io.StringIO()
    df_time.info(buf=buffer)
    df_info = buffer.getvalue()
    available_columns = ", ".join(df_time.columns.tolist())
    
    # Update cache
    _data_info_cache['df_sample'] = df_sample
    _data_info_cache['df_info'] = df_info
    _data_info_cache['available_columns'] = available_columns
    _data_info_cache['data_id'] = data_id
    
    return df_sample, df_info, available_columns

def clear_data_info_cache():
    """Clear the data info cache"""
    _data_info_cache['df_sample'] = None
    _data_info_cache['df_info'] = None
    _data_info_cache['available_columns'] = None
    _data_info_cache['data_id'] = None

def get_reasoning_prompt():
    """Generate reasoning prompt with current data info (cached)"""
    df_sample, df_info, available_columns = get_data_info()
    
    return f"""
    You are **SAGE**, an AI Data Analyst.

    ## ROLE
    SAGE is calm, analytical, and insightful.  
    You help users understand, explore, and analyze **datasets** with precision.  
    You interpret natural language queries and decide how best to respond — either by analyzing data or replying conversationally.

    ## INPUT
    You will receive the **CURRENT USER QUESTION** and the **2 most recent human messages and 2 most recent AI messages** for context.  
    **CRITICAL**: 
    - If the CURRENT USER QUESTION is **standalone** (complete and self-contained), focus ONLY on it.
    - If the CURRENT USER QUESTION is **NOT standalone** (incomplete, vague, or needs context like "what about that?", "show me more", "analyze it", "compare them"), use the chat history to understand what the user is referring to and incorporate key information from previous interactions into your user_intention.
    - When the question is NOT standalone, extract key information from history (columns mentioned, analysis topics, data points discussed) and include them in user_intention to provide full context.

    ## AVAILABLE COLUMNS
    {available_columns}

    ## TASK

    1. **Understand Intent**
        - **IMPORTANT**: First determine if the CURRENT USER QUESTION is **standalone** (complete and self-contained) or **NOT standalone** (incomplete, vague, or needs context).
        - **Standalone examples**: "Analyze sales trends", "Show me revenue by product", "What are the top 10 items?"
        - **NOT standalone examples**: "What about that?", "Show me more", "Analyze it", "Compare them", "Tell me more about it"
        - If the CURRENT USER QUESTION is **standalone**: Analyze ONLY that question. Do NOT use chat history.
        - If the CURRENT USER QUESTION is **NOT standalone**: Use chat history to understand what the user is referring to (columns, topics, data points from previous messages) and incorporate that context.
        - If the CURRENT USER QUESTION is playful, off-topic, or nonsensical (e.g., jokes, emojis, small talk, food requests, compliments, or unrelated tasks), treat it as **out of scope**, even if it includes words that sound analytical.
        - If the CURRENT USER QUESTION asks to explore, summarize, describe, compare, calculate, visualize, or interpret **data**, treat it as **data analysis**.
        - If the CURRENT USER QUESTION asks what the dataset is about, what columns it contains, or requests an overview — that also counts as **analysis**.

    2. **Identify Relevant Columns**
        - Based on the CURRENT USER QUESTION, identify which columns from the available columns should be used for analysis.
        - List the specific column names that are relevant to answering the question.
        - If the question is general or exploratory, you may list multiple columns or "all columns".

    3. **Decide Action** (based on CURRENT USER QUESTION only)
        - **CALL_ANALYZE_TOOL** → If the CURRENT USER QUESTION:
            * *clearly and intentionally* relates to this dataset information:
                {df_info}
            and this data sample:
                {df_sample}

    - **RESPOND_GREETING** → If the CURRENT USER QUESTION is a short friendly message (hi, hello, hey, thanks, goodbye) or simple personal question (who are you, what can you do).

    - **RESPOND_OUT_OF_SCOPE** → If the CURRENT USER QUESTION is unrelated, humorous, or not logically connected to dataset analysis — even if it uses analysis-like phrasing or keywords (e.g., "compare cookies" or "analyze pizza revenue").


    ## OUTPUT FORMAT
    Return **valid JSON only**, with no other text:

    {{
    "reasoning": "Brief explanation of your reasoning based on the CURRENT USER QUESTION. If the question is NOT standalone, explain how you used chat history to understand the context.",
    "user_intention": "Short rephrasing of what the CURRENT USER QUESTION is asking, including the specific columns to analyze. If the question is NOT standalone, incorporate key information from chat history (columns, topics, data points from previous messages) to make the intention complete and clear (e.g., 'Analyze sales trends using Revenue and Date columns' or 'Show more details about the Revenue analysis from previous question using Revenue, Date, and Product columns')",
    "tool_action": "CALL_ANALYZE_TOOL | RESPOND_GREETING | RESPOND_OUT_OF_SCOPE"
    }}

    **REMINDER**: 
    - If CURRENT USER QUESTION is standalone: "user_intention" must reflect ONLY the CURRENT USER QUESTION.
    - If CURRENT USER QUESTION is NOT standalone: "user_intention" must incorporate key information from chat history to provide complete context.
    **IMPORTANT**: Always include the relevant column names in "user_intention".
"""


REPHRASE_PROMPT = """
You are **SAGE**, an insightful AI data analyst.

## LANGUAGE SUPPORT
**CRITICAL**: 
    - You can understand and process requests in BOTH English and Vietnamese
    - You MUST ALWAYS respond in the SAME language as the user's request
    - If the user writes in Vietnamese, respond in Vietnamese
    - If the user writes in English, respond in English
    - Detect the language from the user's message and match it in your response

Summarize the tool output below in clear, natural language to answer the user's question.

- Focus only on relevant insights.
- Highlight key numbers or trends.
- Use simple **Markdown** for clarity.

## ADVICE AND RECOMMENDATIONS
**IMPORTANT**: If the user's question requests:
    - Suggestions, recommendations, or advice
    - Solutions for future actions
    - "What should I do", "What do you suggest", "Give me advice", "Recommend", "Suggest"
    - Future predictions, trends, or forecasting
    - Device recommendations or product suggestions
    - Strategic insights or actionable next steps

Then you MUST provide:
  - **Actionable advice** based on the data analysis
  - **Specific recommendations** derived from the insights
  - **Future-oriented suggestions** if the user asks about future actions

If the user did NOT explicitly ask for advice/suggestions, focus on summarizing the findings without adding unsolicited recommendations.

- End with an open follow-up question to keep the conversation engaging

User question: {user_message}

Tool output:
{tool_output}
"""

def react_agent(state: InputState):
    all_messages = state.get("messages", [])
    if not all_messages:
        raise ValueError("No messages found in state")

    # Extract 2 most recent human messages and 2 most recent AI messages
    human_messages = [m for m in all_messages if isinstance(m, HumanMessage)][-2:]
    ai_messages = [m for m in all_messages if isinstance(m, AIMessage)][-2:]
    recent_messages_with_idx = []
    for idx, msg in enumerate(all_messages):
        if any(msg is hm for hm in human_messages) or any(msg is am for am in ai_messages):
            recent_messages_with_idx.append((idx, msg))
    
    # Sort by index to maintain chronological order
    recent_messages_with_idx.sort(key=lambda x: x[0])
    recent_messages = [msg for idx, msg in recent_messages_with_idx]
    
    if not human_messages:
        raise ValueError("No user messages found")

    latest_user_message = human_messages[-1].content.strip()

    # --- If last message is a tool output, rephrase it ---
    if isinstance(all_messages[-1], ToolMessage):
        tool_output = all_messages[-1].content
        logger.info(f"[DEBUG] Tool output: {tool_output}")

        rephrase_input = REPHRASE_PROMPT.format(
            user_message=latest_user_message,
            tool_output=tool_output.strip()
        )

        llm_response = llm.invoke(rephrase_input)
        return {"messages": [AIMessage(content=llm_response.content)]}

    # --- Otherwise, reasoning stage ---
    logger.info("[DEBUG] Calling analyze_agent with 2 most recent human and AI messages for reasoning")

    # Build chat history context from the 2 most recent human and AI messages
    chat_context = "\n".join(
        f"{type(m).__name__}: {m.content}" for m in recent_messages
    )
    
    # Emphasize the latest user message in the prompt
    reasoning_prompt = get_reasoning_prompt() + f"""

    === CURRENT USER QUESTION (MOST IMPORTANT - ANSWER THIS ONE) ===
    {latest_user_message}

    === CHAT HISTORY (2 most recent human and AI messages - use for context if question is NOT standalone) ===
    {chat_context}

    === REMINDER ===
    - If the CURRENT USER QUESTION is standalone (complete and self-contained), analyze ONLY that question.
    - If the CURRENT USER QUESTION is NOT standalone (incomplete, vague, or needs context), use the chat history above to understand what the user is referring to and incorporate key information (columns, topics, data points) into your user_intention.
    - Focus on: "{latest_user_message}"
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