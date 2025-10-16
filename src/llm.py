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


def generate_notes_from_title(title, lang="English"):
    """Generate detailed notes/content from a short title using the LLM."""
    messages = [
        {
            "role": "system",
            "content": f"You are a helpful assistant that expands short titles into detailed notes in {lang}. Write concise, clear notes in full sentences based on the title."
        },
        {
            "role": "user",
            "content": f"Write detailed notes for the title: {title}"
        }
    ]
    return call_llm_model(model, messages)


system_prompt = '''

Today's date and time: {current_datetime}.
Extract the user's notes into the following structured fields:
1. Title: A concise title of the notes less than 5 words
2. Notes: The notes based on user input written in full sentences.
3. Tags (A list): At most 3 Keywords or tags that categorize the content of the notes.
Output in JSON format without ```json. Output title and notes in the language: {lang}.
4. Event date
5. Event time
Example:
Input: "Badminton tmr 5pm @polyu".
Output:
{{
 "Title": "Badminton at PolyU", 
 "Notes": "Remember to play badminton at 5pm tomorrow at PolyU.",
 "Tags": ["badminton", "sports"],
 "Event date": "2023-10-06",
 "Event time": "17:00"
}}
'''

# A function to extract structured notes using the LLM model
def extract_structured_notes(text, lang="English"):
    from datetime import datetime
    current_datetime = datetime.now().strftime("%Y-%m-%d %H:%M")
    prompt = system_prompt.format(current_datetime=current_datetime, lang=lang)
    messages = [
        {
            "role": "system",
            "content": prompt
        },
        {
            "role": "user",
            "content": f"Extract structured notes from the following text: {text}"
        }
    ]
    response = call_llm_model(model, messages)
    # Attempt to parse the response as JSON
    import json
    try:
        structured = json.loads(response)
        return structured
    except json.JSONDecodeError:
        # If parsing fails, return the raw response for debugging
        return {"error": "Failed to parse JSON", "response": response}


# main function for testing
if __name__ == "__main__":
    # test the extract notes feature
    sample_text = "Meeting with John about the project at 3pm on Friday. Remember to bring the presentation slides."
    structured_notes = extract_structured_notes(sample_text, lang="Chinese")
    print("Extracted Structured Notes:")
    print(structured_notes)
