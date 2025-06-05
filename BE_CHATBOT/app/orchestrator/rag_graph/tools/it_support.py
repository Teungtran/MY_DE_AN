import os
from langchain_community.tools import TavilySearchResults
import datetime
import warnings
warnings.filterwarnings('ignore')
from langchain_core.runnables import RunnableConfig, chain
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config.base_config import APP_CONFIG
from factories.chat_factory import create_chat_model
import os
chat_config = APP_CONFIG.chat_model_config
search_config = APP_CONFIG.search_config
if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)


trusted_tech_domains = [
    "support.apple.com",
    "support.microsoft.com",
    "support.google.com",
    "ifixit.com",
    "tomsguide.com",
    "cnet.com",
    "techradar.com",
    "theverge.com",
    "xda-developers.com",
    "androidauthority.com",
    "appleinsider.com",
    "macrumors.com",
    "reddit.com/r/techsupport",
]

# Load config
chat_config = APP_CONFIG.chat_model_config
search_config = APP_CONFIG.search_config

if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),
        model="gpt-4o-mini",
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)

it_support_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_images=True,
    include_answer=True,
    include_raw_content=True,
    api_key=search_config.api_key,
    description="A search engine optimized for accurate and up-to-date technical support information for laptops, phones, and related devices. Input should be a clear technical question or issue description.",
    include_domains=trusted_tech_domains
)

def create_it_support_chain():
    today = datetime.datetime.now().strftime("%B %d, %Y")
    
    prompt = ChatPromptTemplate.from_messages([
        ("system", f"""You are an IT support and device maintenance assistant specialized in:
        1. Troubleshooting laptops, phones, and related devices
        2. Device cleaning and maintenance
        3. Electronics care and sanitization
        4. Technical guidance and best practices

        Today's date is {today}. Your task is to find the most accurate and recent information to help the user with their technical or maintenance needs.
        End with the IT support phone number (18006601)
        Your goal is to provide accurate, unmodified technical information while maintaining all source links."""),
        ("human", "{user_input}")
    ])
    
    llm_with_tools = llm.bind_tools([it_support_tool])
    llm_chain = prompt | llm_with_tools
    return llm_chain

@chain
def it_support_logic(user_input: str):
    config = RunnableConfig()
    llm_chain = create_it_support_chain()
    input_ = {"user_input": user_input}
    ai_msg = llm_chain.invoke(input_, config=config)
    tool_msgs = it_support_tool.batch(ai_msg.tool_calls, config=config)
    
    # Extract and preserve all links from tool messages
    all_links = []
    for msg in tool_msgs:
        if hasattr(msg, 'content'):
            content = msg.content
            if isinstance(content, str):
                # Look for URLs in the content
                import re
                urls = re.findall(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', content)
                all_links.extend(urls)
    
    response = llm_chain.invoke({**input_, "messages": [ai_msg, *tool_msgs]}, config=config)
    
    # Ensure all links are included in the final response
    final_response = response.content if hasattr(response, 'content') else str(response)
    for link in all_links:
        if link not in final_response:
            final_response += f"\n\nSource: {link}"
    
    return final_response

@tool
def it_support_agent(question: str):
    """
    Tool for handling:
    1. Technical troubleshooting for laptops, phones, and electronics
    2. Device cleaning and maintenance
    3. Electronics care and sanitization
    4. Technical guidance and best practices
    
    Returns original content with all source links preserved.
    """
    response = it_support_logic.invoke(question)
    # Ensure the response ends with the phone numbers
    if not response.endswith("18006601"):
        response += "\n\nNếu bạn cần hỗ trợ thêm, vui lòng liên hệ với nhân viên IT qua số: 18006601"
    return response
