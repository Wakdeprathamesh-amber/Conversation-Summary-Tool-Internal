from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class LeadStatus(BaseModel):
    funnel_stage: str = Field(default="", description="Lead funnel stage")
    intent: str = Field(default="", description="Lead intent level")
    urgency: str = Field(default="", description="Lead urgency level")
    tags: List[str] = Field(default_factory=list, description="Relevant tags for the lead")

class LeadStatusNode:
    """LangGraph node for extracting lead status information"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are working inside **Amber**, a global student accommodation company where students are supported through conversations across channels (calls, WhatsApp, CRM, email).

Each lead is a student looking for housing, and may be at different stages in the booking funnel.

# Role  
You are an AI agent trained to **assess and classify the current status of a student lead** based on all available communication history.

# Behavior  
- Focus exclusively on the **booking-related funnel stage, urgency, and student intent**.
- Analyze messages, timelines, confirmations, and tone to infer status.
- Do NOT extract tasks, timeline summaries, or general conversation context.
- Use tags for helpful metadata like blockers or conditions.

# Output Schema  
Return a structured JSON object:

```json
{{
  "funnel_stage": "",   // e.g., "initial inquiry", "property shared", "offer sent", "booking in progress", "payment done"
  "intent": "",         // e.g., "high intent", "medium intent", "casually browsing", "not interested"
  "urgency": "",        // e.g., "urgent", "move-in this week", "medium urgency", "no clear urgency"
  "tags": []            // e.g., ["visa approved", "budget sensitive", "follow-up needed", "awaiting payment"]
}}
```
Avoid default values or placeholders.
Ensure values match the context inferred from the student's engagement level.
Return ONLY the JSON object.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> LeadStatus:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            status_data = json.loads(json_str)
            normalized = {
                "funnel_stage": status_data.get("funnel_stage", ""),
                "intent": status_data.get("intent", ""),
                "urgency": status_data.get("urgency", ""),
                "tags": status_data.get("tags", [])
            }
            return LeadStatus(**normalized)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return LeadStatus() 