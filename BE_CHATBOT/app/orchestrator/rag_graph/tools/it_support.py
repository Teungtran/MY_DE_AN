import os
from langchain_community.tools import TavilySearchResults
from langchain_community.utilities.tavily_search import TavilySearchAPIWrapper

import datetime
import warnings
warnings.filterwarnings('ignore')
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
    "howtogeek.com",
    "makeuseof.com",
    "ifixit.com/Guide",
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


tavily_search_wrapper = TavilySearchAPIWrapper(
    tavily_api_key=search_config.api_key,
)

it_support_tool = TavilySearchResults(
    max_results=5,
    search_depth="advanced",
    include_images=True,
    include_answer=True,
    include_raw_content=True,
    api_wrapper=tavily_search_wrapper,
    include_domains=trusted_tech_domains
    
)

@tool("it_support_agent")
def it_support_agent(question):
    """
    Tool for handling:
    1. Technical troubleshooting for laptops, phones, and electronics
    2. Device cleaning and maintenance
    3. Electronics care and sanitization
    4. Technical guidance and best practices
    
    Returns original content with all source links preserved.
    """
    search_results = it_support_tool.run(question)

    today = datetime.date.today().strftime("%B %d, %Y")
    prompt = ChatPromptTemplate.from_messages([
        ("system", (
            f"You are an IT support assistant. Today's date is {today}. "
            "You will be given a list of search results. "
            "Your task is to find the most accurate and recent information "
            "to help the user with their technical or maintenance needs.\n\n"
            "Search Results:\n{search_info}\n\n"
            "ALWAYS end with this line:\n"
            "\"To get more help, call 18006601 to contact an IT personnel or 1800.6616 for customer support service.\""
        )),
        ("human", "{user_question}")
    ])

    chain = prompt | llm

    result = chain.invoke({
        "search_info": search_results,
        "user_question": question
    })

    return result.content