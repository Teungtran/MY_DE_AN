import datetime
from typing import Optional, Tuple, Dict, Any, List
import asyncio
import traceback
import time
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance
from config.base_config import APP_CONFIG, BaseConfiguration
from utils.logger.logger import get_logger
from services.data_pipeline.loaders.urls import FPTCrawler
from schemas.urls import FPTData
from services.data_pipeline.embeddings import create_embedding_model
from services.data_pipeline.chat_model.factory import create_chat_model
from services.data_pipeline.vector_store import create_recommend_store

logger = get_logger(__name__)

# Optimized prompt - more concise while preserving intent
TEXT_SUMMARIZE_PROMPT = """
    Extract key information from the "## Mô tả sản phẩm" section focusing on:
    - Design & Materials
    - Performance (RAM, hardware)
    - Camera features
    - Video capabilities
    - Battery & charging
    - AI features
    - Device comparisons
    Preserve image links with original format.
    Text: {input}
"""

class RecommendProcessingPipeline:
    def __init__(self, config: BaseConfiguration = APP_CONFIG):
        self.config = config
        self.openai_api_key = config.chat_model_config.api_key.get_secret_value()
        self.model = config.chat_model_config.model or "gpt-4o-mini"
        self.qdrant_url = config.recommend_config.url
        self.qdrant_api_key = config.recommend_config.api_key.get_secret_value()
        self.qdrant_collection_name = config.recommend_config.collection_name
        self.fpt_data = FPTCrawler()
        self.embedding_model = create_embedding_model(config.embedding_model_config)

        self.vector_store = create_recommend_store(configuration=config, embedding_model=self.embedding_model)
        self.model = create_chat_model(APP_CONFIG.chat_model_config)
        self.client, self.collection_name = self._connect_and_create_collection()
        if self.client and self.collection_name:
            self._apply_payload_schema(self.client, self.collection_name)
        
    # Store extraction prompt as a class variable to avoid recreating it
    METADATA_PROMPT = ChatPromptTemplate.from_messages([
        (("system", """Extract FPT Shop product data with these rules:
            - Extract sales_perks from "Quà tặng và ưu đãi khác"/"Khuyến mãi được hưởng" 
            - Extract guarantee_program from "Bảo hành mở rộng"
            - Extract payment_perks from "Khuyến mãi thanh toán"
            - Use 'device_name' field to determine 'brand' field'
            - If sale_price < 1000000 VND: suitable_for = 'students', else: 'adults'
            - If sale_price > 20000000: category = 'luxury', else: category = 'office'
            - Keep text exactly as it appears
            - Use empty string if not found""")),
        ("human", "{context}")
    ])

    def _connect_and_create_collection(self):
        """Connect to Qdrant and create collection if it doesn't exist."""
        try:
            client = QdrantClient(url=self.qdrant_url, api_key=self.qdrant_api_key)
            collection_name = self.qdrant_collection_name
            vector_size = 1536  
            
            if not client.collection_exists(collection_name):
                client.create_collection(
                    collection_name=collection_name,
                    vectors_config=VectorParams(size=vector_size, distance=Distance.COSINE)
                )
                logger.info(f"Created collection '{collection_name}'")
            else:
                logger.info(f"Collection '{collection_name}' already exists.")

            return client, collection_name
        except Exception as e:
            logger.error(f"Error connecting to Qdrant: {e}")
            return None, None

    def _apply_payload_schema(self, client, collection_name):
        """Apply the payload schema to the Qdrant collection."""
        payload_schema = {
            "device_name": {"type": "text"},
            "brand": {"type": "keyword"},
            "storage": {"type": "text"},
            "battery": {"type": "text"},
            "colors": {"type": "text"}, 
            "cpu": {"type": "text"},
            "card": {"type": "text"},
            "screen": {"type": "text"},
            "suitable_for": {"type": "text"},
            "category": {"type": "keyword"},
            "sales_perks": {"type": "text"},
            "payment_perks": {"type": "text"},
            "guarantee_program": {"type": "text"},
            "source": {"type": "text"},
            "image_link": {"type": "text"},
            "sale_price": {"type": "integer"},          
            "discount_percent": {"type": "integer"},   
            "installment_price": {"type": "integer"},  
            "bonus_points": {"type": "integer"},        
        }

        try:
            # Get existing indexes to avoid recreating them
            existing_indexes = client.get_collection(collection_name).payload_indexes
            existing_fields = {index.field_name for index in existing_indexes}
            
            for field_name, field_config in payload_schema.items():
                if field_name not in existing_fields:
                    client.create_payload_index(
                        collection_name=collection_name,
                        field_name=field_name,
                        field_schema=field_config
                    )
                    logger.info(f"Index created for field: {field_name}")
        except Exception as e:
            logger.warning(f"Failed to apply payload schema: {e}")

    async def _summarize_content(self, content: str) -> str:
        """Summarize tour content using an AI model."""
        try:
            prompt = ChatPromptTemplate.from_template(TEXT_SUMMARIZE_PROMPT)
            chain = prompt | self.model
            extraction = chain.invoke({"input": content})
            return extraction.content
        except Exception as e:
            logger.error(f"Error during fpt content summarization: {e}")
            raise

    async def _extract_metadata_from_context(self, context: str, source_url: Optional[str] = None) -> dict:
        """Extract structured metadata from tour content using an AI model."""
        try:
            # Using the class-level prompt template
            llm = self.model.with_structured_output(schema=FPTData)
            chain = self.METADATA_PROMPT | llm 
            try:
                result: FPTData = chain.invoke({"context": f"Extract the metadata from the following FPT Shop product page text:\n\n{context}"})
                metadata = result.model_dump(mode='json')
                time_update = datetime.datetime.now().strftime("%Y-%m-%d")
                if source_url:
                    metadata["source"] = source_url
                if time_update:
                    metadata['time_update'] = time_update
                return metadata
            except Exception as e:
                logger.error(f"Error during metadata extraction: {e}")
                raise
        except Exception as e:
            logger.error(f"Error during metadata extraction: {e}")
            raise

    async def _process_content(self, content: str, source_url: Optional[str] = None) -> Tuple[str, Dict[str, Any]]:
        """Process tour content by concurrently running summarization and metadata extraction."""
        try:
            summary_task = asyncio.create_task(self._summarize_content(content))
            metadata_task = asyncio.create_task(self._extract_metadata_from_context(content, source_url))
            
            summary, metadata = await asyncio.gather(summary_task, metadata_task)
            
            return summary, metadata
        except Exception as e:
            logger.error(f"Error processing fpt content: {e}")
            raise

    async def _get_document(self, url: str) -> tuple[str, str] | str:
        """Convert tour URL to markdown content and return content with source URL."""
        try:
            logger.info(f"Starting processing for URL: {url}")

            result = await self.fpt_data.get_converted_document(url)
            if not result:
                logger.error("Error in converting URL to markdown.")
                return "Error in converting URL to markdown."

            content, source_url = result
            logger.info(f"Successfully converted URL to markdown: {source_url}")

            return content, source_url

        except Exception as e:
            logger.error(f"An error occurred while converting URL: {e}")
            traceback.print_exc()
            return f"Error: {str(e)}"

    async def _process_document(self, document_tuple):
        """Process a single document tuple into a Document object."""
        if not isinstance(document_tuple, tuple):
            return None
            
        content, source_url = document_tuple
        try:
            summary, metadata = await self._process_content(content, source_url)
            return Document(page_content=summary, metadata=metadata)
        except Exception as e:
            logger.error(f"Error processing document {source_url}: {e}")
            return None
            
    async def _get_documents(self, urls: List[str]) -> List[tuple]:
        """Process multiple tour URLs concurrently."""
        tasks = [self._get_document(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing URL {urls[idx]}: {result}")
            else:
                valid_results.append(result)
                
        return valid_results

    async def _batch_process_documents(self, raw_tuples, batch_size=None):
        """Process documents in batches for better concurrency."""
        all_documents = []
        
        # Determine batch size based on input length
        if batch_size is None:
            input_length = len(raw_tuples)
            if input_length <= 5:
                batch_size = input_length
            else:
                batch_size = max(5, input_length // 4)
        
        for i in range(0, len(raw_tuples), batch_size):
            batch = raw_tuples[i:i+batch_size]
            tasks = [self._process_document(doc_tuple) for doc_tuple in batch]
            processed_batch = await asyncio.gather(*tasks)
            
            valid_docs = [doc for doc in processed_batch if doc is not None]
            all_documents.extend(valid_docs)
            
            logger.info(f"Processed batch {i//batch_size + 1}/{(len(raw_tuples) + batch_size - 1)//batch_size}, got {len(valid_docs)} valid documents")
            
        return all_documents

    async def _run(
        self,
        paths: List[str],
        preloaded_documents: Optional[List[Document]] = None,
        **kwargs,
    ) -> Optional[List[str]]:
        """
        Main entry point for the tour processing pipeline.

        Process multiple URLs and store their embeddings in the vector database.
        Can use preloaded documents if provided, otherwise fetches documents from URLs.

        Args:
            paths: List of URLs to process.
            preloaded_documents: Optional pre-fetched documents to use instead of loading from URLs.

        Returns:
            List of status messages for each processed URL or None if the pipeline failed.
        """
        logger.info(f"Starting tour processing pipeline with {len(paths)} URLs...")
        _start_time = time.time()

        if not self.client or not self.collection_name:
            logger.error("Qdrant client or collection not initialized.")
            return None

        # Step 2: Use preloaded documents or fetch documents from URLs
        if preloaded_documents:
            documents = preloaded_documents
            logger.info(f"Using {len(documents)} preloaded documents")
        else:
            # Fetch raw document content
            start_fetch = time.time()
            raw_tuples = await self._get_documents(paths)
            logger.info(f"Fetched {len(raw_tuples)} documents in {time.time() - start_fetch:.2f}s")
            
            # Process documents in batches with dynamic batch size based on input length
            start_process = time.time()

            documents = await self._batch_process_documents(raw_tuples, batch_size=None)
            logger.info(f"Processed {len(documents)} documents in {time.time() - start_process:.2f}s")

        if not documents:
            logger.warning("No valid documents to process.")
            return ["No valid documents were processed"]

        try:
            # Store documents in vector database in batch
            start_store = time.time()
            await self.vector_store.aadd_documents(documents)
            logger.info(f"Stored {len(documents)} documents in {time.time() - start_store:.2f}s")
        except Exception as e:
            logger.error(f"Error storing documents in vector store: {e}")
            traceback.print_exc()
            return None

        # Generate result messages
        results = [f"Successfully processed document {i+1}/{len(documents)}" for i in range(len(documents))]

        pipeline_duration = time.time() - _start_time
        logger.info(f"Pipeline completed successfully in {round(pipeline_duration, 3)} seconds!")

        return results

    
