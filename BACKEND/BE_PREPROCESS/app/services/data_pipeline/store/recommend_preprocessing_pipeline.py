import datetime
from typing import Optional, Tuple, Dict, Any, List
import asyncio
import traceback
import time
from langchain.prompts import ChatPromptTemplate
from langchain.schema import Document
from qdrant_client import QdrantClient
from qdrant_client.models import VectorParams, Distance, Filter, FieldCondition, MatchValue, FilterSelector
from app.config.base_config import APP_CONFIG, BaseConfiguration
from app.utils.logger.logger import get_logger
from app.services.data_pipeline.loaders.urls import FPTCrawler
from app.schemas.urls import FPTData
from app.services.data_pipeline.embeddings import create_embedding_model
from app.services.data_pipeline.chat_model.factory import create_chat_model
from app.services.data_pipeline.vector_store import create_recommend_store
from app.services.guardrails import data_guardrails
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

GUARDRAIL_PROMPT = """
You are an expert at verifying product information extracted from FPT SHOP websites.
Your task is to verify if the input data related to FPT Shop products like laptop, phones and other FPT Shop electronics.
If yes , return "VALID DATA".
If the input data is unrelated to FPT Shop products, OR NOT from FPT SHOP product OR NOT related to electronic return "INVALID DATA".
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
            collection_info = client.get_collection(collection_name)
            existing_fields = set(collection_info.payload_schema.keys()) if collection_info.payload_schema else set()

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
            words = content.split()
            first_100_words = " ".join(words[:50]) + ("..." if len(words) > 100 else "")
            verify_content = data_guardrails(first_100_words, GUARDRAIL_PROMPT)
            if verify_content.get("result") != "VALID DATA":
                logger.error("Guardrail verification failed: INVALID DATA")
                return "Error: Guardrail verification failed - INVALID DATA"
            else:
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
        
        # Check if content is an error message (guardrail failure)
        if isinstance(content, str) and content.startswith("Error:"):
            logger.error(f"Document processing skipped due to error: {content} for URL: {source_url}")
            # Return a special error document that can be tracked
            return Document(
                page_content="",
                metadata={
                    "source": source_url,
                    "error": content,
                    "processing_failed": True
                }
            )
        
        try:
            summary, metadata = await self._process_content(content, source_url)
            return Document(page_content=summary, metadata=metadata)
        except Exception as e:
            logger.error(f"Error processing document {source_url}: {e}")
            return Document(
                page_content="",
                metadata={
                    "source": source_url,
                    "error": str(e),
                    "processing_failed": True
                }
            )
            
    async def _get_documents(self, urls: List[str]) -> List[tuple]:
        """Process multiple tour URLs concurrently."""
        tasks = [self._get_document(url) for url in urls]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        valid_results = []
        for idx, result in enumerate(results):
            if isinstance(result, Exception):
                logger.error(f"Error processing URL {urls[idx]}: {result}")
            elif isinstance(result, str) and result.startswith("Error:"):
                # Guardrail or other validation error - return as tuple with error message
                logger.error(f"Guardrail/validation error for URL {urls[idx]}: {result}")
                valid_results.append((result, urls[idx]))  # Return error as tuple for proper handling
            elif isinstance(result, tuple):
                valid_results.append(result)
            else:
                logger.warning(f"Unexpected result type for URL {urls[idx]}: {type(result)}")
                
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

    def _delete_chunks_by_device_name(self, device_name: str) -> int:
        """
        Delete all chunks from Qdrant vector DB that match the given device_name.
        
        Args:
            device_name: The device name to filter by
            
        Returns:
            Number of points deleted (or 0 if operation failed)
        """
        try:
            if not self.client or not self.collection_name:
                logger.error("Qdrant client or collection not initialized")
                return 0
            
            logger.info(f"Attempting to delete chunks for device_name '{device_name}' from collection '{self.collection_name}'")
            
            # First, check if any points exist with this device_name
            try:
                search_filter = Filter(
                    must=[
                        FieldCondition(
                            key="device_name",
                            match=MatchValue(value=device_name)
                        )
                    ]
                )
                
                # Scroll to count existing points
                scroll_result = self.client.scroll(
                    collection_name=self.collection_name,
                    scroll_filter=search_filter,
                    limit=1,
                    with_payload=True
                )
                
                if scroll_result and scroll_result[0]:
                    logger.info(f"Found existing points for device_name '{device_name}', proceeding with deletion")
                else:
                    logger.warning(f"No existing points found for device_name '{device_name}' - nothing to delete")
                    return 0
                    
            except Exception as search_error:
                logger.warning(f"Could not verify existing points for '{device_name}': {search_error}")
                # Continue with deletion attempt anyway
            
            # Create filter for device_name
            delete_filter = Filter(
                must=[
                    FieldCondition(
                        key="device_name",
                        match=MatchValue(value=device_name)
                    )
                ]
            )
            
            # Delete points matching the filter
            result = self.client.delete(
                collection_name=self.collection_name,
                points_selector=FilterSelector(filter=delete_filter)
            )
            
            logger.info(f"Successfully deleted chunks for device_name '{device_name}' from Qdrant. Result: {result}")
            return 1  # Qdrant doesn't return count, so return 1 to indicate success
            
        except Exception as e:
            logger.error(f"Error deleting chunks for device_name '{device_name}': {e}", exc_info=True)
            return 0

    async def _run(
        self,
        paths: List[str],
        preloaded_documents: Optional[List[Document]] = None,
        device_names_to_replace: Optional[List[str]] = None,
        **kwargs,
    ) -> Optional[List[str]]:
        """
        Main entry point for the tour processing pipeline.

        Process multiple URLs and store their embeddings in the vector database.
        Can use preloaded documents if provided, otherwise fetches documents from URLs.

        Args:
            paths: List of URLs to process.
            preloaded_documents: Optional pre-fetched documents to use instead of loading from URLs.
            device_names_to_replace: If provided, delete existing chunks with these device_names before adding new ones.

        Returns:
            List of status messages for each processed URL or None if the pipeline failed.
        """
        logger.info(f"Starting tour processing pipeline with {len(paths)} URLs...")
        _start_time = time.time()

        if not self.client or not self.collection_name:
            logger.error("Qdrant client or collection not initialized.")
            return None

        # Step 1: Delete existing chunks if device_names_to_replace is provided
        if device_names_to_replace:
            for device_name in device_names_to_replace:
                logger.info(f"Deleting existing chunks for device_name: {device_name}")
                deleted_count = self._delete_chunks_by_device_name(device_name)
                if deleted_count > 0:
                    logger.info(f"Successfully deleted existing chunks for '{device_name}'")
                else:
                    logger.warning(f"No chunks deleted or deletion failed for '{device_name}'")

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

    
