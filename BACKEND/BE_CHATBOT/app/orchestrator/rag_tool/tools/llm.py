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