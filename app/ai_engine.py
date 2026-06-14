# app/ai_engine.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

# Load environment variables
load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# Use the latest Gemini 1.5 Flash model (Fast and cheap for text crunching)
model = genai.GenerativeModel('gemini-1.5-flash')

def generate_study_materials(transcript_text: str, options: list) -> dict:
    """
    Takes raw text and asks Gemini to generate specific study materials 
    formatted strictly as JSON.
    """
    
    # We construct a prompt based on what the user selected in the UI
    requests = []
    if "summary" in options:
        requests.append("- A comprehensive 'summary' (string)")
    if "flashcards" in options:
        requests.append("- A list of 'flashcards', each with a 'question' and 'answer' (list of dicts)")
    if "quiz" in options:
        requests.append("- A list of 'quiz_questions', each with a 'question', 4 'options', and the 'correct_answer' (list of dicts)")
    
    request_str = "\n".join(requests)
    
    prompt = f"""
    You are an expert academic tutor. Analyze the following lecture transcript and extract the requested study materials.
    
    You MUST respond ONLY with a valid JSON object containing the following keys based on what was requested:
    {request_str}
    
    Do not include markdown formatting like ```json. Just return the raw JSON object.
    
    TRANSCRIPT:
    {transcript_text[:15000]} # Limiting characters just for safety, though Gemini 1.5 can handle massive context
    """

    try:
        response = model.generate_content(prompt)
        # Parse the string response into a Python dictionary
        result_dict = json.loads(response.text)
        return result_dict
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return {"error": str(e)}