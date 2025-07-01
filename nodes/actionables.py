from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class Actionables(BaseModel):
    agent_actions: List[str] = Field(default_factory=list, description="Next actions for the agent")
    student_actions: List[str] = Field(default_factory=list, description="Next actions for the student")

class ActionablesNode:
    """LangGraph node for extracting next actions for agent and student"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are operating within **Amber**, a global student housing platform that connects international students with verified properties.

Conversations are between a **student** and an **Amber sales agent**, where the goal is to finalize accommodation through:
- Offer confirmations
- Budget/location alignment
- Move-in scheduling
- Payment handling
- Document submission (e.g., visas, admission letters)

These conversations may occur over calls, WhatsApp, emails, or CRM notes.

# Role  
You are an AI agent trained to extract follow-up actions and responsibilities from the student-agent conversation.

# Behavior  
- Separate agent vs. student tasks.
- Only include actionable tasks, not general comments or preferences.

# Task  
Return a JSON object like:

```json
{{
  "student_actionables": [],
  "sales_agent_actionables": []
}}
```

Only include actual actions. Leave arrays empty if no actions discussed.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> Actionables:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            actions_data = json.loads(json_str)
            normalized = {
                "agent_actions": actions_data.get("sales_agent_actionables", []),
                "student_actions": actions_data.get("student_actionables", [])
            }
            return Actionables(**normalized)
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return Actionables() 