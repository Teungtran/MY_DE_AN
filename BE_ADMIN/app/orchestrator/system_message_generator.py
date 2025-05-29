from datetime import datetime
from functools import partial
from typing import Callable, Optional, cast

from langchain_core.messages import SystemMessage
from langchain_core.prompts import PipelinePromptTemplate, PromptTemplate
import pytz

from schemas.template import Template
from schemas.user import UserProfile


# Function to get the current date, time, and weekday in Vietnam
def get_vietnam_time():
    # Define the Vietnam timezone
    viet_nam_tz = pytz.timezone("Asia/Ho_Chi_Minh")

    # Get the current time in Vietnam timezone
    viet_nam_time = datetime.now(viet_nam_tz)

    # Format the date, time, and weekday into a single string
    formatted_time = viet_nam_time.strftime("%Y-%m-%d %H:%M:%S") + " (" + viet_nam_time.strftime("%A") + ")"

    # Return the combined string
    return formatted_time


class SystemMessageGeneratorConfig:
    def __init__(
        self,
        max_tokens: int,
        user: UserProfile,
        templates: Template,
        user_system_message: Optional[str] = None,
    ):
        self.max_tokens = max_tokens
        self.user = user
        self.templates = templates
        self.user_system_message = user_system_message
        self.current_time = get_vietnam_time()


# SystemMessageGenerator
class SystemMessageGenerator:
    def __init__(self, config: SystemMessageGeneratorConfig):
        self.config = config
        self.base_instructions_prompt = PromptTemplate.from_template(self.config.templates.base_instructions)
        self.user_info_prompt = PromptTemplate.from_template(self.config.templates.user_info)
        self.current_time_prompt = PromptTemplate.from_template(self.config.templates.current_time)
        self.conversation_summary_prompt = PromptTemplate.from_template(
            cast(str, self.config.templates.conversation_summary)
        )
        self.formatting_instructions_prompt = PromptTemplate.from_template(
            self.config.templates.formatting_instructions
        )
        self.final_prompt = PromptTemplate.from_template(self.config.templates.combined_template)

        self.combined_template = PipelinePromptTemplate(  # TODO: Depricated package
            input_variables=[  # TODO: append when compare to old project
                "base_instructions",
                "user_info",
                "current_time",
                "conversation_summary",
                "formatting_instructions",
            ],
            final_prompt=self.final_prompt,
            pipeline_prompts=[
                ("base_instructions", self.base_instructions_prompt),
                ("user_info", self.user_info_prompt),
                ("current_time", self.current_time_prompt),
                ("conversation_summary", self.conversation_summary_prompt),
                ("formatting_instructions", self.formatting_instructions_prompt),
            ],
        )
        # print(self.current_time_prompt)
        # print(self.user_info_prompt)
        # print(self.combined_template)

    def generate_system_message(self, summary: str) -> SystemMessage:
        formatted_message = self.combined_template.format(
            max_tokens=self.config.max_tokens,
            user_name=self.config.user.username,  # Access username directly
            user_country=self.config.user.country,  # Access country directly
            current_time=self.config.current_time,
            summary=summary,
            user_system_message=self.config.user_system_message,
        )
        return SystemMessage(content=formatted_message)

    def create_system_message_with_summary(self) -> Callable[[str], SystemMessage]:
        return partial(self.generate_system_message)
