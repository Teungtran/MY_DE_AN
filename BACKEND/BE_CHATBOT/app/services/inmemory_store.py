from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.vectorstores import FAISS
from utils.cleaning import count_words
from config.base_config import APP_CONFIG
from factories.embedding_factory import create_embedding_model
embedding_model = create_embedding_model(APP_CONFIG.embedding_model_config)
def merge_small_chunks(chunks, min_words=150):
    if not chunks:
        return []

    merged_chunks = [chunks[0]]
    
    for chunk in chunks[1:]:
        if count_words(chunk.page_content) < min_words:
            # Merge with previous
            merged_chunks[-1].page_content += " " + chunk.page_content
        else:
            merged_chunks.append(chunk)

    return merged_chunks

def create_temporary_faiss_store(top_matches):
    """
    Always create a completely fresh FAISS store (guaranteed clean)
    """
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=100
    )
    
    page_documents = []

    for item in top_matches:
        try:
            payload = item["doc"].payload
            page_content = payload.get("page_content") or payload.get("metadata", {}).get("page_content")
            if page_content:
                chunks = text_splitter.create_documents([page_content])
                merged_chunks = merge_small_chunks(chunks)
                page_documents.extend(merged_chunks)
        except Exception as e:
            raise e

    if page_documents:
        faiss_store = FAISS.from_documents(page_documents, embedding_model)
        return faiss_store
    else:
        return None