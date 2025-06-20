from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
import warnings
warnings.filterwarnings('ignore')
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI
from typing_extensions import Optional
from qdrant_client import QdrantClient
from .evaluate import evaluate_rag_interaction

from langchain.chains.combine_documents import create_stuff_documents_chain
from config.base_config import APP_CONFIG
from factories.vector_store_factory import create_policy_store
from factories.embedding_factory import create_embedding_model
from .llm import extend_query,translate_language,llm_history
from .reranking import  most_relevant
from factories.chat_factory import create_chat_model
from services.dynamodb import DynamoHistory
from ..prompts import GENERATE_PROMPT
chat_config = APP_CONFIG.chat_model_config
import os
if not chat_config:
    llm = ChatOpenAI(
        openai_api_key=os.getenv("OPENAI_API_KEY"),   
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )
else:
    llm = create_chat_model(chat_config)
VECTOR_CACHE = {"VECTOR_DB": None}
LLM = None
QDRANT_URL = APP_CONFIG.vector_store_config.url
QDRANT_API_KEY = APP_CONFIG.vector_store_config.api_key
COLLECTION = APP_CONFIG.vector_store_config.collection_name
KEYBERT = APP_CONFIG.key_bert_config.model
AWS_SECRET_ACCESS_KEY = APP_CONFIG.dynamo_config.aws_secret_access_key
TABLE_NAME = APP_CONFIG.dynamo_config.table_name
AWS_SECRET_ACCESS_ID = APP_CONFIG.dynamo_config.aws_access_key_id
REGION_NAME = APP_CONFIG.dynamo_config.region_name
def setup_multi_retrieval(semantic_retriever, llm):
    """Set up multi-query retrieval with caching."""
        
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=semantic_retriever,
        llm=llm
    )
    return multi_retriever


qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY.get_secret_value(),
)

def initialize_system():
    """Initialize RAG system with caching to avoid redundant initialization."""
    if VECTOR_CACHE["VECTOR_DB"] is not None:
        return VECTOR_CACHE["VECTOR_DB"]
    embedding = create_embedding_model(APP_CONFIG.embedding_model_config)
    vector_db = create_policy_store(APP_CONFIG, embedding_model=embedding)
    VECTOR_CACHE["VECTOR_DB"] = vector_db
    return vector_db

def get_or_create_vectordb():
    """Get existing vector DB or initialize a new one."""
    if VECTOR_CACHE["VECTOR_DB"] is None:
        VECTOR_CACHE["VECTOR_DB"] = initialize_system()
    return VECTOR_CACHE["VECTOR_DB"]

@tool("rag_agent")
def RAG_Agent(user_input: str = None,conversation_id: Optional[str] = None) -> str:
    """
    Tool to retrieve information about FPT policies and customer support on policy.
    """
    try:
        if not user_input:
            return "I'm sorry, but I need a question to search for information.", []
            
        if not llm:
            return "I'm having trouble accessing my knowledge base right now.", []
            
        vector_db = get_or_create_vectordb()
        if not vector_db:
            return "I'm having trouble accessing my knowledge base right now.", []
        
        RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
            [("system", GENERATE_PROMPT), ("human", "{input}")]
        )
        
        # Get extended queries and translated language in parallel operations
        try:
            extended_queries = extend_query(user_input)
            language = translate_language(user_input)
            print(f"Extended queries: {extended_queries}")
        except Exception as e:
            print(f"Error in query processing: {e}")
            extended_queries = [user_input]
            language = user_input
        
        # Set up retriever once
        semantic_retriever = vector_db.as_retriever(
            search_type="mmr",  
            search_kwargs={
                "k": 5,
                "fetch_k": 10,
                "lambda_mult": 0.7
            }
        )
        
        try:
            multi_retriever = setup_multi_retrieval(semantic_retriever, llm)
        except Exception as e:
            print(f"Error setting up retrieval: {e}")
            return "I'm having trouble processing your question right now.", []
        
        try:
            relevant_docs, scores = most_relevant(
                extended_queries=extended_queries,
                multi_retriever=multi_retriever,
                vectorstore=vector_db,
                translate_language=language,
                llm=llm
            )
            print(f"Found {len(relevant_docs)} relevant documents")
        except Exception as e:
            print(f"Error in document retrieval: {e}")
            return "I couldn't find good information about your question.", []
        
        if not relevant_docs:
            print("No relevant documents found")
            return "I couldn't find any information about your question.", []
        
        try:
            qa_chain = create_stuff_documents_chain(llm, RAG_PROMPT_TEMPLATE)
            rag_response = qa_chain.invoke({
                "input": user_input,  
                "context": relevant_docs,
                "metadata": {"requires_reasoning": True}
            })
        except Exception as e:
            print(f"Error in QA chain: {e}")
            return "I found some information but couldn't process it properly.", []
        
        # Extract answer from response
        if isinstance(rag_response, dict):
            answer = rag_response.get("answer", rag_response)
        else:
            answer = rag_response
        
        return answer
        
    except Exception as e:
        print(f"General error in RAG_Agent: {e}")
        return "I apologize, but I encountered an error while searching for information.", []


@tool
def recall_memory(user_id: str, conversation_id: str) -> str:
    """
    Retrieve the top 5 most recent messages for a given user and conversation.

    Args:
        user_id (str): The ID of the user whose conversation history is being retrieved.
        conversation_id (str): The ID of the conversation to retrieve history for.

    Returns:
        str: A newline-separated string of the 5 most recent messages.
    """
    manager = DynamoHistory(
        aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
        aws_access_key_id=AWS_SECRET_ACCESS_ID,
        table_name=TABLE_NAME,
        region_name=REGION_NAME,
    )

    top_5_recent = manager.get_conversation_history(conversation_id, user_id, 5)

    messages_only = [msg.get("message", "") for msg in top_5_recent]
    format = "\n".join(messages_only)
    answer = llm_history(format)
    return answer
