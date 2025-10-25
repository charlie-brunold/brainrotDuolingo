# test_groq.py
import os
import time
from groq import Groq
from dotenv import load_dotenv

load_dotenv()

client = Groq(api_key=os.environ.get("GROQ_API_KEY"))

start = time.time()

response = client.chat.completions.create(
    messages=[
        {
            "role": "user",
            "content": "Evaluate this comment: 'Great explanation, very helpful!'"
        }
    ],
    model="openai/gpt-oss-20b",
    temperature=0.5,
    max_tokens=500
)

elapsed = (time.time() - start) * 1000

print(f"Response time: {elapsed:.0f}ms")
print(f"\n{response.choices[0].message.content}")