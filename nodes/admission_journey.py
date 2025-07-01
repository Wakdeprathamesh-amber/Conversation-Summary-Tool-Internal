from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class AdmissionJourney(BaseModel):
    admission_journey: str = Field(default="", description="Summary of the student's admission, booking, and visa journey.")

class AdmissionJourneyNode:
    """LangGraph node for extracting the student's admission journey"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are working within **Amber**, a global student accommodation platform that assists international students in finding housing near their universities.

In many cases, conversations between students and Amber agents also touch upon **the student's admission journey** — such as:
- University application and confirmation
- Visa application and status
- Flight booking and travel plans
- Guarantor requirements

# Role  
You are an AI agent trained to **track and summarize the student's admission journey**. Your job is to extract the most **up-to-date, structured information** related to the student's academic onboarding and international travel — independent of accommodation matters.

# Behavior  
- Review all available sources: call logs, WhatsApp chats, emails, CRM notes.
- Always prefer **latest status** if multiple references exist.
- Focus only on academic onboarding and travel aspects.
- Do NOT include anything about accommodation, property availability, pricing, or bookings.

# Output Schema  
Return a structured JSON object with the following fields:

```json
{{
  "university_status": "",     // e.g., "admission confirmed", "waiting for CAS", "applied but pending"
  "visa_status": "",           // e.g., "approved", "in progress", "not yet applied"
  "guarantor_status": "",      // e.g., "not required", "student looking for one", "provided by agent"
  "flight_status": "",         // e.g., "booked", "rescheduled to June 25", "not booked"
  "other_details": []          // Optional array of extra notes (e.g., "student has IELTS waiver", "medical certificate needed")
}}

```
Omit any field entirely if there is no meaningful data.
Do NOT include empty strings ("").
Summarize clearly but concisely.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            journey_data = json.loads(json_str)
            # Return the dict directly for new schema
            return journey_data
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return {} 