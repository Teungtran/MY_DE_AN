from typing import Optional, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from config.base_config import APP_CONFIG
from factories.chat_factory import create_chat_model
from langchain_openai import ChatOpenAI
import os
chat_config = APP_CONFIG.chat_model_config

if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)

def llm_recommend(
    user_input: Optional[str] = None,
    search_context : str = None,
    language: Optional[str] = None,
    top_device_names: Optional[List[str]] = None,
    source: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> Tuple[str, Optional[List[str]]]:
    """Generate product recommendations with error handling."""
    if not llm:
        return "Sorry, I'm unable to generate recommendations at the moment. Please try again later.", top_device_names
    
    if not search_context:
        return "No product information available to generate recommendations.", top_device_names
        
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
                - Reply in the language that best matches the user's query (English or Vietnamese only; default to English if unclear).
                - From {retrieved_devices} find best 3 matching devices with {user_query} to recommend.
                - include all details from {search_context} for your recommendation,(make sure to include sales_perks, paymen_perks) and add:  
                - {source}  
                - {images} 
                - Ask user if they want to buy or need for more information.
            """),
            ("human", "User query: {user_query}\n\nSearch results:\n{search_context}")
        ])
        chain = prompt | llm
        response = chain.invoke({
            "user_query": user_input or "",
            "search_context": search_context,
            "retrieved_devices": top_device_names or [],
            "source": source or "",
            "images": images or [],
            "language": language or "en"
        })
        
        return response.content if hasattr(response, 'content') else response
    except Exception as e:
        print(f"Error in llm_recommend: {e}")
        return f"Unable to process recommendation request. Technical error: {str(e)[:100]}"

def llm_device_detail(language: str, detail: str, source: str, device_name: str) -> str:
    """
    Retrieve detailed information about a specific device with error handling.
    """
    if not llm:
        return f"Sorry, I'm unable to provide details for {device_name} at the moment. Please try again later."
    
    if not detail:
        return f"No detailed information available for {device_name}."
    
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
                    You are a product assistant for FPT Shop selling tech devices.
                    Provide concise information about the specific device.
                    Include links and image links if present.
                    Maintain the detected language.
                    End with a reference to {source} for more details.
                """),
            ("human", "device_name: {device_name}\n\nSearch results:\n{detail}\n\nLanguage:\n{language}")
        ])

        chain = prompt | llm
        response = chain.invoke({
            "device_name": device_name,
            "detail": detail,
            "language": language or "en",
            "source": source or ""
        })
        
        result = response.content if hasattr(response, 'content') else response
        return result
    except Exception as e:
        print(f"Error in llm_device_detail: {e}")
        return f"Unable to retrieve details for {device_name}. Technical error: {str(e)[:100]}"