# app/ai_engine.py
import google.generativeai as genai
import os
from dotenv import load_dotenv
import json

load_dotenv()
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

model = genai.GenerativeModel('gemini-1.5-flash')

def generate_study_materials(transcript_text: str, options: list) -> dict:
    requests = []
    options = [opt.lower().strip() for opt in options]
    
    if "summary" in options:
        requests.append("- A comprehensive 'summary' (string)")
    if "flashcards" in options:
        requests.append("- A list of 'flashcards', each with a 'question' and 'answer' (list of dicts)")
    if "quiz" in options:
        requests.append("- A list of 'quiz_questions', each with a 'question', 4 'options', and the 'correct_answer' (list of dicts)")
    if "mind map" in options or "mindmap" in options:
        requests.append("- A 'mind_map' representing core concepts as a hierarchical structure (nested dictionary)")
    
    request_str = "\n".join(requests)
    
    prompt = f"""
    You are an expert academic tutor. Analyze the following content and extract the requested study materials.
    
    You MUST respond ONLY with a valid JSON object containing the following keys based on what was requested:
    {request_str}
    
    Do not include markdown formatting like ```json. Just return the raw JSON object.
    
    CONTENT:
    {transcript_text[:15000]}
    """

    try:
        response = model.generate_content(prompt)
        # Strip markdown if the AI accidentally adds it
        clean_json = response.text.replace("```json", "").replace("```", "").strip()
        result_dict = json.loads(clean_json)
        return result_dict
    except Exception as e:
        print(f"AI Generation Error: {e}")
        return {"error": str(e)}