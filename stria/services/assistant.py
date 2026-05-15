import os
import asyncio
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

system_prompt = """"""

async def call_openai(prompt: str):
    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": prompt}
        ],
        model="gpt-4o-mini",
        temperature=0.1,
        max_tokens=250
    )
    return response.choices[0].message.content

if __name__ == "__main__":
    prompt = "Testing"
    response = asyncio.run(call_openai(prompt))
    print(response)