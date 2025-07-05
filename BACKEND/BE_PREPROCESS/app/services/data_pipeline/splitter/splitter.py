from typing import Dict, List, Optional, Sequence, Type, Union

from langchain.schema import Document
from langchain.text_splitter import (
    CharacterTextSplitter,
    MarkdownTextSplitter,
    RecursiveCharacterTextSplitter,
    TextSplitter,
)
from langchain_core.embeddings import Embeddings
from langchain_experimental.text_splitter import SemanticChunker

from .custom_splitter import TableSplitter


class DocumentSplitter:
    """
    A utility class for splitting documents into smaller chunks using different text splitting strategies.

    Supported splitters:
    - "markdown" (MarkdownTextSplitter)
    - "text" (CharacterTextSplitter)
    - "recursive" (RecursiveCharacterTextSplitter)
    - "semantic" (SemanticChunker, requires an embedding model)
    """

    def __init__(
        self,
        chunk_size: int = 512,
        chunk_overlap: int = 100,
        splitter: str = "table",
        embedding_model: Optional[Embeddings] = None,
    ):
        """
        Initializes the DocumentSplitter with the specified chunking strategy.

        :param chunk_size: The maximum size of each chunk.
        :param chunk_overlap: The number of overlapping characters between consecutive chunks.
        :param splitter: The type of splitter to use. Options: ["markdown", "text", "recursive", "semantic"].
        :param embedding_model: (Optional) Required only if using "semantic" splitter.
        :raises ValueError: If an invalid splitter type is provided.
        """

        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Define available splitters
        splitters: Dict[
            str,
            Type[Union[MarkdownTextSplitter, CharacterTextSplitter, RecursiveCharacterTextSplitter, TableSplitter]],
        ] = {
            "markdown": MarkdownTextSplitter,
            "text": CharacterTextSplitter,
            "recursive": RecursiveCharacterTextSplitter,
            "table": TableSplitter,
        }

        # Validate splitter type
        text_splitter: Union[TextSplitter, SemanticChunker, None] = None
        if splitter == "semantic":
            if not embedding_model:
                raise ValueError("SemanticChunker requires a valid embedding model.")
            text_splitter = SemanticChunker(embedding_model)
        elif splitter in splitters:
            text_splitter = splitters[splitter].from_tiktoken_encoder(
                chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap
            )
        if text_splitter is None:
            raise ValueError(
                f"Invalid splitter type: '{splitter}'. Choose from {list(splitters.keys()) + ['semantic']}."
            )
        self.text_splitter = text_splitter

    async def split_documents(self, docs_list: List[Document]) -> Sequence[Document]:
        """
        Splits a list of documents into smaller chunks using the chosen text splitter.

        :param docs_list: A list of Document objects to be split.
        :return: A list of split Document objects.
        :raises RuntimeError: If the text splitter is not initialized properly.
        """
        if not self.text_splitter:
            raise RuntimeError("Text splitter is not initialized. Ensure a valid splitter type was provided.")

        return await self.text_splitter.atransform_documents(docs_list)
