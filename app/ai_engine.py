# app/ai_engine.py
import os
import json
from dotenv import load_dotenv
from google import genai
from google.genai import types

# Load environment variables
load_dotenv()

api_key = os.getenv("GEMINI_API_KEY")

# Initialize the new Google GenAI Client
client = genai.Client(api_key=api_key) if api_key else None

def generate_study_materials(content_text: str, options: list) -> dict:
    if not client:
        return {"error": "Missing GEMINI_API_KEY in .env file."}

    requests = []
    options = [opt.lower().strip() for opt in options]
    
    if "summary" in options:
        requests.append("- A comprehensive 'summary' (string)")
    if "flashcards" in options:
        requests.append("- A list of 'flashcards', each with a 'question' and 'answer' (list of dicts)")
    if "quiz" in options:
        requests.append("- A list of 'quiz_questions', each with a 'question', 4 'options' (list of strings), and the 'correct_answer' (string) (list of dicts)")
    if "mind map" in options or "mindmap" in options:
        requests.append("- A 'mind_map' representing core concepts as a hierarchical structure (nested dictionary)")
    
    if not requests:
        return {"error": "No valid options selected for generation."}

    request_str = "\n".join(requests)
    
    prompt = f"""
    You are an expert academic tutor. Analyze the following educational content and extract the requested study materials.
    
    You MUST respond ONLY with a valid JSON object containing the following keys based on what was requested:
    {request_str}
    
    CONTENT:
    {content_text[:20000]} 
    """

    try:
        # Using the new SDK syntax and forcing strict JSON output
        response = client.models.generate_content(
            model='gemini-2.5-flash',
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        
        result_dict = json.loads(response.text)
        return result_dict
        
    except json.JSONDecodeError:
        return {"error": "AI returned malformed data. Try again."}
    except Exception as e:
        return {"error": str(e)}