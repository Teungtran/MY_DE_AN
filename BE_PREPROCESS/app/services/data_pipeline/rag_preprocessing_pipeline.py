from datetime import datetime
import time
from typing import List, Optional, cast

from langchain.schema import Document

from config.base_config import APP_CONFIG, BaseConfiguration
from schemas.urls import DocumentMetadata
from services.data_pipeline.embeddings import create_embedding_model
from services.data_pipeline.loaders.urls import FPTCrawler
from services.data_pipeline.loaders.pdf import FPTPDFLoader

from services.data_pipeline.splitter import DocumentSplitter
from services.data_pipeline.vector_store import create_policy_store
from utils.logger import get_logger

logger = get_logger(__name__)


# This will be the main pipeline for the preprocessing service
class RAGPreprocessingPipeline:
    def __init__(self, config: BaseConfiguration = APP_CONFIG,type="url"):
        self.config = config

        self.embedding_model = create_embedding_model(config.embedding_model_config)
        self.vector_store = create_policy_store(configuration=config, embedding_model=self.embedding_model)
        if type == "urls":
            self.loader = FPTCrawler()
        elif type == "pdfs":
            self.loader = FPTPDFLoader()        
        self.text_splitter = DocumentSplitter(
            chunk_size=self.config.chunking_method_config.chunk_size,
            chunk_overlap=self.config.chunking_method_config.chunk_overlap,
            splitter=self.config.chunking_method_config.chunking_method,
        )

    async def _get_document(self, path: str, metadata: Optional[DocumentMetadata] = None, **kwargs) -> Document:
        document_metadata = {
            "source": metadata.source if metadata and metadata.source else "unknown",
            "type": metadata.type if metadata and metadata.type else "unknown",
            "description": metadata.description if metadata and metadata.description else "",
            "update_at": (
                metadata.update_at.isoformat() if metadata and metadata.update_at else datetime.now().isoformat()
            ),
        }

        text = await self.loader.get_converted_document(path)

        if isinstance(text, tuple):
            text = " ".join(str(item) for item in text)

        document = Document(page_content=text, metadata=document_metadata)
        return document

    async def _get_documents(
        self, paths: List[str], metadatas: Optional[List[DocumentMetadata]] = None, **kwargs
    ) -> List[Document]:
        documents = []
        for idx, path in enumerate(paths):
            metadata = metadatas[idx] if metadatas and idx < len(metadatas) else None
            doc = await self._get_document(path, metadata, **kwargs)
            if doc:
                documents.append(doc)
        return documents

    async def _run(
        self,
        paths: List[str],
        metadatas: Optional[List[DocumentMetadata]] = None,
        preloaded_documents: Optional[List[Document]] = None,
        **kwargs,
    ):
        """
        Pipeline to preprocess files and store their embeddings in a vector database.

        Can use preloaded documents if provided, otherwise fetches documents from paths.

        Args:
            paths (List[str]): List of paths to files to process.
            metadatas (List[dict], optional): List of metadata dictionaries corresponding to each file.
            preloaded_documents (List[Document], optional): Pre-fetched documents to use instead of loading from paths.
        """
        logger.info("Starting file processing pipeline...")
        _start_time = time.time()

        # Step 1 & 2: Use preloaded documents or convert files to Document objects
        if preloaded_documents:
            documents = preloaded_documents
            logger.info("Using preloaded documents")
        else:
            documents = await self._get_documents(paths, metadatas, **kwargs)

        if not documents:
            logger.error("No documents were processed.")
            return None

        # Step 3: Split the document into smaller chunks
        try:
            chunks = await self.text_splitter.split_documents(list(documents))
            chunks = cast(list[Document], list(chunks))
        except Exception as e:
            logger.error(f"Error during document splitting: {e}")
            return None

        try:
            await self.vector_store.aadd_documents(chunks)
        except Exception as e:
            logger.error(f"Error storing documents in vector store: {e}")
            return None

        logger.info(f"Stored {len(chunks)} documents in the vector database.")
        logger.info(f"Pipeline completed successfully in {round(time.time()-_start_time, 3)} seconds!")


# import asyncio
# async def main():
#     loader = DocumentPreprocessingPipeline(type="urls")
#     chunks = await loader._run(
#         paths = [
#             "https://www.vietnamairlines.com/vn/vi/travel-information/baggage/restricted-baggage",
#             "https://www.vietnamairlines.com/vn/vi/travel-information/baggage/special-baggage",
#         ]
#     )
#     print(chunks)
# if __name__ == "__main__":
#     asyncio.run(main())
