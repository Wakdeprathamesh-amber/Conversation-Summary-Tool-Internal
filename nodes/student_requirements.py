from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class StudentRequirements(BaseModel):
    room_type: List[str] = Field(default_factory=list, description="Preferred room types")
    budget_range: str = Field(default="", description="Budget range")
    location_preferences: List[str] = Field(default_factory=list, description="Preferred locations")
    duration: str = Field(default="", description="Contract duration")
    move_in_date: str = Field(default="", description="Desired move-in date")
    special_requests: List[str] = Field(default_factory=list, description="Special requests")

class StudentRequirementsNode:
    """LangGraph node for extracting student accommodation requirements"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are an AI agent working at **Amber**, a global student accommodation platform that helps international students find housing near their universities.

Students typically communicate their housing **requirements and preferences** across calls, WhatsApp, CRM notes, and email threads.

# Role  
Your job is to extract and maintain a **structured, up-to-date snapshot** of the student's latest accommodation requirements, based on everything the student says (either explicitly or implicitly).

# Behavior  
- Only consider **student-stated preferences** — ignore agent suggestions unless the student agrees or confirms.  
- If a student **updates** their requirements, always reflect the **latest version**.  
- Do NOT duplicate existing static CRM fields unless they are **reconfirmed** in the conversation.  
- Do NOT speculate. Only include requirements that are **clearly stated or strongly implied** by the student.

# Output Schema  
Return a **single JSON object** with the following fields:

```json
{{
  "room_type": [],                 // e.g., ["ensuite", "studio"]
  "budget_range": "",             // e.g., "£200–£250/week"
  "location_preferences": [],     // e.g., ["near King's College London", "Zone 1"]
  "duration": "",                 // e.g., "12 months", "short stay for 6 months"
  "move_in_date": "",             // e.g., "2025-09-15" or "early September"
  "special_requests": []          // e.g., ["female-only", "pet-friendly", "ground floor", "bills included"]
}}

```
Leave out any fields not mentioned — do NOT include them as null, "", or empty arrays unless there's meaningful input.
All fields must reflect the most up-to-date student input, even if stated indirectly (e.g., "That's too expensive" → budget adjustment).
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> StudentRequirements:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            req_data = json.loads(json_str)
            normalized = {
                "room_type": req_data.get("room_type", []),
                "budget_range": req_data.get("budget_range", ""),
                "location_preferences": req_data.get("location_preferences", []),
                "duration": req_data.get("duration", ""),
                "move_in_date": req_data.get("move_in_date", ""),
                "special_requests": req_data.get("special_requests", [])
            }
            return StudentRequirements(**normalized)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return StudentRequirements() 