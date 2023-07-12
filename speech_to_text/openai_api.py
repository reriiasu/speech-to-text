import openai
import os


class OpenAIAPI:
    def __init__(self):
        openai.api_key = os.getenv("OPENAI_API_KEY")
        self.MODEL_NAME = "gpt-3.5-turbo"
        self.MAX_TOKENS = 2000

    def text_proofreading(self, text: str):
        response = openai.ChatCompletion.create(
            model=self.MODEL_NAME,
            max_tokens=self.MAX_TOKENS,
            messages=[
                {
                    "role": "system",
                    "content": "Please proofread. Please return only the proofreading results.",
                },
                {"role": "user", "content": text},
            ],
        )
        return response.choices[0]["message"]["content"].strip()
