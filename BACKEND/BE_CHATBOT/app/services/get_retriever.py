from langchain.retrievers import EnsembleRetriever

def get_device_retriever(faiss_store):
    mmr_retriever = faiss_store.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 3, "fetch_k": 5, "lambda_mult": 0.7}
    )
    similarity_retriever = faiss_store.as_retriever(
        search_type="similarity",
        search_kwargs={"k": 3}
    )
    ensemble = EnsembleRetriever(retrievers=[similarity_retriever, mmr_retriever], weights=[0.4, 0.6])
    return ensemble