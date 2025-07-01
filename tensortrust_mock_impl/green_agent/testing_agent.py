# -*- coding: utf-8 -*-

from openai import OpenAI
import os

class TestingAgent:
    def __init__(self, system_message: str, model: str = "o4-mini") -> None:
        self.client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        self.model = model
        self.memory = [
            {"role": "system", "content": system_message}
        ]
    
    def get_response(self, user_query: str) -> str:
        self.memory.append({"role": "user", "content": user_query})

        completion = self.client.chat.completions.create(
            model=self.model,
            messages=self.memory
        )

        response = completion.choices[0].message.content
        self.memory.append({"role": "assistant", "content": response})

        return response


# Example usage:
if __name__ == "__main__":
    agent = TestingAgent(model="gpt-4o")
    messages = [
        {"role": "system", "content": "You are a helpful assistant."},
        {"role": "user", "content": "Can you explain the concept of recursion in programming?"}
    ]
    solution = agent.get_response(messages)
    print(solution)