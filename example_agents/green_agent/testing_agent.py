# -*- coding: utf-8 -*-

from openai import OpenAI
import os

class TestingAgent:
    def __init__(self, system_message: str, model: str = "o4-mini") -> None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        self.client = OpenAI(api_key=api_key)
        self.model = model
        self.memory = [
            {"role": "system", "content": system_message}
        ]
    
    def get_response(self, user_query: str) -> str:
        self.memory.append({"role": "user", "content": user_query})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.memory  # type: ignore
        )

        response = completion.choices[0].message.content
        if response is None:
            response = "No response generated"
        self.memory.append({"role": "assistant", "content": response})

        return response


# Example usage:
if __name__ == "__main__":
    # Set a default system message for testing
    system_message = "You are a helpful assistant."
    agent = TestingAgent(system_message=system_message, model="gpt-4o")
    
    user_query = "Can you explain the concept of recursion in programming?"
    solution = agent.get_response(user_query)
    print(solution)