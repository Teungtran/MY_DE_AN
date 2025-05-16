import os
import asyncio
from typing import List
from langchain_community.document_loaders import PyMuPDFLoader
from langchain.schema import Document 
import logging

logger = logging.getLogger(__name__)

class FPTPDFLoader:
    """
    A class for loading PDF files using LangChain's PyMuPDFLoader with async support.
    """

    DEFAULT_DOWNLOADS_DIR = r"C:\Users\Admin\Downloads"

    def __init__(self):
        """Initialize the FPTPDFLoader."""
        self.loader = None
        self.documents = None
        self.pdf_path = None

    async def get_converted_document(self, pdf_path: str) -> List[Document]:
        """
        Load a PDF file asynchronously and return the document objects.

        Args:
            pdf_path (str): Path to the PDF file.

        Returns:
            List[Document]: List of Document objects, one per page.
        """
        full_path = pdf_path

        # If the given path is just a filename or doesn't exist, look in the default folder
        if not os.path.exists(pdf_path):
            candidate = os.path.join(self.DEFAULT_DOWNLOADS_DIR, os.path.basename(pdf_path))
            if os.path.exists(candidate):
                full_path = candidate
            else:
                logger.error(f"Error: File '{pdf_path}' not found in specified path or default Downloads.")
                return []

        try:
            loop = asyncio.get_event_loop()
            documents = await loop.run_in_executor(None, self._load_pdf_executor, full_path)

            self.documents = documents
            self.pdf_path = full_path

            logger.info(f"PDF loaded successfully (async): {full_path}")
            logger.info(f"Number of pages/documents: {len(self.documents)}")

            return self.documents
        except Exception as e:
            logger.error(f"Error loading PDF asynchronously: {e}")
            return []

    def _load_pdf_executor(self, pdf_path: str) -> List[Document]:
        """Helper method for async PDF loading."""
        self.loader = PyMuPDFLoader(
            file_path=pdf_path,
            pages_delimiter = "\n",
            mode = "single",
            extract_images = True,
            extract_tables = "markdown"
            )
        return self.loader.load()
