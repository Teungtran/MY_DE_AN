from __future__ import annotations

from functools import partial
from typing import Any, Optional

from langchain_core.callbacks import Callbacks
from langchain_core.prompts import (
    BasePromptTemplate,
    PromptTemplate,
    format_document,
)
from langchain_core.retrievers import BaseRetriever
from langchain_core.tools import StructuredTool
from langchain_core.vectorstores import VectorStore
from pydantic import BaseModel, Field

from config.base_config import BaseConfiguration
from factories.embedding_factory import create_embedding_model
from factories.vector_store_factory import create_vector_store


class RetrieverInput(BaseModel):
    """Input to the retriever."""
    query: str = Field(description="The final question that the user wants to answer does not require the entire conversation history. Extract precise terms from the latest user question and relevant previous ones. The query should include your company name, if applicable, to search your company’s knowledge base and generate an appropriate answer.")


def _get_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
) -> Any:
    docs = retriever.invoke(query, config={"callbacks": callbacks})
    content = document_separator.join(format_document(doc, document_prompt) for doc in docs)
    artifact = [doc.metadata for doc in docs]
    return content, artifact


async def _aget_relevant_documents(
    query: str,
    retriever: BaseRetriever,
    document_prompt: BasePromptTemplate,
    document_separator: str,
    callbacks: Callbacks = None,
) -> Any:
    docs = await retriever.ainvoke(query, config={"callbacks": callbacks})
    content = document_separator.join(format_document(doc, document_prompt) for doc in docs)
    artifact = [doc.metadata for doc in docs]
    return content, artifact


def create_custom_retriever_tool(
    retriever: BaseRetriever,
    name: str,
    description: str,
    *,
    document_prompt: Optional[BasePromptTemplate] = None,
    document_separator: str = "\n\n",
) -> StructuredTool:
    """Create a tool to do retrieval of documents.

    Args:
        retriever: The retriever to use for the retrieval
        name: The name for the tool. This will be passed to the language model,
            so should be unique and somewhat descriptive.
        description: The description for the tool. This will be passed to the language
            model, so should be descriptive.
        document_prompt: The prompt to use for the document. Defaults to None.
        document_separator: The separator to use between documents. Defaults to "\n\n".

    Returns:
        Tool class to pass to an agent.
    """
    document_prompt = document_prompt or PromptTemplate.from_template("{page_content}")
    func = partial(
        _get_relevant_documents,
        retriever=retriever,
        document_prompt=document_prompt,
        document_separator=document_separator,
    )
    afunc = partial(
        _aget_relevant_documents,
        retriever=retriever,
        document_prompt=document_prompt,
        document_separator=document_separator,
    )
    return StructuredTool.from_function(
        name=name,
        description=description,
        func=func,
        coroutine=afunc,
        args_schema=RetrieverInput,
    )


def create_knowledge_retriever(vector_store: VectorStore, config: BaseConfiguration = BaseConfiguration()):
    return vector_store.as_retriever(search_type=config.search_type, search_kwargs=config.search_kwargs)


config = BaseConfiguration()


embedding_model = create_embedding_model(config.embedding_model_config)
vector_store = create_vector_store(configuration=config, embedding_model=embedding_model)


retriever = create_knowledge_retriever(vector_store=vector_store, config=config)


retriever_tool = create_custom_retriever_tool(
    retriever=retriever,
    name="retrieve_information",  # TODO:
    description="Fetch any information about Vietnam Airlines, a national airline of Vietnam.",  # TODO:
)

# content, artifact = retriever_tool.invoke("VNA?")
# print(type(content), type(artifact))
# print(len(artifact))
# for item in artifact:
#     print(item)

# print(content)
