import os
import asyncio
from pathlib import Path

from dotenv import load_dotenv
from openai import AsyncOpenAI

from ragas.llms import llm_factory
from ragas.metrics.collections import Faithfulness


BASE_DIR = Path(__file__).resolve().parent
load_dotenv(BASE_DIR / ".env")

API_KEY = os.environ["GEMINI_API_KEY"]


# Async Gemini client through Google's
# OpenAI-compatible endpoint
client = AsyncOpenAI(
    api_key=API_KEY,
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/"
)


# Ragas evaluator
llm = llm_factory(
    "gemini-2.0-flash",
    client=client
)


metric = Faithfulness(
    llm=llm
)


async def main():

    print("LLM:", llm)
    print("Metric:", metric)

    result = await metric.ascore(
        user_input="What is the stipend?",
        response="The stipend is Rs 2,00,000 per month.",
        retrieved_contexts=[
            "The Future Founders Fellowship provides "
            "a stipend of Rs 2,00,000 per month."
        ]
    )

    print("\nResult:", result)
    print("Score:", result.value)


if __name__ == "__main__":
    asyncio.run(main())