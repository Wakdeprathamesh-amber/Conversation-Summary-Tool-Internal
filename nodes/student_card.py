from typing import Dict, Any
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from pydantic import BaseModel, Field
import json
import re

class StudentProfile(BaseModel):
    """Schema for student profile information"""
    name: str = Field(description="Student's full name")
    nationality: str = Field(description="Student's nationality")
    course_details: Dict[str, str] = Field(description="Course and university details")
    budget: Dict[str, Any] = Field(description="Budget preferences and constraints")
    requirements: Dict[str, Any] = Field(description="Housing requirements and preferences")
    contact_info: Dict[str, str] = Field(description="Contact information")

class StudentCardNode:
    """LangGraph node for generating student profile cards"""
    
    def __init__(self, llm: ChatOpenAI):
        self.llm = llm
        self._load_prompt()
    
    def _load_prompt(self):
        """Load the improved prompt template for student card generation"""
        template = """
# Role
You are an AI agent trained to extract static profile information about a student from CRM data.

# Behavior
- Focus only on structured CRM-style data (not conversational messages).
- Extract background info, contact, and course details.
- Avoid duplicating intent, urgency, or conversation summaries.

# Task
Generate a structured profile card with the following fields:

```json
{{
  "name": "",
  "nationality": "",
  "course_details": {{
    "course_name": "",
    "university": "",
    "start_date": ""
  }},
  "budget": {{
    "range": "",
    "payment_frequency": "",
    "notes": ""
  }},
  "requirements": {{
    "room_type": [],
    "locations": [],
    "amenities": [],
    "contract_length": "",
    "move_in_date": ""
  }},
  "contact_info": {{
    "email": "",
    "phone": ""
  }}
}}
```

Return ONLY the JSON object.
Input Data:
{input_data}
"""
        self.prompt = PromptTemplate.from_template(template)
    
    def _extract_json_from_response(self, text: str) -> str:
        """Extract JSON from response text, handling code blocks."""
        # Try to find JSON within code blocks first
        code_block_match = re.search(r'```(?:json)?\n(.*?)\n```', text, re.DOTALL)
        if code_block_match:
            return code_block_match.group(1)
        return text
    
    async def process(self, input_data: Dict[str, Any]) -> StudentProfile:
        """Process lead data and generate a student profile"""
        # Format the prompt with lead data
        formatted_prompt = self.prompt.format(input_data=json.dumps(input_data, indent=2))
        
        # Get response from LLM
        response = await self.llm.ainvoke(formatted_prompt)
        
        try:
            # Extract and parse JSON from response
            json_str = self._extract_json_from_response(response.content)
            profile_data = json.loads(json_str)
            
            # Normalize the data structure if needed
            normalized_data = {
                "name": profile_data.get("name", ""),
                "nationality": profile_data.get("nationality", ""),
                "course_details": {
                    "course_name": profile_data.get("course_details", {}).get("course_name", ""),
                    "university": profile_data.get("course_details", {}).get("university", ""),
                    "start_date": profile_data.get("course_details", {}).get("start_date", "")
                },
                "budget": {
                    "range": profile_data.get("budget", {}).get("range", ""),
                    "payment_frequency": profile_data.get("budget", {}).get("payment_frequency", ""),
                    "notes": profile_data.get("budget", {}).get("notes", "")
                },
                "requirements": {
                    "room_type": profile_data.get("requirements", {}).get("room_type", []),
                    "locations": profile_data.get("requirements", {}).get("locations", []),
                    "amenities": profile_data.get("requirements", {}).get("amenities", []),
                    "contract_length": profile_data.get("requirements", {}).get("contract_length", ""),
                    "move_in_date": profile_data.get("requirements", {}).get("move_in_date", "")
                },
                "contact_info": {
                    "email": profile_data.get("contact_info", {}).get("email", ""),
                    "phone": profile_data.get("contact_info", {}).get("phone", "")
                }
            }
            
            # Create and return StudentProfile instance
            return StudentProfile(**normalized_data)
            
        except (json.JSONDecodeError, ValueError) as e:
            # If parsing fails, return an empty profile
            print(f"Error parsing LLM response: {e}")
            print(f"Raw response: {response.content}")
            return StudentProfile(
                name="",
                nationality="",
                course_details={},
                budget={},
                requirements={},
                contact_info={}
            ) 