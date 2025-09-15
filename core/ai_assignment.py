import re
import google.genai as genai
from google.genai import types
from django.conf import settings

class AIAssignmentService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def provide_guidance(self, student_text=None):
        """
        Returns AI-generated guidance, explanations, and tips for an assignment.
        Does not automatically solve the assignment, but gives flexible support.
        student_text: optional content student uploads (drafts, notes, code)
        """
        prompt = """
        You are an educational assistant helping a student understand and complete their assignment.
        Provide explanations, hints, strategies, and resources.
        It's okay to give example approaches or conceptual guidance,
        but do NOT simply provide the full answer.
        """
        if student_text:
            prompt += f"\nThe student submitted the following content:\n{student_text}"

        prompt += """
        Return a JSON array with objects:
        - title: brief hint or tip title
        - description: detailed guidance or explanation (use **bold** to emphasize important words)
        - url: optional resource link (can be Google search, tutorial, or documentation)
        Be flexible: allow multiple tips or examples in the guidance.
        """

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(temperature=0.8, max_output_tokens=1200)

        text_output = ""
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
                    "title": "General Guidance",
                    "description": "Our AI service is temporarily unavailable. Focus on your notes, textbooks, and online tutorials.",
                    "url": "https://www.google.com/search?q=assignment+help"
                }
            ]
            """

        # Strip markdown code block formatting
        text_output = re.sub(r"^```json\s*|\s*```$", "", text_output.strip(), flags=re.MULTILINE)

        return text_output
