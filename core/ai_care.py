import re
import google.genai as genai
from google.genai import types
from django.conf import settings

class AcademicAIService:
    def __init__(self):
        # Initialize cuea AI client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def provide_guidance(self, question_text=None):
        """
        Returns AI-generated guidance specifically about CUEA.
        """
        prompt = """
        You are an AI assistant for CUEA (Catholic University of Eastern Africa).
        Provide accurate, clear, and helpful answers to questions about CUEA programs, courses, faculties, departments, admission, and other academic information.
        Emphasize important terms using **bold**. Explain concepts clearly.
        """

        if question_text:
            prompt += f"\nUser question: {question_text}"

        prompt += """
        Return a JSON array with objects:
        - title: short hint or concept
        - description: detailed explanation
        - url: optional resource link (CUEA official website if available)
        """

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(temperature=0.8, max_output_tokens=1200)

        try:
            response = self.client.models.generate_content(
                model="gemini-2.0-flash",
                contents=contents,
                config=config
            )
            text_output = response.text
        except Exception as e:
            print("Gemini API error:", e)
            text_output = """
            [
                {
                    "title": "CUEA Guidance",
                    "description": "The AI service is temporarily unavailable. Please visit https://www.cuea.edu for official information.",
                    "url": "https://www.cuea.edu"
                }
            ]
            """

        # Remove markdown code blocks if present
        text_output = re.sub(r"^```json\s*|\s*```$", "", text_output.strip(), flags=re.MULTILINE)
        return text_output
