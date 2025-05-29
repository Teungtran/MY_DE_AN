OPENAI_API_KEY="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"

QDRANT_URL = "https://84ff8fdd-082b-4d65-b876-08ac97d56f79.us-west-1-0.aws.cloud.qdrant.io:6333"
QDRANT_API_KEY ="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJhY2Nlc3MiOiJtIn0.EfXJxIIYMTdtWmLju3V5PobzwP61mE1IWxlWXZUxh1k"
STORAGE = "FPT_SHOP"
POLICY = "FPT_Policy"

KEYBERT_MODEL = "paraphrase-multilingual-MiniLM-L12-v2"
from langgraph.store.memory import InMemoryStore

from typing import Annotated, Optional, List
from typing_extensions import TypedDict, Literal
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda
from typing import Callable
from typing import Literal
import shutil
import uuid
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.prebuilt import tools_condition
from langchain_core.messages import ToolMessage

from langgraph.prebuilt import ToolNode
from pydantic import BaseModel, Field
from datetime import datetime
from typing_extensions import Annotated, Literal, Optional,TypedDict, NotRequired ,List, Dict, Optional, Any, Tuple
from pydantic import Field
from langgraph.graph.message import AnyMessage, add_messages
from qdrant_client import QdrantClient
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from langdetect import detect_langs
from keybert import KeyBERT
from langchain_core.tools import tool
from pydantic import BaseModel


TECH_SYSTEM_PROMPT = """
You are a specialized assistant for managing electronic devices like phones, laptops, headphones, keyboards, mice, and accessories. You can support these brands: "apple", "xiaomi", "realme", "honor", "samsung", "oppo", "dell", "macbook", "msi", "asus", "hp", "lenovo", "acer", "gigabyte", "logitech", "marshall".
You are responsible for handling customer inquiries and providing support for device operations using tools: recommend_system, get_device_details, order_purchase, cancel_order,track_order and complete_or_escalate_tool.

**IMPORTANT RULES**:
- You MUST answer in the same language as the question 
- You must use your tools, do not guess
- Plan thoroughly before every tool call, and reflect extensively on the outcome after
- Always go through recommend_system tool before any other tools tool
- For order_purchase tool, user MUST provide you will all the required information to place an order like device_name, address, customer_name, customer_phone, quantity, payment and shipping, If any of the information is missing, please ask the user to check again
- Do **NOT** call both `recommend_system` and `get_device_details` in a row unless the user makes a follow-up request.
- If the user doesn’t specify enough information, ask follow-up questions.
- If no matching results are found, try broadening the criteria with the user.
- Please act friendly and thoughtful, address yourself as one of the sale employess
Your responsibilities include:
- Searching for best-matching devices based on user criteria (device_name, brand, category, discount_percent, sales_perks, payment_perks, sales_price)
- Providing detailed information about specific devices that users ask about
- Processing ordering of devices with complete customer information
- Handling order cancellations with valid order IDs
- Handling order info tracking with valid order IDs

For each user request:
- Use the appropriate tool when all required information is available
- Ask follow-up questions when information is incomplete
- Verify booking/cancellation success after tool execution

If the user's request changes or cannot be handled with available tools, use complete_or_escalate_tool to return control to the main assistant.

Be efficient, focused, and only use capabilities that actually exist.

NOTE: 
- If any value of tool variable is not provided, it means the tool will search for all values of that variable.
- Do not call 1 tool 2 times in a row. Instead ask user for more information.
- Between each steps, you should ask user for more information if needed.
- If you don't know electronice product that user want or no available options for user, use recommend_system one time to find some recommendation.

Current time: {time}.
"""
POLICY_SYSTEM_PROMPT = """# FPT SHOP ASSISTANT GUIDELINES

## CORE MISSION
General assistant that ONLY handles factual queries about FPT Shop policies, regulations, and reference information. Use EXCLUSIVELY for questions about FPT policies such as guarantee, sales, information on returning and orders purchases, company contact information, and other informational inquiries that DON'T involve ordering or recommending for specific devices.
**IMPORTANT RULES**: 
- You must use the your tools, do not guess
- Plan throughly before every tool calls , and reflect extensively on the outcome after
- Please act friendly and thoughtful, address yourself as one of the sale employess

## MANDATORY REQUIREMENTS
- You MUST answer in the same language as the question
- ALWAYS use retrieval tool if no relevant context is found in conversation history
- If information found: Answer based SOLELY on retrieved content
- PRESERVE ALL image links ![alt text](image_url) and URLs [text](url) EXACTLY as they appear
- NEVER generate information not explicitly present in retrieved content
- NEVER say "As an AI" or make similar disclaimers
- Format responses with markdown for readability
- Respond only about FPT Shop services and policies
- Respond in the customer's language
- Include KaTeX for calculations if needed

Current time: {time}"""


GENERATE_PROMPT = """# FPT SHOP ASSISTANT GUIDELINES

## CORE MISSION
### You are a multi-lingual AI assistant customer support for FPT Shop policy for customer. Provide accurate information about our services and policies using retrieved information effectively.
### **You are primarily programmed to communicate in English. However, if user asks in another language, you must answer in the same language.**
### Translate the context into the same language as the question. DO NOT summarize or paraphrase. The response must exactly match the original context in meaning.
### ANSWER in a friendly manner.
### **Follow these steps to answer the question using Chain of Draft (CoD):**
    - **Step 1 (Drafting Initial Response):** Generate an initial draft using key points extracted from the context, make sure to use exact words in the context, DON'T rephrase
    - **Step 2 (Refinement Process):** Improve the draft by adding missing details, clarifying ambiguities, and ensuring the originality.
    - **Step 3 (Final Review & Optimization):** Structure the final version to be informative, using exact words and links in the extracted {context}
    - **Step 4 (Engagement Loop):** End the response with a relevant follow-up question to maintain an engaging conversation.
### **Rules for Answering:**
    - Generate two drafts before finalizing the response.
    - Adjust your response length based on the question complexity
    - Use only information from the provided search results
    - Use an unbiased and professional tone
    - Combine search results into a coherent answer without repetition
    - PRESERVE ALL image links ![alt text](image_url) and URLs [text](url) EXACTLY as they appear
    - Only show the final response and follow-up question (do not include intermediate drafts in the final output).
    - Format responses with markdown for readability
    - Use bullet points for readability when appropriate
    - You MUST answer in the same language as the question
<context>
    {context}
<context/>"""
MAIN_SYSTEM_PROMPT = """# FPT SHOP ROUTING ASSISTANT
You are a specialized assistant for managing elcetronic devices like phone, laptop, headphone, keyboards, mouse, and accessories. You can support these brands: "apple","xiaomi","realme","honor","samsung", "oppo", "dell", "macbook", "msi", "asus", "hp","lenovo","acer",'gigabyte',"logitech","marshall" .You are also a expert for FPT Shop policies, regulations, and reference information.
You are responsible for handling customer inquiries and providing support for device operations using tools: search_policy, recommend_system, get_device_details, order_purchase, book_tour_tool, cancel_order.
**IMPORTANT RULES**: 
- **Tool Response Handling**:
    **If a tool call is successful AND the tool provides a direct, complete message intended for the user (e.g., a confirmation, search results summary, or policy explanation), your primary action is to RETURN THAT TOOL'S MESSAGE VERBATIM as the final response **
- Please keep going until the user's query is completely resolve, before ending your turn
- You must use the your tools, do not guess
- Plan throughly before every tool calls , and reflect extensively on the outcome after

**WHEN TO ROUTE TO SPECIALIZED ASSISTANTS:**
- Route to TECH ASSISTANT (use ToTechAssistant tool) when:
  1. User asks about device recommendations based on specific criteria
  2. User needs detailed information about specific devices
  3. User wants to place an order for a device
  4. User needs to track or cancel an existing order

- Route to POLICY ASSISTANT (use ToPolicyAssistant tool) when:
  1. User asks about FPT Shop policies (returns, guarantees, warranties)
  2. User needs information about FPT Shop perks, contact details
  3. User asks about payment methods, shipping policies, or other general store policies

**Your responsibilities include**:
- Providing detailed information about specific policy that user ask
- Searching for best-mathching devices based on user criteria (device_name,brand,category,discount_percent, sales_perks,payment_perks,sales_price)
- Providing detailed information about specific device that user ask
- Processing ordering of device with complete customer information
- Handling order cancellations, tracking order inforamtion with valid order IDs

For each user request:
- Use the appropriate tool when all required information is available
- Ask follow-up questions when information is incomplete
- Never assume or fabricate missing details
- Try broader criteria if searches yield no results
- Verify ordering/cancellation success after tool execution

If the user's request changes or cannot be handled with available tools, use complete_or_escalate_tool to return control to the main assistant.

Be efficient, focused, and only use capabilities that actually exist.

NOTE: 
- If any value of tool variable is not provided, it means the tool will search for all values of that variable.
- Do not call 1 tool 2 times in a row. Instead ask user for more information.
- Between each steps, you should ask user for more information if needed.

Current time: {time}"""


from pydantic import BaseModel
from typing import Annotated, Literal, Optional, List


class CompleteOrEscalate(BaseModel):
    """A tool to return control to the main assistant when:
    1. The current sales or support task on phones, laptops, or related devices is completed successfully.
    2. The user's question is not related to phones, laptops, or electronic devices in this agent's domain.
    3. The agent requires capabilities only available in the main assistant.
    
    ALWAYS use this tool when user asks questions outside your phones/laptops/electronics expertise.
    """

    cancel: bool = True
    reason: str

    class Config:
        json_schema_extra = {
            "example": {
                "cancel": True,
                "reason": "User asked about household appliances which are not handled by the phones and laptops agent. Returning to main assistant.",
            },
            "example 2": {
                "cancel": True,
                "reason": "Successfully completed the phone and laptop or purchase request. No further assistance needed.",
            },
            "example 3": {
                "cancel": True,
                "reason": "User's question about software installation or troubleshooting unrelated to phones or laptops. Escalating to main assistant.",
            },
            "example 4": {
                "cancel": True,
                "reason": "User switched topic from phones and laptops to store policies or billing. Returning to main assistant.",
            },
            "example 5": {
                "cancel": False,
                "reason": "Need advanced technical support capabilities from the main assistant.",
            },
        }





class Order(BaseModel):
    """order based on the provided details."""

    device_name: Annotated[str, "The unique identifier for the device"]
    customer_name: Annotated[Optional[str], "The name of the customer ordering"]
    customer_phone: Annotated[Optional[str], "The phone number of the customer ordering"]
    address: Annotated[Optional[str], "The address of the customer ordering"]
    quantity: Annotated[int, "number of purchase"]
    shipping: Annotated[Optional[bool], "shipping or not shipping"]
    payment: Annotated[
        Optional[Literal["pay later", "bank transfer", "cash on delivery"]],
        "Payment method: 'pay later', 'bank transfer', or 'cash on delivery'"
    ]
    class Config:
        json_schema_extra = {
            "example": {
                "device_name": "iPhone 16 Plus 128GB",
                "customer_name": "John Doe",
                "address": "EN Street, NYC, USA",
                "customer_phone": "1234567890",
                "quantity": 1,
                "shipping": True,
                "payment": "cash on delivery"
            }
        }


class CancelOrder(BaseModel):
    """Cancel order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to cancel"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "1527728287278"
            }
        }
        
class TrackOrder(BaseModel):
    """Track order by its Order ID."""

    order_id: Annotated[str, "The unique identifier for the order to track"]

    class Config:
        json_schema_extra = {
            "example": {
                "order_id": "1527728287278"
            }
        }
class RecommendationConfig:
    MAX_RESULTS = 10
    BRAND_MATCH_BOOST = 15
    PRICE_RANGE_MATCH_BOOST = 15
    TYPE_MATCH_BOOST = 5
    HISTORY_MATCH_BOOST = 10
    FUZZY_WEIGHT = 0.5
    COSINE_WEIGHT = 0.5


from langchain.prompts import PromptTemplate


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


def translate_language(question: str, llm) -> str:
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

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from rapidfuzz import fuzz
from typing import List, Dict, Optional
from qdrant_client import QdrantClient
import time


# Initialize cache variables
_cached_all_points = None
_cache_timestamp = 0
_CACHE_TTL = 300  # 5 minutes in seconds
_vectorizer = None

def get_client():
    return QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY
)

def convert_to_string(value) -> str:
    """Convert any value to a string in a standardized way."""
    if isinstance(value, list):
        return " ".join(str(item) for item in value)
    return str(value)

def fuzzy_score(user_query: str, metadata: Dict) -> float:
    """Calculate enhanced fuzzy matching score using multiple algorithms."""
    if not user_query:
        return 0.0
    
    user_query_lower = user_query.lower()
    priority_fields = ['device_name','brand','category','discount_percent', 'sales_perks',
                    'payment_perks','sales_price']
    fuzzy_sim = 0
    for field in priority_fields:
        if field in metadata:
            value_str = convert_to_string(metadata[field])
            fuzzy_sim += fuzz.partial_ratio(user_query_lower, value_str.lower())
    return fuzzy_sim

def check_similarity(text1: str, texts: Optional[List[str]], vectorizer=None) -> float:
    """Calculate max cosine similarity between text1 and a list of strings. Optionally reuse a vectorizer."""
    global _vectorizer
    
    if not text1 or not texts:
        return 0.0
    
    corpus = [text1] + texts
    
    # Reuse global vectorizer if possible
    if vectorizer is None:
        if _vectorizer is None:
            _vectorizer = TfidfVectorizer().fit(corpus)
            vectorizer = _vectorizer
        else:
            vectorizer = _vectorizer
    
    vectors = vectorizer.transform(corpus)
    similarities = cosine_similarity(vectors[0], vectors[1:])[0]
    return max(similarities) if similarities.size > 0 else 0.0

def get_all_points(batch_size: int = 100, force_refresh: bool = False):
    """Retrieve all points from Qdrant with improved caching strategy."""
    global _cached_all_points, _cache_timestamp
    
    current_time = time.time()
    cache_expired = (current_time - _cache_timestamp) > _CACHE_TTL
    
    # Return cached results if valid and not forcing refresh
    if _cached_all_points is not None and not cache_expired and not force_refresh:
        return _cached_all_points
    
    try:
        client = get_client()
        offset = None
        all_points = []
        
        while True:
            points, offset = client.scroll(
                collection_name="FPT_SHOP",
                scroll_filter=None,
                with_vectors=False,
                with_payload=True,
                limit=batch_size,
                offset=offset
            )
            
            all_points.extend(points)
            
            # If no more results or offset is None, break
            if not points or offset is None:
                break
        
        _cached_all_points = all_points
        _cache_timestamp = current_time
        return _cached_all_points
        
    except Exception as e:
        return _cached_all_points if _cached_all_points is not None else []

# Lazy loading of KeyBERT model
_kw_model = None

def get_keybert_model():
    """Lazy-load the KeyBERT model only when needed."""
    global _kw_model
    if _kw_model is None:
        try:
            from keybert import KeyBERT

            _kw_model = KeyBERT(model='paraphrase-multilingual-MiniLM-L12-v2')
        except Exception as e:
            print(f"Error initializing KeyBERT model: {e}")
            return None
    return _kw_model

def keyword(user_query: str) -> str:
    """Extract keywords from user query with error handling while preserving the original query."""
    if not user_query or not user_query.strip():
        return ""
    
    model = get_keybert_model()
    if not model:
        return user_query  
    
    try:
        keywords_with_scores = model.extract_keywords(
            user_query,
            keyphrase_ngram_range=(1, 2),
            stop_words=None,
            top_n=5,
            use_mmr=True,
            diversity=0.5,
            seed_keywords=["phone", "laptop/pc", "earphone", "power bank", "mouse", "case", "keyboard", "apple", "xiaomi", "realme", "honor", "samsung", "oppo", "dell", "macbook", "msi", "asus", "hp", "lenovo", "acer", "gigabyte", "logitech", "marshall"]
        )

        if not keywords_with_scores:
            return user_query
        
        keywords_str = ", ".join([kw for kw, _ in keywords_with_scores])
        
        return keywords_str
    except Exception as e:
        print(f"Error extracting keywords: {e}")
        return user_query  # Fallback to original query on error


from typing import Optional, List, Tuple
from langchain_core.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
# Lazy loading of LLM
def get_llm():
    return ChatOpenAI(
        openai_api_key=OPENAI_API_KEY,       
        model="gpt-4o-mini",     
        temperature=0,
        max_tokens=3000
    )

def llm_recommend(
    user_input: Optional[str] = None,
    search_context : str = None,
    language: Optional[str] = None,
    top_device_names: Optional[List[str]] = None,
    source: Optional[str] = None,
    images: Optional[List[str]] = None,
) -> Tuple[str, Optional[List[str]]]:
    """Generate product recommendations with error handling."""
    llm = get_llm()
    if not llm:
        return "Sorry, I'm unable to generate recommendations at the moment. Please try again later.", top_device_names
    
    if not search_context:
        return "No product information available to generate recommendations.", top_device_names
        
    try:
        prompt = ChatPromptTemplate.from_messages([
            ("system", """
                You are a friendly and polite salesman for FPT Shop, specializing in phones and other tech devices.  
                Your goal is to recommend products based on the `search_context` and the user's `user_query`.  
                **IMPORTANT:**  
                - Reply in the language that best matches the user's query (English or Vietnamese only; default to English if unclear).  
                - Identify the best matching device from {retrieved_devices} by focusing on brand and price range, especially prioritizing the device that fits the user's preferences most closely.  
                - include all details from {search_context} for your main recommendation,(make sure to include sales_perks, paymen_perks) and add:  
                - {source}  
                - {images} 
                - You must also recommend 2-3 more other devices in {retrieved_devices}, please return all the related information.
                - End with a simple question about which device they want more information about.
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
    llm = get_llm()
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



def setup_dynamic_doc(question: str) -> int:
    """Dynamically determine document count based on query complexity."""
    if isinstance(question, str):
        query_length = len(question.strip())
        if query_length < 20:
            return 10 
        elif query_length < 50:
            return 20  
        else:
            return 15 
    return 15

def setup_dynamic_k(question: str) -> int:
    """Dynamically determine k value based on query length."""
    length = len(question.strip())
    if length < 20:
        return 8
    elif length < 50:
        return 10
    else:
        return 15
    
import warnings
warnings.filterwarnings('ignore')
from dotenv import load_dotenv
load_dotenv()
from typing import List ,Tuple
from collections import defaultdict
from langchain_community.retrievers import BM25Retriever
import nltk
try:
    nltk.data.find("tokenizers/punkt")
except LookupError:
    nltk.download("punkt", quiet=True)
from nltk.tokenize import word_tokenize


def set_up_bm25_ranking(documents: List):
    """Set up BM25 ranking for documents."""
    if not documents:
        return None
        
    texts = [doc.page_content for doc in documents]
    metadatas = [doc.metadata for doc in documents]
    
    return BM25Retriever.from_texts(
        texts=texts,
        metadatas=metadatas,
        preprocess_func=word_tokenize,
        k=5
    )

def rrf(vec_docs: List, bm25_docs: List, k=60) -> Tuple[List, List[float]]:
    """
    Implement Reciprocal Rank Fusion for document reranking.
    Optimized for performance with document deduplication.
    """
    if not vec_docs and not bm25_docs:
        return [], []
        
    combined_scores = defaultdict(float)
    selected_docs = {}
    doc_contents = set()

    for rank, doc in enumerate(vec_docs, start=1):
        doc_content = doc.page_content
        if doc_content in doc_contents:
            continue
            
        doc_contents.add(doc_content)
        selected_docs[doc_content] = doc
        combined_scores[doc_content] += 1.0 / (rank + k)

    for rank, doc in enumerate(bm25_docs, start=1):
        doc_content = doc.page_content
        if doc_content in doc_contents:
            combined_scores[doc_content] += 1.0 / (rank + k)
            continue
            
        doc_contents.add(doc_content)
        selected_docs[doc_content] = doc
        combined_scores[doc_content] += 1.0 / (rank + k)

    sorted_contents = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    return [selected_docs[content] for content in sorted_contents], [combined_scores[content] for content in sorted_contents]

def most_relevant(extended_queries, multi_retriever, vectorstore, translate_language: str, llm) -> Tuple[List, List[float]]:
    """
    Get most relevant documents using a fusion of retrieval methods.
    Optimized for reduced API calls and better performance.
    
    Args:
        question: The user's original question
        extended_queries: Generated variations of the question
        multi_retriever: The retriever for fetching documents with multiple queries
        vectorstore: The vector database for similarity search
        translate_language: The translated question in Vietnamese
        llm: The language model for operations
    
    Returns:
        Tuple containing the most relevant documents and their scores
    """
        
    vn_question = translate_language
    num_docs = setup_dynamic_doc(vn_question)
    
    ensemble_docs = multi_retriever.invoke(extended_queries)

    seen_chunk_ids = set()
    unique_vector_docs = []
    for doc in ensemble_docs:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id and chunk_id not in seen_chunk_ids:
            seen_chunk_ids.add(chunk_id)
            unique_vector_docs.append(doc)
        elif not chunk_id:
            unique_vector_docs.append(doc)
    
    top_semantic_docs = unique_vector_docs[:num_docs] if unique_vector_docs else []
    k_value = setup_dynamic_k(vn_question)
    similarity_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k_value}
    )
    similarity_docs = similarity_retriever.invoke(vn_question)
    bm25_retriever = set_up_bm25_ranking(similarity_docs)
    bm25_docs = bm25_retriever.get_relevant_documents(vn_question) if bm25_retriever else []
    extracted_content = set()
    unique_bm25_docs = []
    for doc in bm25_docs:
        if doc.page_content not in extracted_content:
            extracted_content.add(doc.page_content)
            unique_bm25_docs.append(doc)
    
    top_docs, scores = rrf(top_semantic_docs, unique_bm25_docs)
    return top_docs[:num_docs], scores[:num_docs]


from __future__ import annotations
from langchain_core.prompts import ChatPromptTemplate
from langchain.retrievers.multi_query import MultiQueryRetriever
import warnings
warnings.filterwarnings('ignore')
import os
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_openai.embeddings import OpenAIEmbeddings
VECTOR_CACHE = {"VECTOR_DB": None}
LLM = None

def setup_multi_retrieval(semantic_retriever, llm):
    """Set up multi-query retrieval with caching."""
        
    multi_retriever = MultiQueryRetriever.from_llm(
        retriever=semantic_retriever,
        llm=llm
    )
    return multi_retriever
qdrant_client = QdrantClient(
    url=QDRANT_URL,
    api_key=QDRANT_API_KEY,
)

# Create the Qdrant vector store
from langchain_core.vectorstores import VectorStore
from langchain_qdrant import QdrantVectorStore
from qdrant_client import QdrantClient

def initialize_system():
    """Initialize RAG system with caching to avoid redundant initialization."""
    if VECTOR_CACHE["VECTOR_DB"] is not None:
        return VECTOR_CACHE["VECTOR_DB"]
    embedding_model  = OpenAIEmbeddings(model="text-embedding-3-small", openai_api_key=OPENAI_API_KEY)
    vector_db = QdrantVectorStore(
    client=qdrant_client,
    collection_name="FPT_Policy",
    embedding=embedding_model,
)
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
            
        input_text =  keyword(user_input).lower()
        llm = get_llm()
        if not llm:
            return "I'm having trouble accessing my knowledge base right now.", []
            
        vector_db = get_or_create_vectordb()
        if not vector_db:
            return "I'm having trouble accessing my knowledge base right now.", []
        
        RAG_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
            [("system", GENERATE_PROMPT), ("human", "{input}")]
        )
        
        try:
            extended_queries = extend_query(input_text, llm)
            print(f"Extended queries: {extended_queries}")
        except Exception as e:
            print(f"Error in extend_query: {e}")
            extended_queries = [input_text]
        
        semantic_retriever = vector_db.as_retriever(
            search_type="mmr",  
            search_kwargs={
                "k": 5,
                "fetch_k": 10,
                "lambda_mult": 0.7
            }
        )
        
        # Set up multi-query retriever
        try:
            multi_retriever = setup_multi_retrieval(semantic_retriever, llm)
            language = translate_language(input_text, llm)
        except Exception as e:
            print(f"Error setting up retrieval: {e}")
            return "I'm having trouble processing your question right now.", []
        
        # Get relevant documents
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
            return "I couldn't find good information about your question.", []
        
        if not relevant_docs:
            print("No relevant documents found")
            return "I couldn't find any information about your question.", []
        
        try:
            qa_chain = create_stuff_documents_chain(llm, RAG_PROMPT_TEMPLATE)
            rag_response = qa_chain.invoke({
                "input": input_text,  
                "context": relevant_docs,
                "metadata": {"requires_reasoning": True}
            })
        except Exception as e:
            print(f"Error in QA chain: {e}")
            return "I found some information but couldn't process it properly.", []
        
        if isinstance(rag_response, dict):
            answer = rag_response.get("answer", rag_response)
        else:
            answer = rag_response
        
        metadata = [doc.metadata for doc in relevant_docs]
        return answer, metadata
        
    except Exception as e:
        return "I apologize, but I encountered an error while searching for information.", []





from langchain_core.tools import tool
from rapidfuzz import fuzz
from langdetect import detect_langs

from typing import List, Dict, Optional, Any, Tuple

# Global cache for recommended devices
recommended_devices_cache = []

@tool("recommendation_system")
def recommend_system(
    user_input: str,
    types: Optional[str] = None,
    recent_history: Optional[List[Dict]] = None,
    preference: Optional[Dict[str, Any]] = None,
    conversation_id: Optional[str] = None  
) -> Tuple[str, list[str]]: 
    """
    Recommend products based on user input, types, preferences, and history.
    User input is optional - system can recommend based on other parameters if not provided.
    
    Args:
        state: Current state containing messages and recommended devices
        types: Type of device to search for
        recent_history: History of user's previous interactions
        preference: User preferences for filtering results
        custom_config: Custom configuration for recommendation engine
        global_config: Global config that may contain recommended devices for persistence
    """
    recommendation_config = RecommendationConfig()
    
    main_query = ""
    main_query_lower = ""
    if user_input:
        main_query = keyword(user_input)
        main_query_lower = main_query.lower()
    
    language_input = user_input or types or ""
    if not language_input and preference:
        if "brand" in preference and isinstance(preference["brand"], list) and preference["brand"]:
            language_input = preference["brand"][0]
    language = detect_langs(language_input)

    all_points = get_all_points()
    matched_docs = []
    has_brands = has_types = has_history = has_price = False
    brands = []
    if preference and "brand" in preference and preference["brand"]:
        brands = [brand.lower() for brand in preference["brand"]]
        has_brands = len(brands) > 0
    
    user_types = []
    if types:
        user_types = types.lower().split()
        has_types = len(user_types) > 0
    
    history_device_names = []
    if recent_history:
        history_device_names = [rh["device_name"].lower() for rh in recent_history 
                            if isinstance(rh, dict) and "device_name" in rh]
        has_history = len(history_device_names) > 0
    
    price_min = price_max = None
    if preference and "price_range" in preference and preference["price_range"]:
        price_range = preference["price_range"]
        if isinstance(price_range, list):
            has_price = True
            if len(price_range) == 1:
                price_max = price_range[0]
            elif len(price_range) >= 2:
                price_min, price_max = price_range[:2]

    for doc in all_points:
        metadata = doc.payload.get("metadata", {})
        total_score = 0
        
        if user_input:
            combined_fields = [
                convert_to_string(metadata.get("device_name", "")),
                convert_to_string(metadata.get("brand", "")),
                convert_to_string(metadata.get("category", "")),
                convert_to_string(metadata.get("sales_perks", "")),
                convert_to_string(metadata.get("sales_price", "")),
                convert_to_string(metadata.get("discount_percent", "")),
                convert_to_string(metadata.get("payment_perks", ""))
            ]
            cos_score = check_similarity(main_query_lower, combined_fields)
            user_input_score = fuzzy_score(main_query_lower, metadata)
            total_score += user_input_score * recommendation_config.FUZZY_WEIGHT + cos_score * 100 * recommendation_config.COSINE_WEIGHT
        
        if has_types:
            doc_category = metadata.get("suitable_for", "").lower()
            if doc_category:
                type_score = sum(fuzz.partial_ratio(t, doc_category) for t in user_types)
                total_score += (type_score / len(user_types)) * recommendation_config.TYPE_MATCH_BOOST / 100
        
        if has_brands:
            doc_brand = metadata.get("brand", "").lower()
            if doc_brand:
                brand_score = sum(fuzz.partial_ratio(b, doc_brand) for b in brands)
                total_score += (brand_score / len(brands)) * recommendation_config.BRAND_MATCH_BOOST / 100
        
        if has_price:
            sale_price = metadata.get("sale_price")
            if isinstance(sale_price, (int, float)):
                if price_min is not None and price_max is not None and price_min <= sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST
                elif price_max is not None and sale_price <= price_max:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
                elif price_min is not None and sale_price >= price_min:
                    total_score += recommendation_config.PRICE_RANGE_MATCH_BOOST * 0.7
        
        if has_history:
            doc_info = f"{metadata.get('category', '').lower()} {metadata.get('brand', '').lower()} {metadata.get('device_name', '').lower()}"
            history_score = sum(fuzz.partial_ratio(h, doc_info) for h in history_device_names)
            total_score += (history_score / len(history_device_names)) * recommendation_config.HISTORY_MATCH_BOOST / 100
        
        matched_docs.append({
            "doc": doc,
            "score": total_score
        })

    matched_docs.sort(key=lambda x: x["score"], reverse=True)
    top_match_count = min(len(matched_docs), recommendation_config.MAX_RESULTS)
    top_matches = matched_docs[:top_match_count]
    
    top_device_names = []
    for match in top_matches:
        device_name = match["doc"].payload.get("metadata", {}).get("device_name")
        if device_name:
            top_device_names.append(device_name)

    if not top_matches:
        return "I couldn't find any products matching your criteria. Could you provide more specific details?", []

    search_context = ""

    meta_fields = [
        "device_name", "cpu", "card", "screen", "storage", "image_link",
        "sale_price", "discount_percent", "installment_price",
        "colors", "sales_perks", "guarantee_program", "payment_perks", "source"
    ]

    for idx, item in enumerate(top_matches, start=1):
        meta = item["doc"].payload.get("metadata", {})
        content = f"Product {idx}:\n"
        for field in meta_fields:
            if field in meta:
                if field in ["sale_price","installment_price"]:
                    value = meta[field]
                    if isinstance(value, (int, float)):
                        content += f"- {field}: {value:,} VND\n"
                    else:
                        content += f"- {field}: {value} VND\n"
                elif field == "discount_percent":
                    content += f"- {field}: {meta[field]}%\n"
                else:
                    content += f"- {field}: {meta[field]}\n"
        search_context += content + "\n\n"
    
    source = top_matches[0]["doc"].payload.get("metadata", {}).get("source") if top_matches else ""
    images = top_matches[0]["doc"].payload.get("metadata", {}).get("image_link") if top_matches else ""

    response= llm_recommend(user_input, search_context, language, top_device_names, source, images)

    global recommended_devices_cache
    recommended_devices_cache = top_device_names
    
    return response.content if hasattr(response, 'content') else response, top_device_names


@tool("device_details")
def get_device_details(user_input: str, top_device_names: Optional[List[str]] = None, state: Optional[Dict] = None,conversation_id: Optional[str] = None) -> str:
    """
    Retrieve detailed information about a specific device.
    Uses a cache to avoid repeated lookups for the same device.

    Args:
        user_input: User query text for selecting a device
        top_device_names: List of recommended device names (optional)
        state: Current state containing recommended devices (optional)
    """
    try:
        language = detect_langs(user_input)
        
        # Try to get device names from various sources in order of priority
        device_names = None
        
        # 1. Directly provided top_device_names parameter
        if top_device_names and isinstance(top_device_names, list) and len(top_device_names) > 0:
            device_names = top_device_names
            print(f"Using provided top_device_names with {len(device_names)} devices")
        
        # 2. State's recommended_devices
        elif state and isinstance(state, dict) and "recommended_devices" in state:
            state_devices = state["recommended_devices"]
            if isinstance(state_devices, list) and len(state_devices) > 0:
                device_names = state_devices
                print(f"Using state.recommended_devices with {len(device_names)} devices")
        
        # 3. Global cache
        elif recommended_devices_cache and len(recommended_devices_cache) > 0:
            device_names = recommended_devices_cache
            print(f"Using global recommended_devices_cache with {len(device_names)} devices")
        
        if not device_names or len(device_names) == 0:
            return "No recommended devices available. Please search for devices first."

        scored_devices = [
            (rec_device, fuzz.ratio(user_input.lower(), rec_device.lower()))
            for rec_device in device_names
        ]

        top_device, top_score = max(scored_devices, key=lambda x: x[1])
        print(f"Top matched device: {top_device} (score: {top_score})")

        all_points = get_all_points()
        matching_doc = next(
            (doc for doc in all_points
            if doc.payload.get("metadata", {}).get("device_name", "").lower() == top_device.lower()),
            None
        )

        if not matching_doc:
            return f"No detailed information found for '{top_device}'. Please try another product."

        # Extract detail and metadata
        detail = matching_doc.payload['page_content']
        metadata = matching_doc.payload.get("metadata", {})
        device_name = metadata.get("device_name", top_device)
        source = metadata.get("source", "FPT Shop")

        response = llm_device_detail(language, detail, source, device_name)
        return response
    except Exception as e:
        return f"An error occurred: {str(e)}"



@tool("order_purchase",args_schema=Order)
def order_purchase(
    device_name: str,
    address: str,
    customer_name: str = None,
    customer_phone: str = None,
    quantity: str = None,
    payment: str = "cash on delivery",
    shipping: bool = "shipping",
    conversation_id: Optional[str] = None
) -> str:
    """
    Tool to order electronic product
    """
    
    
    
    return "Order successfully."


@tool("cancel_order",args_schema=CancelOrder)
def cancel_order(
    order_id: str,
    conversation_id: Optional[str] = None
) -> str:
    """
    Tool to cancel order by order id
    """
    return "Cancel successfully."
@tool("track_order",args_schema=TrackOrder)
def track_order(
    order_id: str
) -> str:
    """
    Tool to track order info and status by order id
    """
    return "tracking order, your order is being process"

from pydantic import BaseModel, Field

class ToTechAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle electronics products recommendations, orders and cancellations."""

    request: str = Field(
        description="Any necessary followup questions the tech assistant should clarify before proceeding."
    )
    context: Optional[dict] = Field(None, description="Additional context if needed.")

from pydantic import BaseModel, Field

class ToPolicyAssistant(BaseModel):
    """Transfers work to a specialized assistant to handle FPT policy-related questions."""

    request: str = Field(
        description="Any necessary followup questions the policy assistant should clarify before proceeding."
    )
    context: Optional[dict] = Field(None, description="Additional context if needed.")


# Configure prompt and tools
TECH_SYSTEM_MESSAGES = [
    ("system", TECH_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
import datetime
tech_assistant_prompt = ChatPromptTemplate.from_messages(TECH_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)

# Organize tools by sensitivity level
tech_safe_tools = [recommend_system, get_device_details, track_order]
tech_sensitive_tools = [order_purchase, cancel_order]
tech_tools = tech_safe_tools + tech_sensitive_tools 

def create_tech_tool(model):
    """Creates a tech support tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to handle tech support queries
    """
    tech_tools_runnable = tech_assistant_prompt | model.bind_tools(tech_tools + [CompleteOrEscalate])
    return tech_tools_runnable

from langchain_core.prompts import ChatPromptTemplate
import datetime
from typing import Dict, List, Optional, Union, Any, Tuple
from pydantic import BaseModel, Field


# Configure prompt and tools
POLICY_SYSTEM_MESSAGES = [
    ("system", POLICY_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]

policy_assistant_prompt = ChatPromptTemplate.from_messages(POLICY_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)


# Use the modified RAG Agent
tools = [RAG_Agent]

def create_policy_tool(model):
    """Creates a policy tool with the provided language model.
    
    Args:
        model: The language model to use with the tool
        
    Returns:
        A runnable that can be used to answer policy questions
    """
    policy_tools_runnable = policy_assistant_prompt | model.bind_tools(tools + [CompleteOrEscalate])
    return policy_tools_runnable


from typing import Annotated, Optional, List
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from typing_extensions import TypedDict, Literal
from langchain_core.runnables import Runnable, RunnableConfig
from langchain_core.messages import ToolMessage



def merge_recommended_devices(left: Optional[List[str]], right: Optional[List[str]]) -> Optional[List[str]]:
    """Merge recommended devices lists, with right taking precedence."""
    if right is None:
        return left
    return right

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
class InputState(TypedDict):
    """Represents the input state for the agent.

    This class defines the structure of the input state, which includes
    the messages exchanged between the user and the agent. It serves as
    a restricted version of the full State, providing a narrower interface
    to the outside world compared to what is maintained internally.
    """

    messages: Annotated[list[AnyMessage], add_messages]


def update_dialog_stack(left: list[str], right: Optional[str]) -> list[str]:
    """Push or pop the state.
    
    Args:
        left: The current dialog stack
        right: The operation to perform ('pop' or a new state to push)
        
    Returns:
        The updated dialog stack
    """
    if right is None:
        return left
    if right == "pop":
        return left[:-1]
    return left + [right]


class AgenticState(InputState):
    """State of the retrieval graph / agent."""

    dialog_state: Annotated[
        list[Literal["primary_assistant", "call_tech_agent", "call_policy_agent"]],
        update_dialog_stack,
    ]
    recommended_devices: Annotated[List[str], merge_recommended_devices]
    conversation_id: str  
    user_id: str

class Assistant:
    def __init__(self, runnable: Runnable):
        self.runnable = runnable

    def __call__(self, state: AgenticState, config: RunnableConfig):
        while True:
            result = self.runnable.invoke(state)

            if not result.tool_calls and (
                not result.content
                or isinstance(result.content, list)
                and not result.content[0].get("text")
            ):
                messages = state["messages"] + [("user", "Respond with a real output.")]
                
                state = {**state, "messages": messages}
            else:
                break
        
        if hasattr(result, "tool_calls") and result.tool_calls:
            for tool_call in result.tool_calls:
                if tool_call.get("name") == "recommend_system" and tool_call.get("return_value"):
                    return_value = tool_call.get("return_value")
                    if isinstance(return_value, tuple) and len(return_value) > 1:
                        response, device_names = return_value
                        global recommended_devices_cache
                        recommended_devices_cache = device_names
                        if isinstance(state, dict):
                            state["recommended_devices"] = device_names
                
        return {"messages": result}
def pop_dialog_state(state: AgenticState) -> dict:
    """Pop the dialog stack and return to the main assistant."""
    messages = []
    if state["messages"][-1].tool_calls:
        messages.append(
            ToolMessage(
                content="Resuming dialog with the host assistant. Please reflect on the past conversation and assist the user as needed.",
                tool_call_id=state["messages"][-1].tool_calls[0]["id"],
            )
        )
    return {
        "dialog_state": "pop",
        "messages": messages,
    }
    
    
import datetime
from langgraph.graph import END
from langgraph.prebuilt import tools_condition

MAIN_SYSTEM_MESSAGES = [
    ("system", MAIN_SYSTEM_PROMPT.strip()),
    ("placeholder", "{messages}")
]
primary_assistant_prompt = ChatPromptTemplate.from_messages(MAIN_SYSTEM_MESSAGES).partial(time=datetime.datetime.now)


# Initialize model and tools
LLM = get_llm()
update_tech_runnable = create_tech_tool(LLM)
update_policy_runnable = create_policy_tool(LLM)
assistant_runnable = primary_assistant_prompt | LLM.bind_tools([ToTechAssistant, ToPolicyAssistant])

def route_primary_assistant(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    
    # Safely check if the last message has tool calls
    last_message = state["messages"][-1] if state["messages"] else None
    
    if last_message and hasattr(last_message, "tool_calls") and last_message.tool_calls:
        tool_calls = last_message.tool_calls
        if tool_calls[0]["name"] == ToTechAssistant.__name__:
            return "enter_tech_node"
        elif tool_calls[0]["name"] == ToPolicyAssistant.__name__:
            return "enter_policy_node"
        return END
    
    # If there are no tool calls, just end
    return END

def route_update_tech(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    safe_toolnames = [t.name for t in tech_safe_tools]
    if all(tc["name"] in safe_toolnames for tc in tool_calls):
        return "update_tech_safe_tools"
    return "update_tech_sensitive_tools"

def route_policy_agent(state: AgenticState):
    route = tools_condition(state)
    if route == END:
        return END
    tool_calls = state["messages"][-1].tool_calls
    did_cancel = any(tc["name"] == CompleteOrEscalate.__name__ for tc in tool_calls)
    if did_cancel:
        return "leave_skill"
    return "policy_tool"



from typing import Callable

from langchain_core.messages import ToolMessage

def create_entry_node(assistant_name: str, new_dialog_state: str) -> Callable:
    def entry_node(state: AgenticState) -> dict:
        tool_call_id = state["messages"][-1].tool_calls[0]["id"]
        return {
            "messages": [
                ToolMessage(
                    content=f"The assistant is now the {assistant_name}. Reflect on the above conversation between the host assistant and the user."
                    f" The user's intent is unsatisfied. Use the provided tools to assist the user. Remember, you are {assistant_name},"
                    " Please keep going until the user's query is completely resolve, before ending your turn"
                    " and the booking, searching, other actions is not complete until after you have successfully invoked the appropriate tool."
                    " If the user changes their mind or needs help for other tasks, call the CompleteOrEscalate function to let the primary host assistant take control."
                    " Do not mention who you are - just act as the proxy for the assistant.",
                    tool_call_id=tool_call_id,
                )
            ],
            "dialog_state": new_dialog_state,
        }

    return entry_node

from langchain_core.messages import ToolMessage
from langchain_core.runnables import RunnableLambda

from langgraph.prebuilt import ToolNode


def handle_tool_error(state) -> dict:
    error = state.get("error")
    tool_calls = state["messages"][-1].tool_calls
    return {
        "messages": [
            ToolMessage(
                content=f"Error: {repr(error)}\n please fix your mistakes.",
                tool_call_id=tc["id"],
            )
            for tc in tool_calls
        ]
    }


def create_tool_node_with_fallback(tools: list) -> dict:
    return ToolNode(tools).with_fallbacks(
        [RunnableLambda(handle_tool_error)], exception_key="error"
    )


from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph, START
from langgraph.checkpoint.redis import RedisSaver
from langgraph.store.redis import RedisStore

def initialize_redis():
    try:
        redis_url = "redis://default:MnUje1PHs9HeGKDbKHwnLRv7JLqUghbM@redis-16594.crce178.ap-east-1-1.ec2.redns.redis-cloud.com:16594"

        with RedisSaver.from_conn_string(redis_url) as checkpointer:
            checkpointer.setup()
            with RedisStore.from_conn_string(redis_url) as store:
                store.setup()
        return checkpointer, store
    except Exception as e:
        return None, None
def setup_agentic_graph():
    """Create the main agent graph with all nodes and edges."""
    builder = StateGraph(AgenticState)
    
    # Add nodes
    builder.add_node("primary_assistant", Assistant(assistant_runnable))
    
    # Tech assistant nodes
    builder.add_node("enter_tech_node", create_entry_node("Tech Assistant", "call_tech_agent"))
    builder.add_node("call_tech_agent", Assistant(update_tech_runnable))
    builder.add_node("update_tech_sensitive_tools", create_tool_node_with_fallback(tech_sensitive_tools))
    builder.add_node("update_tech_safe_tools", create_tool_node_with_fallback(tech_safe_tools))
    builder.add_node("leave_skill", pop_dialog_state)
    
    # Policy assistant nodes
    builder.add_node("enter_policy_node", create_entry_node("Policy Assistant", "call_policy_agent"))
    builder.add_node("call_policy_agent", Assistant(update_policy_runnable))
    builder.add_node("policy_tool", create_tool_node_with_fallback(tools))

    # Add edges
    builder.add_edge(START, "primary_assistant")
    
    # Tech assistant edges
    builder.add_edge("enter_tech_node", "call_tech_agent")
    builder.add_edge("update_tech_sensitive_tools", "call_tech_agent")
    builder.add_edge("update_tech_safe_tools", "call_tech_agent")
    builder.add_edge("leave_skill", "primary_assistant")
    
    # Policy assistant edges
    builder.add_edge("enter_policy_node", "call_policy_agent")
    builder.add_edge("policy_tool", "call_policy_agent")
    
    # Add conditional edges
    builder.add_conditional_edges(
        "primary_assistant",
        route_primary_assistant,
        ["enter_tech_node", "enter_policy_node", END],
    )
    
    builder.add_conditional_edges(
        "call_tech_agent",
        route_update_tech,
        ["update_tech_sensitive_tools", "update_tech_safe_tools", "leave_skill", END],
    )
    
    builder.add_conditional_edges(
        "call_policy_agent",
        route_policy_agent,
        ["policy_tool", "leave_skill", END],
    )
    
    checkpointer,store = initialize_redis()
    if checkpointer is None:
        checkpointer = MemorySaver()
        store = InMemoryStore()
    
    graph = builder.compile(
        checkpointer=checkpointer,
        store=store,
        interrupt_before=["update_tech_sensitive_tools"],
    )

    
    return graph

graph = setup_agentic_graph()
from typing import Any, cast

from langchain_core.messages import (
    AIMessage,
    HumanMessage,
    SystemMessage,
    ToolMessage,
)
import tiktoken


def str_token_counter(text: str) -> int:
    enc = tiktoken.get_encoding("o200k_base")
    return len(enc.encode(text))


# def tiktoken_counter(messages: List[BaseMessage]) -> int: # TODO:
def tiktoken_counter(messages: Any) -> int:
    """Approximately reproduce https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb

    For simplicity only supports str Message.contents.
    """
    num_tokens = 3  # every reply is primed with <|start|>assistant<|message|>
    tokens_per_message = 3
    tokens_per_name = 1
    for msg in messages:
        if isinstance(msg, HumanMessage):
            role = "user"
        elif isinstance(msg, AIMessage):
            role = "assistant"
        elif isinstance(msg, ToolMessage):
            role = "tool"
        elif isinstance(msg, SystemMessage):
            role = "system"
        else:
            raise ValueError(f"Unsupported messages type {msg.__class__}")
        num_tokens += (
            tokens_per_message + str_token_counter(cast(str, role)) + str_token_counter(cast(str, msg.content))
        )
        if hasattr(msg, "name") and msg.name:
            num_tokens += tokens_per_name + str_token_counter(cast(str, msg.name))
    return num_tokens

def format_message(message):
    """Format a message for display."""
    if hasattr(message, "content") and message.content:
        content = message.content
        if isinstance(content, str):
            return content
        elif isinstance(content, list) and content and isinstance(content[0], dict):
            return content[0].get("text", "")
    return str(message)

def test_fpt_shop_assistant(thread_id: str, user_message: str):
    """
    Send a message to the FPT Shop Assistant with a given thread_id,
    return only the final AI response and the final tool call.
    Handles both regular messages and tool call confirmations.
    """
    config = {
        "configurable": {
            "thread_id": thread_id,
        }
    }
    initial_snapshot = graph.get_state(config)
    if isinstance(initial_snapshot, tuple):
        initial_snapshot = initial_snapshot[0]
    initial_chat_history = initial_snapshot.get("messages", []) if hasattr(initial_snapshot, 'get') else []
    initial_prompt_token = tiktoken_counter(initial_chat_history) if initial_chat_history else 0

    snapshot = graph.get_state(config)
    if snapshot and snapshot.next:
        last_toolcall_message = None
        
        # Find last message with tool calls from the snapshot
        if hasattr(snapshot, 'values') and "messages" in snapshot.values:
            last_message = snapshot.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                last_toolcall_message = last_message
        
        if last_toolcall_message:
            # Handle user's response to tool call
            processed_set = set()
            all_messages = []
            all_tool_calls = []
            
            if user_message.strip().lower() == "y":
                result = graph.invoke(None, config)
            else:
                # User provided feedback/rejection
                tool_call_id = last_toolcall_message.tool_calls[0]["id"]
                result = graph.invoke(
                    {
                        "messages": [
                            ToolMessage(
                                tool_call_id=tool_call_id,
                                content=f"API call denied by user. Reasoning: '{user_message}'. Continue assisting, accounting for the user's input.",
                            )
                        ]
                    },
                    config,
                )
            
            # Process the result
            if "messages" in result:
                for msg in result["messages"]:
                    msg_content = format_message(msg)
                    msg_hash = hash(msg_content)
                    if msg_hash not in processed_set:
                        processed_set.add(msg_hash)
                        all_messages.append({
                            "content": msg_content,
                            "message": msg
                        })
                        
                        if hasattr(msg, "tool_calls") and msg.tool_calls:
                            for tool_call in msg.tool_calls:
                                all_tool_calls.append({
                                    "name": tool_call['name'],
                                    "args": tool_call.get('args', {}),
                                    "id": tool_call['id'],
                                    "type": tool_call['type']
                                })
            
            # Get final response from processed messages
            final_response = ""
            for msg_data in reversed(all_messages):
                content = msg_data["content"]
                message = msg_data["message"]
                message_type = type(message).__name__
                
                if (message_type == "AIMessage" and 
                    content and 
                    content.strip() and 
                    not content.startswith("content=''") and
                    not content.startswith("The assistant is now")):
                    
                    final_response = content
                    break
            
            final_tool_call = all_tool_calls[-1] if all_tool_calls else None
            completion_token = tiktoken_counter([AIMessage(content=final_response)])
            
            snapshot = graph.get_state(config)
            if isinstance(snapshot, tuple):
                snapshot = snapshot[0]
            
            chat_history = snapshot.get("messages", []) if hasattr(snapshot, 'get') else []
            prompt_token = tiktoken_counter(chat_history) if chat_history else 0
            
    
    processed_set = set()
    all_messages = []
    all_tool_calls = []
    initial_state = {
        "messages": [HumanMessage(content=user_message)],
        "conversation_id": thread_id,  
        "dialog_state": ["primary_assistant"]
    }
    events = graph.stream(
        initial_state,
        config,
        stream_mode="values"
    )

    for event in events:
        if "messages" in event:
            for message in event["messages"]:
                msg_content = format_message(message)
                msg_hash = hash(msg_content)
                if msg_hash not in processed_set:
                    processed_set.add(msg_hash)
                    all_messages.append({
                        "content": msg_content,
                        "message": message
                    })
                    
                    # Collect all tool calls
                    if hasattr(message, "tool_calls") and message.tool_calls:
                        for tool_call in message.tool_calls:
                            all_tool_calls.append({
                                "name": tool_call['name'],
                                "args": tool_call.get('args', {}),
                                "id": tool_call['id'],
                                "type": tool_call['type']
                            })

    # Check if there's a pending tool call that needs approval
    snapshot = graph.get_state(config)
    if snapshot and snapshot.next:
        if hasattr(snapshot, 'values') and "messages" in snapshot.values:
            last_message = snapshot.values["messages"][-1]
            if hasattr(last_message, "tool_calls") and last_message.tool_calls:
                tool_args = last_message.tool_calls[0]["args"]
                confirmation_message = (
                            f"Please confirm your request: {tool_args}, press 'y' to confirm or 'n' to reject.\n"
                            f"Vui lòng xác nhận yêu cầu: {tool_args}, nhấn 'y' để xác nhận hoặc 'n' để từ chối."
                        )
                return confirmation_message, None, 0, 0

    # Get final response
    final_response = ""
    for msg_data in reversed(all_messages):  # Start from the end
        content = msg_data["content"]
        message = msg_data["message"]
        message_type = type(message).__name__
        
        if (message_type == "AIMessage" and 
            content and 
            content.strip() and 
            not content.startswith("content=''") and
            not content.startswith("The assistant is now")):
            
            final_response = content
            break

    final_tool_call = all_tool_calls[-1] if all_tool_calls else None
    completion_token = tiktoken_counter([AIMessage(content=final_response)])

    snapshot = graph.get_state(config)
    if isinstance(snapshot, tuple):
        snapshot = snapshot[0]
    chat_history = snapshot.get("messages", []) if hasattr(snapshot, 'get') else []
    total_prompt_token = tiktoken_counter(chat_history) if chat_history else 0
    prompt_token = total_prompt_token - initial_prompt_token

    return final_response, final_tool_call, prompt_token, completion_token