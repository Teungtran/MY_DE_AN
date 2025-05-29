"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import field
from typing import Optional

from config.base_config import BaseConfiguration

from . import prompts


class RAGConfiguration(BaseConfiguration):
    """The configuration for the agent."""

    system_prompt: Optional[str] = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used by the retriever to generate queries based on a step in the research plan."
        },
    )
    
    generate_prompt: Optional[str] = field(
        default=prompts.GENERATE_PROMPT,
        metadata={
            "description": "The prompt used by the generator to generate a response based on the retrieved documents."
        },
    )
