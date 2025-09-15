import re
import google.genai as genai
from google.genai import types
from django.conf import settings

class TimetableAIService:
    def __init__(self):
        self.client = genai.Client(api_key=settings.GEMINI_API_KEY)

    def create_timetable(self, courses):
        """
        Generates a personal timetable based on a list of courses.
        courses: list of dicts with 'code', 'name', 'credits', 'preferred_times' (optional)
        Returns JSON with day-wise schedule.
        """
        prompt = """
        You are a university AI assistant. Create a weekly timetable for a student.
        - Input courses are listed with code, name, and credits.
        - Avoid time conflicts.
        - Distribute courses evenly across weekdays.
        - Suggest ideal study times if no preference is given.
        - Return JSON format: {"day": [{"time": "HH:MM-HH:MM", "course_code": "", "course_name": ""}]}
        """

        prompt += "\nCourses:\n" + str(courses)

        contents = [types.Content(role="user", parts=[types.Part.from_text(text=prompt)])]
        config = types.GenerateContentConfig(temperature=0.7, max_output_tokens=1200)

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
            {
                "Monday": [],
                "Tuesday": [],
                "Wednesday": [],
                "Thursday": [],
                "Friday": []
            }
            """

        # Remove code block formatting if any
        text_output = re.sub(r"^```json\s*|\s*```$", "", text_output.strip(), flags=re.MULTILINE)
        return text_output
