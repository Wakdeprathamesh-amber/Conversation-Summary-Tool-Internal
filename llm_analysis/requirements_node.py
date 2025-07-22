import os
import json
from openai import OpenAI

class RequirementsNode:
    def __init__(self, openai_api_key: str, prompt_path: str):
        self.openai_api_key = openai_api_key
        self.prompt_path = prompt_path
        self.client = OpenAI(api_key=self.openai_api_key)

    def load_prompt(self):
        with open(self.prompt_path, 'r', encoding='utf-8') as f:
            return f.read()

    def run(self, timeline_path: str, output_path: str = None):
        with open(timeline_path, 'r', encoding='utf-8') as f:
            timeline = json.load(f)
        prompt = self.load_prompt()
        # Insert timeline as JSON string (or prettified)
        timeline_str = json.dumps(timeline, indent=2, ensure_ascii=False)
        full_prompt = prompt.replace('{TIMELINE}', timeline_str)
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert assistant for extracting student accommodation requirements."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        # Extract the JSON from the response
        result_text = response.choices[0].message.content
        try:
            result_json = json.loads(result_text)
        except Exception:
            # Try to extract JSON substring if LLM output is not pure JSON
            import re
            match = re.search(r'\{[\s\S]*\}', result_text)
            if match:
                result_json = json.loads(match.group(0))
            else:
                raise ValueError("Could not parse JSON from LLM output")
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, indent=2, ensure_ascii=False)
            print(f"[RequirementsNode] Saved requirements to {output_path}")
        return result_json 