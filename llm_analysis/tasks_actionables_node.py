import os
import json
from openai import OpenAI

class TasksAndActionablesNode:
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
        timeline_str = json.dumps(timeline, indent=2, ensure_ascii=False)
        full_prompt = prompt.replace('{TIMELINE}', timeline_str)
        print("[TasksAndActionablesNode] Sending prompt to LLM...")
        response = self.client.chat.completions.create(
            model="gpt-4.1-mini",
            messages=[
                {"role": "system", "content": "You are an expert assistant for extracting tasks and actionables from student accommodation conversations."},
                {"role": "user", "content": full_prompt}
            ],
            temperature=0.2,
            max_tokens=1500
        )
        result_text = response.choices[0].message.content
        print("[TasksAndActionablesNode] Received LLM response")
        try:
            result_json = json.loads(result_text)
        except Exception as e:
            print(f"[TasksAndActionablesNode] JSON parsing error: {e}")
            import re
            match = re.search(r'\{[\s\S]*\}', result_text)
            if match:
                try:
                    result_json = json.loads(match.group(0))
                except Exception as e2:
                    print(f"[TasksAndActionablesNode] Fallback JSON parsing error: {e2}")
                    raise ValueError("Could not parse JSON from LLM output")
            else:
                print("[TasksAndActionablesNode] No JSON object found in LLM output.")
                raise ValueError("Could not parse JSON from LLM output")
        if output_path:
            with open(output_path, 'w', encoding='utf-8') as f:
                json.dump(result_json, f, indent=2, ensure_ascii=False)
            print(f"[TasksAndActionablesNode] Saved output to {output_path}")
        return result_json 