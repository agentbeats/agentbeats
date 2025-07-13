import os
import asyncio
from openai import AsyncOpenAI
from agents import Agent, Model, ModelProvider, OpenAIChatCompletionsModel, RunConfig, Runner
from agents import set_tracing_disabled
set_tracing_disabled(disabled=True)

OPENROUTER_BASE_URL = os.getenv("OPENAI_API_BASE", "https://openrouter.ai/api/v1")
OPENROUTER_API_KEY = os.getenv("OPENAI_API_KEY")
MODEL_NAME = "o4-mini"

custom_client = AsyncOpenAI(base_url=OPENROUTER_BASE_URL, api_key=OPENROUTER_API_KEY)

class CustomModelProvider(ModelProvider):
    def get_model(self, model_name: str | None) -> Model:
        return OpenAIChatCompletionsModel(model=model_name or MODEL_NAME, openai_client=custom_client)

CUSTOM_MODEL_PROVIDER = CustomModelProvider()

async def main():
    agent = Agent(
        name="TestAgent",
        instructions="You are a helpful assistant.",
        model=MODEL_NAME,
        tools=[],
    )
    prompt = "Say 'Hello from OpenRouter!'"
    result = await Runner.run(
        agent,
        prompt,
        run_config=RunConfig(model_provider=CUSTOM_MODEL_PROVIDER)
    )
    print("Result:", result.final_output)

if __name__ == "__main__":
    asyncio.run(main()) 