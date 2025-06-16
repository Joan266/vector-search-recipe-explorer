import re
from typing import List, Dict
import google.generativeai as genai
from config import GEMINI_API_KEY

class TextProcessor:
    def __init__(self):
        genai.configure(api_key=GEMINI_API_KEY)
        self.gemini_model = genai.GenerativeModel('gemini-pro')

    def transform_instructions(self, instructions: str) -> str:
        """Transform recipe instructions using Gemini API"""
        try:
            prompt = """
            You are an experienced, friendly, and encouraging chef providing clear audio instructions for a home cook. 
            Your goal is to guide the user through each step of the recipe, making it sound natural, easy to follow, 
            and engaging, as if you're speaking directly to them.

            For each distinct step, provide the instruction in a conversational tone. Break down complex steps into 
            simpler actions where appropriate. When referring to temperatures or timings, clearly state them.

            Present the output as a numbered list of instructions. Do not include any introductory or concluding 
            remarks outside of the numbered steps themselves.

            Here are the recipe instructions:
            """
            
            response = self.gemini_model.generate_content(f"{prompt}\n{instructions}")
            return response.text
        except Exception:
            return instructions

    def normalize_text(self, text: str) -> str:
        """Normalize recipe instructions text"""
        if not text:
            return ""
        text = re.sub(r'[\r\n]+', '. ', text)
        text = re.sub(r'\.{2,}', '.', text)
        return re.sub(r'\s+', ' ', text).strip()

    def split_into_steps(self, text: str) -> List[str]:
        """Split instructions into individual steps"""
        if not text:
            return []
        steps = re.split(r'(?<=\d)\.\s+|(?<=[.!?])\s+(?=[A-Z])', text)
        return [step.strip() for step in steps if step.strip()]