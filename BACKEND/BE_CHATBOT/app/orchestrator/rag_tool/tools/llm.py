from langchain.prompts import PromptTemplate
from langchain_openai import ChatOpenAI
from app.config.base_config import APP_CONFIG
from app.factories.chat_factory import create_chat_model
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

def get_llm():
    """Get the initialized LLM instance."""
    return llm

def extend_query(question: str, llm) -> str:
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