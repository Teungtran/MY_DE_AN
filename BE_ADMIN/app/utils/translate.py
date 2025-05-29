from dotenv import load_dotenv
from langchain_openai import AzureChatOpenAI

from .time_measure import measure_time

load_dotenv()


azure_deployment_name = "gpt-4o-mini-chat-completion"
api_version = "2024-08-01-preview"

llm = AzureChatOpenAI(
    azure_deployment=azure_deployment_name,  # or your deployment
    api_version=api_version,  # or your api version
    temperature=0,
    max_tokens=1200,
    timeout=None,
    max_retries=1,
    # other params...
)


@measure_time
async def translate(sentence: str, lang_code: str):
    messages = [
        (
            "system",
            "You are a language translation model. Your task is to provide only the translated version of the sentence in the specified language. Do not include any additional explanations or details.",
        ),
        ("human", f"translate: {sentence} into {lang_code}."),
    ]

    response = await llm.ainvoke(messages)

    return response.content
