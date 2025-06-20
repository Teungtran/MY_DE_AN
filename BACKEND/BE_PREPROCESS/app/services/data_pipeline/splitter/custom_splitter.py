import re
from typing import List, Tuple

from langchain.schema import Document
from langchain.text_splitter import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter


def find_tables(text: str) -> Tuple[List[str], str]:
    """
    Extracts Markdown-style tables from the text.
    Returns a list of tables and the remaining text without tables.
    """
    table_pattern = r"(\|.*\|\n\|[-:| ]+\|[\s\S]*?(?=\n\n|\Z))"
    tables = re.findall(table_pattern, text)
    tables = [table.strip() for table in tables]

    remaining_text = re.sub(table_pattern, "", text).strip()
    return tables, remaining_text


class TableSplitter:
    """
    A custom document splitter that keeps tables intact and ensures headers stay with content.
    Text chunks are sized appropriately while maintaining semantic coherence.
    """

    def __init__(self, chunk_size: int = 2000, chunk_overlap: int = 100):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap

        # Configure the header splitter to keep headers with content
        self.header_splitter = MarkdownHeaderTextSplitter(
            headers_to_split_on=[("#", "Header 1"), ("##", "Header 2"), ("###", "Header 3")],
            strip_headers=False,
            return_each_line=False,
        )

        # Text splitter for further splitting large header sections
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunk_size, chunk_overlap=self.chunk_overlap, separators=["\n\n", "\n", " ", ""]
        )

    @classmethod
    def from_tiktoken_encoder(cls, chunk_size: int, chunk_overlap: int):
        return cls(chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    async def atransform_documents(self, docs_list: List[Document]) -> List[Document]:
        """Core implementation for splitting documents."""
        all_chunks = []

        for doc in docs_list:
            # First extract tables
            tables, remaining_text = find_tables(doc.page_content)
            # Process remaining text with header awareness
            if remaining_text:
                # Split by headers
                header_chunks = self.header_splitter.split_text(remaining_text)
                # Convert to Document objects with appropriate metadata
                header_docs = []
                for chunk in header_chunks:
                    if chunk.page_content.strip():
                        new_doc = Document(page_content=str(chunk), metadata=doc.metadata.copy())
                        header_docs.append(new_doc)
                # Further split large header sections
                for header_doc in header_docs:
                    if len(header_doc.page_content) > self.chunk_size:
                        header_match = re.match(r"^(#{1,6}.*?\n)", header_doc.page_content)
                        header_text = header_match.group(1) if header_match else ""
                        content = (
                            header_doc.page_content[len(header_text) :] if header_text else header_doc.page_content
                        )
                        # Split content
                        if content:
                            content_chunks = self.text_splitter.split_text(content)  # returns List[str]
                            # Add header to each chunk
                            for chunk_text in content_chunks:
                                if chunk_text.strip():
                                    all_chunks.append(
                                        Document(page_content=header_text + chunk_text, metadata=header_doc.metadata)
                                    )
                    else:
                        all_chunks.append(header_doc)

            # Add tables as separate documents (never split them)
            for table in tables:
                all_chunks.append(Document(page_content=table, metadata=doc.metadata))
        return all_chunks
