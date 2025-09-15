import os
from google import genai
from google.genai import types
import json
from django.utils.safestring import mark_safe
import markdown
import re

def generate_questions(course_name: str, topic: str, num_questions: int = 5) -> list:
    client = genai.Client(api_key=os.environ.get("GEMINI_API_KEY"))

    prompt_text = f"""
    You are an educational assistant.
    Generate {num_questions} clear and concise revision questions
    for the course with marks "{course_name}" on the topic "{topic}".
    Format the output strictly as a JSON list of strings.
    """

    contents = [
        types.Content(
            role="user",
            parts=[types.Part.from_text(text=prompt_text)],
        )
    ]

    generate_config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_budget=-1)
    )

    response_text = ""
    for chunk in client.models.generate_content_stream(
        model="gemini-2.5-flash",
        contents=contents,
        config=generate_config
    ):
        if chunk.text:  # ✅ skip None
            response_text += chunk.text

    # Clean up JSON
    response_text = response_text.strip()
    match = re.search(r'\[.*\]', response_text, re.DOTALL)
    if match:
        response_text = match.group(0)

    try:
        questions_list = json.loads(response_text)
        if not isinstance(questions_list, list):
            questions_list = [str(questions_list)]
    except Exception:
        questions_list = [response_text]

    html_questions = [mark_safe(markdown.markdown(q)) for q in questions_list]
    return html_questions
