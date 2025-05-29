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

    # Process vector documents first
    for rank, doc in enumerate(vec_docs, start=1):
        doc_content = doc.page_content
        if doc_content not in doc_contents:
            doc_contents.add(doc_content)
            selected_docs[doc_content] = doc
            combined_scores[doc_content] = 1.0 / (rank + k)

    # Process BM25 documents and update scores
    for rank, doc in enumerate(bm25_docs, start=1):
        doc_content = doc.page_content
        if doc_content in doc_contents:
            combined_scores[doc_content] += 1.0 / (rank + k)
        else:
            doc_contents.add(doc_content)
            selected_docs[doc_content] = doc
            combined_scores[doc_content] = 1.0 / (rank + k)

    # Sort by combined scores
    sorted_contents = sorted(combined_scores.keys(), key=lambda x: combined_scores[x], reverse=True)
    return [selected_docs[content] for content in sorted_contents], [combined_scores[content] for content in sorted_contents]

def most_relevant(extended_queries, multi_retriever, vectorstore, translate_language: str, llm) -> Tuple[List, List[float]]:
    """
    Get most relevant documents using a fusion of retrieval methods.
    Optimized for reduced API calls and better performance.
    
    Args:
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
    
    # Get ensemble documents from multi-retriever
    ensemble_docs = multi_retriever.invoke(extended_queries)

    # Deduplicate vector docs more efficiently
    seen_chunk_ids = set()
    unique_vector_docs = []
    for doc in ensemble_docs:
        chunk_id = doc.metadata.get("chunk_id")
        if chunk_id:
            if chunk_id not in seen_chunk_ids:
                seen_chunk_ids.add(chunk_id)
                unique_vector_docs.append(doc)
        else:
            unique_vector_docs.append(doc)
    
    top_semantic_docs = unique_vector_docs[:num_docs] if unique_vector_docs else []
    
    # Set up similarity search
    k_value = setup_dynamic_k(vn_question)
    similarity_retriever = vectorstore.as_retriever(
        search_type="similarity",
        search_kwargs={"k": k_value}
    )
    similarity_docs = similarity_retriever.invoke(vn_question)
    
    # Set up BM25 and get documents
    bm25_retriever = set_up_bm25_ranking(similarity_docs)
    bm25_docs = bm25_retriever.get_relevant_documents(vn_question) if bm25_retriever else []
    
    # Deduplicate BM25 docs efficiently
    unique_bm25_docs = []
    seen_content = set()
    for doc in bm25_docs:
        if doc.page_content not in seen_content:
            seen_content.add(doc.page_content)
            unique_bm25_docs.append(doc)
    
    # Apply RRF fusion
    top_docs, scores = rrf(top_semantic_docs, unique_bm25_docs)
    return top_docs[:num_docs], scores[:num_docs]
