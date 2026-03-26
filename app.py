from fastapi import FastAPI
from pydantic import BaseModel
from openai import OpenAI
import os
import json

# -------------------------------
# Initialize FastAPI and OpenAI
# -------------------------------
app = FastAPI(title="CV Analyzer & Cover Letter Generator")

api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise Exception("OPENAI_API_KEY not set in environment")

client = OpenAI(api_key=api_key)

# -------------------------------
# Prompts
# -------------------------------
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

# -------------------------------
# Request model
# -------------------------------
class CVRequest(BaseModel):
    cv_text: str
    role: str

# -------------------------------
# Endpoint: Analyze CV
# -------------------------------
@app.post("/analyze")
async def analyze_cv(req: CVRequest):
    try:
        response = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyse this CV:\n\n{req.cv_text}"}
            ],
            temperature=0.3
        )
        # Parse JSON safely
        analysis = json.loads(response.choices[0].message.content)
        return {"analysis": analysis}
    except Exception as e:
        return {"error": str(e)}

# -------------------------------
# Endpoint: Generate Cover Letter
# -------------------------------
@app.post("/coverletter")
async def cover_letter(req: CVRequest):
    try:
        # Step 1: Analyze CV
        analysis_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": f"Analyse this CV:\n\n{req.cv_text}"}
            ],
            temperature=0.3
        )
        analysis = json.loads(analysis_resp.choices[0].message.content)

        # Step 2: Generate Cover Letter
        prompt_msg = (
            f"Target role: {req.role}\n"
            f"Strengths: {analysis['strengths']}\n"
            f"CV: {req.cv_text}"
        )
        cover_resp = client.chat.completions.create(
            model="gpt-4o",
            messages=[
                {"role": "system", "content": COVER_LETTER_PROMPT},
                {"role": "user", "content": prompt_msg}
            ],
            temperature=0.7
        )
        cover_letter_text = cover_resp.choices[0].message.content

        return {"analysis": analysis, "cover_letter": cover_letter_text}

    except Exception as e:
        return {"error": str(e)}
