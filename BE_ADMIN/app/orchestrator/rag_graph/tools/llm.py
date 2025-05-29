from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from config.base_config import APP_CONFIG
from factories.chat_factory import create_chat_model
from typing import Union
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



def extend_query(question: str) -> str:
    """Generate multiple query variations for a question using cached results."""
    QUERY_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an AI language model assistant, understand both Vietnamese and English. You only support answering questions about FPT Shop.
        Your task is to generate four different versions of the given user question to retrieve relevant documents from a vector database.
        Provide these alternative questions separated by newlines.
        Always generate questions that refer back to FPT Shop, all the questions must be related to FPT Shop.
        Original question: {question}"""
    )
    llm_chain = QUERY_PROMPT | llm
    response = llm_chain.invoke({"question": question})
    return response.content if hasattr(response, 'content') else response


def translate_language(question: str) -> str:
    """Translate user question to Vietnamese with caching."""
    LANGUAGE_PROMPT = PromptTemplate(
        input_variables=["question"],
        template="""You are an Vietnamese interpreter, understand many languages.
        Your task is to translate user question in to Vienamese, DO NOT add anything else to the question
        if user's questions are in Vietnamese, just return the question
        Original question: {question}"""
    )
    llm_chain = LANGUAGE_PROMPT | llm
    response = llm_chain.invoke({"question": question})
    return response.content if hasattr(response, 'content') else response


def llm_history(chat_history: Union[str, dict]) -> str:
    """Rephrase the given chat history JSON into a natural language summary or answer."""
    
    if isinstance(chat_history, dict):
        import json
        chat_history = json.dumps(chat_history, indent=2)

    QUERY_PROMPT = PromptTemplate(
        input_variables=["chat_history"],
        template="""
        Please rephrase the following JSON object into a natural language summary or answer:
        
        Chat History:
        {chat_history}
        """
    )
    
    llm_chain = QUERY_PROMPT | llm
    response = llm_chain.invoke({"chat_history": chat_history})
    return response.content if hasattr(response, 'content') else str(response)
