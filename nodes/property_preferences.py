from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class PropertyPreference(BaseModel):
    property_name: str = Field(default="", description="Name of the property discussed")
    room_type: str = Field(default="", description="Type of room discussed")
    student_thoughts: str = Field(default="", description="Student's thoughts or feedback on the property")

class PropertyPreferencesNode:
    """LangGraph node for extracting property preferences"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are part of **Amber**, a global student accommodation platform helping international students book verified housing near their universities.

In conversations between students and Amber agents, students often share their preferences for:
- Property type (studio, ensuite, shared)
- Amenities (gym, laundry, study room)
- Distance from university or locality
- Budget constraints or payment flexibility
- Gender-specific housing or visa requirements

# Role  
You are an AI agent trained to extract all student feedback on specific properties shared by the agent.

# Behavior  
- For ANY property name, room type, or location mentioned by either student or agent, include it in the output, even if feedback is minimal or only implied.
- If the student does not express a clear opinion, set 'student_thoughts' to 'not specified'.
- Capture student opinions/queries/likes/dislikes per property if available.

# Task
Return a list of properties with feedback:

```json
[
  {{
    "property_name": "",
    "room_type": "",
    "student_thoughts": ""
  }}
]
```

Return ONLY the array of objects.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        # Match triple backtick code block, with or without 'json', allowing for extra whitespace/newlines
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
        if code_block_match:
            candidate = code_block_match.group(1).strip()
            candidate = re.sub(r'^```(?:json)?', '', candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(r'```$', '', candidate).strip()
            print(f"[DEBUG] Candidate JSON string before parsing:\n{candidate}\n")
            return candidate
        print(f"[DEBUG] No code block found, using raw text:\n{text.strip()}\n")
        return text.strip()

    async def process(self, input_data: Dict[str, Any]) -> List[PropertyPreference]:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        print(f"\n[DEBUG] Raw LLM response:\n{response.content}\n")
        try:
            json_str = self._extract_json_from_response(response.content)
            prefs_data = json.loads(json_str)
            return [PropertyPreference(**item) for item in prefs_data]
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return [] 