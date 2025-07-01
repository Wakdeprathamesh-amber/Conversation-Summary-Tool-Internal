from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class Task(BaseModel):
    type: str = Field(default="", description="Type of task (call, email, etc.)")
    due: str = Field(default="", description="Due date/time for the task")
    status: str = Field(default="", description="Status of the task (pending, done, etc.)")
    created_by: str = Field(default="", description="Who created the task")

class TasksAndNextStepsNode:
    """LangGraph node for extracting tasks and next steps"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
# Context  
You are operating as part of **Amber**, a global student accommodation platform that helps international students find and book verified housing near their universities.

Each conversation is between a **student** and an **Amber sales agent**, where the student is trying to:
- Book or confirm their accommodation
- Get help with visa or university-related tasks
- Clarify payments, move-in dates, or booking issues
- Finalize required steps before check-in

The goal is to extract and track clearly defined **tasks and next steps** discussed during the interaction.

# Role  
You are an AI agent trained to extract structured, actionable **tasks and follow-up steps** from any student-agent conversation. These may come from phone calls, WhatsApp chats, emails, CRM notes, or support threads.

# Behavior  
- Focus on **clearly stated or strongly implied** tasks with context.
- Include only tasks with:
  - A **specific owner** (student or agent)
  - A defined **task type** (e.g., "confirm booking", "upload passport copy")
  - A **due date** or time reference (e.g., "by Monday", "before travel")
  - A **status** (e.g., pending, done, in progress)

- Disregard vague follow-ups unless structured and time-bound.
- You may infer the task or due date only if clearly implied in context.

# Output Schema  
Return a JSON array of tasks in this format:

```json
[
  {{
    "type": "",         // e.g., "make payment", "submit visa docs", "call reception"
    "due": "",          // ISO 8601 (YYYY-MM-DD) or natural phrase if no date given
    "status": "",       // "pending", "done", or "in progress"
    "created_by": ""    // "student", "agent", or their name if mentioned
  }}
]
```

Return only structured tasks. Skip if task info is unclear.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text

    async def process(self, input_data: Dict[str, Any]) -> List[Task]:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        try:
            json_str = self._extract_json_from_response(response.content)
            tasks_data = json.loads(json_str)
            return [Task(**item) for item in tasks_data]
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return [] 