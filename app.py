import asyncio
import time
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn
import sys
import json

# Import the timeline extraction function
def import_timeline_func():
    try:
        from db_test_extract import consolidate_and_save_timeline
        return consolidate_and_save_timeline
    except ImportError:
        print("Could not import timeline extraction function.")
        return None

# Add import for orchestrator
from llm_analysis.orchestrator import generate_requirements_summary
from llm_analysis.orchestrator import generate_combined_summary

app = FastAPI()

# Allow CORS for local frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/generate-timeline")
def generate_timeline_api(mobile: str = Query(None), email: str = Query(None)):
    """
    Generate timeline for a given mobile number or email.
    Returns the timeline JSON as used by the frontend.
    """
    timeline_func = import_timeline_func()
    if not timeline_func:
        return JSONResponse(status_code=500, content={"error": "Timeline extraction function not available."})
    if not mobile and not email:
        return JSONResponse(status_code=400, content={"error": "Provide either mobile or email."})
    # Run extraction and load the generated file
    timeline_func(mobile_number=mobile, email=email)
    # Determine file path
    import os
    if mobile:
        timeline_path = os.path.join('data', f'timeline_{mobile}.json')
    elif email:
        email_safe = email.replace('@', '_').replace('.', '_')
        timeline_path = os.path.join('data', f'timeline_{email_safe}.json')
    else:
        timeline_path = os.path.join('data', 'timeline_unknown.json')
    if not os.path.exists(timeline_path):
        return JSONResponse(status_code=404, content={"error": "Timeline not found."})
    with open(timeline_path, 'r', encoding='utf-8') as f:
        timeline = f.read()
    return JSONResponse(content=json.loads(timeline))

@app.get("/generate-summary")
def generate_summary_api(mobile: str = Query(None), email: str = Query(None)):
    """
    Generate LLM summary for a given mobile number or email.
    Returns the raw LLM output as JSON.
    """
    import os
    if not mobile and not email:
        return JSONResponse(status_code=400, content={"error": "Provide either mobile or email."})
    if mobile:
        timeline_path = os.path.join('data', f'timeline_{mobile}.json')
    elif email:
        email_safe = email.replace('@', '_').replace('.', '_')
        timeline_path = os.path.join('data', f'timeline_{email_safe}.json')
    else:
        timeline_path = os.path.join('data', 'timeline_unknown.json')
    if not os.path.exists(timeline_path):
        return JSONResponse(status_code=404, content={"error": "Timeline not found."})
    try:
        result = generate_combined_summary(timeline_path)
        return JSONResponse(content=result)
    except Exception as e:
        return JSONResponse(status_code=500, content={"error": str(e)})

if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "api":
        uvicorn.run("app:app", host="0.0.0.0", port=8000, reload=True)
    else:
        # For now, just test with Lead001
        result = generate_requirements_summary("data/timeline_Lead001.json")
        print("\n===== ON-DEMAND SUMMARY OUTPUT =====")
        print(json.dumps(result, indent=2)) 