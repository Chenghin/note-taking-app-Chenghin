# import libraries
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv() # Loads environment variables from .env
token = os.environ["GITHUB_TOKEN"]
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"
# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0): 
    client = OpenAI(base_url=endpoint, api_key=token)
    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature, top_p=top_p, model=model
    )
    return response.choices[0].message.content

# A function to call an LLM model and return the response
def call_llm_model_raw(model, messages, temperature=1.0, top_p=1.0): 
    client = OpenAI(base_url=endpoint, api_key=token)
    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature, top_p=top_p, model=model
    )
    return response

# A function to translate text using the LLM model
def translate_text(text, target_language="French"):
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that translates English to other languages.",
        },
        {
            "role": "user",
            "content": f"Translate the following text to {target_language}: {text}",
        }
    ]
    return call_llm_model(model, messages)

# main function for testing
if __name__ == "__main__":
    test_text = "Hello, how are you?"
    translated = translate_text(test_text, target_language="Chinese")
    print(f"Original: {test_text}\nTranslated: {translated}")