from typing import Dict, Any, List
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class ConversationSummary(BaseModel):
    key_discussion_points: List[str] = Field(default_factory=list)
    objections_raised: List[str] = Field(default_factory=list)
    questions_asked: List[str] = Field(default_factory=list)
    other_details: List[str] = Field(default_factory=list)

class ConversationSummaryNode:
    """LangGraph node for generating a TL;DR summary of the conversation"""
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()

    def _load_prompt(self):
        template = """
    # Context  
    You are part of **Amber**, a global student accommodation platform helping international students secure housing near their universities.  
    Conversations take place over calls, WhatsApp, CRM notes, and emails, and typically involve:  
    - Property selection and preferences  
    - Booking status and payments  
    - Visa and university timelines  
    - Move-in planning, objections, and coordination  

    # Role  
    You are an AI agent trained to extract and maintain a **structured, comprehensive summary** of a conversation between a **student** and a **sales agent**.  
    This summary will be used by **sales, support, and operations teams** to understand what was discussed and what needs follow-up.

    # Behavior  
    - Review the full conversation transcript, which is provided as a single string.  
    - Each line in the transcript is in the format: `[timestamp] [CHANNEL] content` (e.g., `[2025-02-15 08:02] [CALL] ...`).
    - Extract all **explicit and implied details** from the transcript, regardless of channel.  
    - Capture **questions, blockers, updates, tone, hesitations, and concerns** — not just the main topics.  
    - Preserve **chronological order** where required.  
    - Never guess. Include only what's clearly said or strongly implied.

    # Output Schema  
    Return a structured JSON object with the following fields:

    ```json
    {{
    "key_discussion_points": [
        "Student asked about ensuite options near King's College London",
        "Agent explained tenancy start dates and billing cycles",
        "Student shared that visa may be delayed by 2 weeks"
    ],
    "objections_raised": [
        "Uncomfortable with current pricing due to currency exchange rate",
        "Uncertain about confirming before visa approval"
    ],
    "questions_asked": [
        "Can I cancel if my visa is denied?",
        "Are there any offers for early booking?"
    ],
    "other_details": [
        "Student seemed hesitant but interested",
        "Tone was polite and cooperative throughout",
        "Mentioned they will discuss with family before deciding"
    ]
    }}
    ```
    
    # Input Data
    Transcript:
    {input_data}
    """
        self.prompt = PromptTemplate.from_template(template)

    def _extract_json_from_response(self, text: str) -> str:
        # Match triple backtick code block, with or without 'json'
        code_block_match = re.search(r'```(?:json)?\s*([\s\S]*?)\s*```', text, re.IGNORECASE)
        if code_block_match:
            candidate = code_block_match.group(1).strip()
            # Remove any leading/trailing backticks or language tags just in case
            candidate = re.sub(r'^```(?:json)?', '', candidate, flags=re.IGNORECASE).strip()
            candidate = re.sub(r'```$', '', candidate).strip()
            print(f"[DEBUG] Candidate JSON string before parsing:\n{candidate}\n")
            return candidate
        print(f"[DEBUG] No code block found, using raw text:\n{text.strip()}\n")
        return text.strip()

    async def process(self, input_data: Dict[str, Any]) -> ConversationSummary:
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        response = await self.llm.ainvoke(formatted_prompt)
        print(f"\n[DEBUG] Raw LLM response:\n{response.content}\n")
        try:
            json_str = self._extract_json_from_response(response.content)
            print(f"[DEBUG] Candidate JSON string before parsing:\n{json_str}\n")
            summary_data = json.loads(json_str)
            return ConversationSummary(**summary_data)
        except (json.JSONDecodeError, ValueError, TypeError) as e:
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return ConversationSummary() 