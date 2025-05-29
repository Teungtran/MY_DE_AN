"""Define the configurable parameters for the agent."""

from __future__ import annotations

from dataclasses import field

from config.base_config import BaseConfiguration

from . import prompts


class AgenticConfiguration(BaseConfiguration):
    """The configuration for the agent."""

    system_prompt: str = field(
        default=prompts.SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for classifying user questions to route them to the correct node."
        },
    )
