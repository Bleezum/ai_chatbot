import os
import json
import re
import google.genai as genai
from google.genai import types
from django.conf import settings

class AIService:
    def __init__(self):
        # Initialize Gemini client
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def fetch_online_resources(self, course_name, student):
        """
        Returns a list of recommended online resources for the given course.
        Ensures JSON parsing even if AI returns extra text.
        """

        # Prompt for Gemini
        prompt_text = f"""
        You are an educational assistant.
        Recommend 3-5 free, high-quality online resources for the course '{course_name}'.
        Include e-books, lecture notes, tutorials, or videos.

        If specific resources cannot be found, suggest general resources to help students understand the topic.

        Return ONLY a JSON array with the following fields for each resource:
        - title
        - description
        - url

        Example:
        [
          {{
            "title": "Intro to CS",
            "description": "Free ebook for learning computer science basics.",
            "url": "https://example.com/intro-cs"
          }}
        ]
        """

        # Prepare request
        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt_text)])]
        
        # Use a simpler configuration without thinking budget
        config = types.GenerateContentConfig(
            temperature=0.7,
            max_output_tokens=1000,
        )

        # Collect response
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
            # Return a fallback resource on API error
            return [
                {
                    "title": f"General resources for {course_name}",
                    "description": "Our AI service is temporarily unavailable. Try searching online tutorials or textbooks.",
                    "url": "https://www.google.com/search?q=" + course_name.replace(" ", "+")
                }
            ]

        # Strip markdown code block if present
        text_output = re.sub(r"^```json\s*|\s*```$", "", text_output.strip(), flags=re.MULTILINE)

        # Extract first JSON array only
        match = re.search(r"\[.*\]", text_output, re.DOTALL)
        if match:
            text_output = match.group(0)
        else:
            text_output = ""

        # Parse JSON safely
        resources = []
        if text_output:
            try:
                resources = json.loads(text_output)
                # Validate that we have at least one resource
                if not resources or not isinstance(resources, list):
                    raise json.JSONDecodeError("Empty or invalid resources", "", 0)
            except json.JSONDecodeError:
                # fallback resource if JSON is invalid
                resources = [
                    {
                        "title": f"General resources for {course_name}",
                        "description": "No specific online resources found. You can check Google Scholar, OpenCourseWare, or YouTube tutorials.",
                        "url": "https://www.google.com/search?q=" + course_name.replace(" ", "+")
                    }
                ]
        else:
            # fallback if no text at all
            resources = [
                {
                    "title": f"General resources for {course_name}",
                    "description": "No online resources found. Try searching online tutorials or textbooks.",
                    "url": "https://www.google.com/search?q=" + course_name.replace(" ", "+")
                }
            ]

        return resources