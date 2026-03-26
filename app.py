from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
import json

app = FastAPI()

# Initialize OpenAI client
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise Exception("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=api_key)

# Prompts
SYSTEM_PROMPT = """
You are an expert career coach and professional CV reviewer.
Respond ONLY with a JSON object in this exact format:
{"strengths":["...","...","..."],
 "improvements":["...","...","..."],
 "overall_score":7,
 "score_reason":"One sentence explanation"}
Every point must reference a specific CV detail. Return valid JSON only.
"""

COVER_LETTER_PROMPT = """
You are an expert cover letter writer.
Write a 200-280 word cover letter using specific CV achievements.
Open with a strong, specific first sentence. Return the letter text only.
"""

# Request models
class CVRequest(BaseModel):
    cv_text: str
    role: str

# Endpoint to analyze CV
@app.post("/analyze")
async def analyze_cv(req: CVRequest):
    try:
        resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system", "content": SYSTEM_PROMPT},
                {"role":"user", "content": f"Analyse this CV:\n\n{req.cv_text}"}
            ],
            temperature=0.3
        )
        analysis = json.loads(resp.choices[0].message.content)
    except Exception as e:
        return {"error": str(e)}
    return {"analysis": analysis}

# Endpoint to generate cover letter
@app.post("/coverletter")
async def cover_letter(req: CVRequest):
    try:
        # First analyze
        analysis_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system", "content": SYSTEM_PROMPT},
                {"role":"user", "content": f"Analyse this CV:\n\n{req.cv_text}"}
            ],
            temperature=0.3
        )
        analysis = json.loads(analysis_resp.choices[0].message.content)

        # Generate cover letter
        msg = f'Target role: {req.role}\nStrengths: {analysis["strengths"]}\nCV: {req.cv_text}'
        cover_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role":"system","content":COVER_LETTER_PROMPT},
                {"role":"user","content":msg}
            ],
            temperature=0.7
        )
        cover_letter_text = cover_resp.choices[0].message.content
    except Exception as e:
        return {"error": str(e)}
    return {"analysis": analysis, "cover_letter": cover_letter_text}
