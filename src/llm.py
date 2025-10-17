# import libraries
import os
from openai import OpenAI
from dotenv import load_dotenv


load_dotenv()  # Loads environment variables from .env
# Do NOT read sensitive environment variables at import time to avoid crashes
# when the environment variable is not available (for example, on Vercel during build).
endpoint = "https://models.github.ai/inference"
model = "openai/gpt-4.1-mini"
# A function to call an LLM model and return the response
def call_llm_model(model, messages, temperature=1.0, top_p=1.0):
    # Read token at call time so importing this module doesn't fail when the
    # environment variable is not present. This prevents serverless function
    # crashes during startup when secrets are not configured.
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set. LLM calls require this token.")

    client = OpenAI(base_url=endpoint, api_key=token)
    response = client.chat.completions.create(
        messages=messages,
        temperature=temperature, top_p=top_p, model=model
    )
    return response.choices[0].message.content

# A function to call an LLM model and return the response
def call_llm_model_raw(model, messages, temperature=1.0, top_p=1.0):
    token = os.environ.get("GITHUB_TOKEN")
    if not token:
        raise RuntimeError("GITHUB_TOKEN environment variable is not set. LLM calls require this token.")

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
            "content": "You are a helpful assistant that translates text to other languages.",
        },
        {
            "role": "user",
            "content": f"Translate the following text to {target_language}: {text}",
        }
    ]
    return call_llm_model(model, messages)


def translate_tags(tags, target_language="French"):
    """Translate a list of tag strings and return a comma-separated string
    containing only the literal translations (no extra text or punctuation).

    tags: list[str] or comma-separated string
    returns: string like "老师, 指导者, 学校"
    """
    # Normalize tags to a list of plain words
    if not tags:
        return ''
    if isinstance(tags, str):
        # If tags is a JSON-like string (e.g., '["A","B"]') or CSV, try to parse
        import json
        try:
            parsed = json.loads(tags)
            if isinstance(parsed, list):
                tag_list = [t for t in parsed]
            else:
                # fallback: split by comma
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
        except Exception:
            tag_list = [t.strip() for t in tags.split(',') if t.strip()]
    elif isinstance(tags, list):
        tag_list = [t for t in tags]
    else:
        tag_list = [str(tags)]

    # Translate tags one-by-one to reduce ambiguity and force a single-word response
    translations = []
    for tag in tag_list:
        t = str(tag).strip()
        if not t:
            continue
        # Ask the model to return only the literal translated word
        messages = [
            {
                "role": "system",
                "content": "You are a strict translator. When asked to translate a single word or short phrase, respond with ONLY the translated word or phrase in the target language. Do NOT add any extra text, explanation, punctuation, or quotes."
            },
            {
                "role": "user",
                "content": f"Translate the following word to {target_language}: {t}"
            }
        ]
        try:
            res = call_llm_model(model, messages).strip()
        except Exception:
            res = ''

        # Clean the response: remove backticks, surrounding quotes, brackets
        res = res.replace('`', '').strip()
        if res.startswith('[') and res.endswith(']'):
            try:
                import json
                parsed = json.loads(res)
                if isinstance(parsed, list) and parsed:
                    res = str(parsed[0]).strip()
            except Exception:
                # fallback to trimming brackets
                res = res.lstrip('[').rstrip(']')

        # Remove surrounding quotes
        if (res.startswith('"') and res.endswith('"')) or (res.startswith("'") and res.endswith("'")):
            res = res[1:-1].strip()

        # If model returns multiple lines, take first non-empty line
        if '\n' in res:
            lines = [l.strip() for l in res.splitlines() if l.strip()]
            res = lines[0] if lines else res

        translations.append(res)

    # Join translations preserving order, skipping empties
    cleaned_translations = [s for s in [t.strip() for t in translations] if s]
    return ', '.join(cleaned_translations)


# A function to detect the language of text using the LLM model
def detect_language(text):
    """Detect the language of the given text"""
    messages = [
        {
            "role": "system",
            "content": "You are a helpful assistant that detects the language of text. Respond with only the language name in English (e.g., 'English', 'French', 'Spanish', etc.).",
        },
        {
            "role": "user",
            "content": f"What language is this text written in? Text: {text}",
        }
    ]
    return call_llm_model(model, messages).strip()


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
