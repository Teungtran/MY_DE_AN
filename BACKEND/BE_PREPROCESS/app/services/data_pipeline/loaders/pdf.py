import os
import asyncio
import tempfile
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.schema import Document 
import logging
from fastapi import UploadFile
logger = logging.getLogger(__name__)

class FPTPDFLoader:
    """
    A class for loading PDF files using LangChain's PyMuPDFLoader with async support.
    """


    def __init__(self, extract_images=False):
        """
        Initialize the FPTPDFLoader.
        
        Args:
            extract_images (bool): Whether to extract images from PDFs. 
                                  Requires Pillow to be installed.
        """
        self.loader = None
        self.documents = None
        self.extract_images = extract_images

    async def get_converted_document(self, pdf: UploadFile) -> List[Document]:
        """
        Load a PDF file asynchronously and return the document objects.

        Args:
            pdf (UploadFile): FastAPI UploadFile object containing the PDF.

        Returns:
            List[Document]: List of Document objects, one per page.
        """


        try:
            # Create a temporary file to store the uploaded PDF
            with tempfile.NamedTemporaryFile(delete=False, suffix=".pdf") as tmp_file:
                # Read the content from the uploaded file
                content = await pdf.read()
                # Write it to the temporary file
                tmp_file.write(content)
                tmp_file_path = tmp_file.name
            
            # Reset the file pointer for future use
            await pdf.seek(0)
            
            # Process the PDF from the temporary file
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(None, self._load_pdf_executor, tmp_file_path)
            
            # Clean up the temporary file
            os.unlink(tmp_file_path)
            
            self.documents = documents

            logger.info(f"Number of pages/documents: {len(self.documents)}")

            return self.documents
        except Exception as e:
            logger.error(f"Error loading PDF asynchronously: {e}")
            return []

    def _load_pdf_executor(self, pdf_path: str) -> List[Document]:
        """Helper method for async PDF loading."""
        try:
            # Try with image extraction if requested
            if self.extract_images:
                self.loader = PyMuPDFLoader(
                    file_path=pdf_path,
                    pages_delimiter="\n",
                    mode="single",
                    extract_images=True,
                    extract_tables="markdown"
                )
                return self.loader.load()
        except ImportError as e:
            logger.warning(f"Image extraction disabled due to missing dependencies: {e}")
            # Fall back to no image extraction
        
        # Use safe options without image extraction
        self.loader = PyMuPDFLoader(
            file_path=pdf_path,
            pages_delimiter="\n",
            mode="single",
            extract_images=False,
            extract_tables="markdown"
        )
        return self.loader.load()
