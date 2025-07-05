from datetime import datetime
import time
import os
import tempfile
from typing import List, Optional, cast, Dict, Any

from langchain.schema import Document
from fastapi import UploadFile

from config.base_config import APP_CONFIG, BaseConfiguration
from schemas.document_metadata import DocumentMetadata
from services.data_pipeline.embeddings import create_embedding_model
from services.data_pipeline.loaders.pdf import FPTPDFLoader

from services.data_pipeline.splitter import DocumentSplitter
from services.data_pipeline.vector_store import create_policy_store
from services.storage.s3 import AsyncS3Client, S3Input, get_s3_client
from utils.logger.logger import get_logger

logger = get_logger(__name__)


class PDFRAGPreprocessingPipeline:
    def __init__(self, config: BaseConfiguration = APP_CONFIG):
        self.config = config
        self.bucket_name = self.config.s3config.bucket_name
        self.embedding_model = create_embedding_model(config.embedding_model_config)
        self.vector_store = create_policy_store(configuration=config, embedding_model=self.embedding_model)
        self.loader = FPTPDFLoader(extract_images=False)
        self.text_splitter = DocumentSplitter(
            chunk_size=self.config.chunking_method_config.chunk_size,
            chunk_overlap=self.config.chunking_method_config.chunk_overlap,
            splitter=self.config.chunking_method_config.chunking_method,
        )
        self.s3_client = None

    async def _get_document(self, pdf_file: UploadFile, metadata: Optional[DocumentMetadata] = None, **kwargs) -> List[Document]:
        """
        Process a single PDF file and return a list of Document objects (one per page).
        
        Args:
            pdf_file (UploadFile): The uploaded PDF file.
            metadata (DocumentMetadata, optional): Metadata for the document.
            
        Returns:
            List[Document]: List of Document objects with metadata.
        """
        document_metadata = {
            "source": metadata.source if metadata and metadata.source else pdf_file.filename,
            "type": metadata.type if metadata and metadata.type else "RAG",
            "description": metadata.description if metadata and metadata.description else "PDF",
            "update_at": (
                metadata.update_at.isoformat() if metadata and metadata.update_at else datetime.now().isoformat()
            ),
        }

        # Use the PDF loader to get documents
        documents = await self.loader.get_converted_document(pdf_file)
        
        # Add metadata to each document
        for doc in documents:
            doc.metadata.update(document_metadata)
            
        return documents

    async def _get_documents(
        self, pdf_files: List[UploadFile], metadatas: Optional[List[DocumentMetadata]] = None, **kwargs
    ) -> List[Document]:
        """
        Process multiple PDF files and return a list of Document objects.
        
        Args:
            pdf_files (List[UploadFile]): List of uploaded PDF files.
            metadatas (List[DocumentMetadata], optional): List of metadata for each file.
            
        Returns:
            List[Document]: Combined list of Document objects from all PDFs.
        """
        all_documents = []
        for idx, pdf_file in enumerate(pdf_files):
            metadata = metadatas[idx] if metadatas and idx < len(metadatas) else None
            docs = await self._get_document(pdf_file, metadata, **kwargs)
            if docs:
                all_documents.extend(docs)
        return all_documents

    async def upload_to_s3(self, file: UploadFile, metadata: Dict[str, Any], s3_client: AsyncS3Client) -> str:
        """
        Upload a file to S3 and return the S3 key
        
        Args:
            file (UploadFile): The file to upload
            metadata (Dict[str, Any]): Metadata to attach to the S3 object
            s3_client (AsyncS3Client): S3 client to use for upload
            
        Returns:
            str: The S3 key of the uploaded file
        """
        try:
            # Reset file pointer to beginning
            await file.seek(0)
            
            # Read file content
            content = await file.read()
            
            # Create a temporary file to store the content
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Reset file pointer for further processing
            await file.seek(0)
            
            # Save to S3 with original filename
            s3_key = f"knowledge_store/rag_pdf/{file.filename}"
            
            await s3_client.put_object(
                S3Input(bucket_name=self.bucket_name, object_name=s3_key, file_path=tmp_file_path),
                extra_args={"Metadata": metadata},
            )
            
            logger.info(f"Original PDF saved to S3: {s3_key}")
            
            # Clean up temporary file
            os.remove(tmp_file_path)
            
            return s3_key
        except Exception as e:
            logger.error(f"Error saving file to S3: {e}")
            raise

    async def _run(
        self,
        pdf_files: List[UploadFile],
        metadatas: Optional[List[DocumentMetadata]] = None,
        preloaded_documents: Optional[List[Document]] = None,
        s3_client: Optional[AsyncS3Client] = None,
        **kwargs,
    ):
        """
        Pipeline to preprocess PDF files and store their embeddings in a vector database.

        Can use preloaded documents if provided, otherwise fetches documents from PDF files.

        Args:
            pdf_files (List[UploadFile]): List of PDF files to process.
            metadatas (List[DocumentMetadata], optional): List of metadata dictionaries corresponding to each file.
            preloaded_documents (List[Document], optional): Pre-fetched documents to use instead of loading from files.
            s3_client (AsyncS3Client, optional): S3 client to use for uploading files.
        """
        logger.info("Starting PDF processing pipeline...")
        _start_time = time.time()

        # Get S3 client if not provided
        if s3_client is None:
            s3_client = await get_s3_client()

        # First, upload the original PDF files to S3
        if pdf_files and not preloaded_documents:
            logger.info("Uploading original PDF files to S3")
            for idx, file in enumerate(pdf_files):
                try:
                    # Prepare metadata for S3
                    s3_metadata = {
                        "source": file.filename,
                        "description": metadatas[idx].description if metadatas and idx < len(metadatas) else "PDF",
                        "type": metadatas[idx].type if metadatas and idx < len(metadatas) else "RAG",
                        "processed_date": datetime.now().isoformat()
                    }
                    
                    # Upload file to S3
                    await self.upload_to_s3(file, s3_metadata, s3_client)
                    
                except Exception as e:
                    logger.error(f"Error uploading original PDF to S3: {e}")
                    # Continue with processing even if original file upload fails

        # Step 1 & 2: Use preloaded documents or convert files to Document objects
        if preloaded_documents:
            documents = preloaded_documents
            logger.info("Using preloaded documents")
        else:
            documents = await self._get_documents(pdf_files, metadatas, **kwargs)

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
        
        return chunks


