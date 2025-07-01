from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class TimelineEvent(BaseModel):
    type: str = Field(default="", description="Type of event: call, whatsapp, email, etc.")
    timestamp: str = Field(default="", description="Timestamp of the event")
    agent: str = Field(default="", description="Agent involved (if applicable)")
    direction: str = Field(default="", description="Direction of communication: inbound/outbound (if applicable)")
    content: str = Field(default="", description="Content or summary of the event (if applicable)")
    duration: str = Field(default="", description="Duration (for calls, if applicable)")

class ConversationTimelineNode:
    """LangGraph node for constructing a channel-wise conversation timeline"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Role
You are an AI agent trained to create a timeline of interactions between the agent and the student.

# Behavior
- Use WhatsApp, calls, and email metadata.
- Be concise, sort chronologically, skip small talk or repeated messages.

# Task
Return a JSON array of timeline events:

```json
[
  {{
    "type": "",          // call, email, whatsapp
    "timestamp": "",
    "agent": "",
    "direction": "",     // inbound/outbound
    "content": "",       // short description of what was discussed
    "duration": ""       // in seconds (for calls)
  }}
]
```

Omit any field if unknown.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> List[TimelineEvent]:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            events_data = json.loads(json_str)
            return [TimelineEvent(**item) for item in events_data]
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return [] 