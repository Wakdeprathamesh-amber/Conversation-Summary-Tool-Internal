import os
import json
from typing import Dict, Any

class DataLoader:
    def __init__(self, lead_id: str, data_dir: str = "data"):
        self.lead_id = lead_id
        self.data_dir = data_dir
        self.lead_path = os.path.join(data_dir, lead_id)

    def load_calls(self, last_processed: Dict[str, str]) -> str:
        call_file = os.path.join(self.lead_path, "call_001.txt")
        if not os.path.exists(call_file):
            return ""
        # If never processed, load all; otherwise, return empty (no incremental logic for plain text)
        if not last_processed.get("calls"):
            with open(call_file, "r") as f:
                return f.read()
        return ""

    # Placeholder for future data types
    def load_whatsapp(self, last_processed: Dict[str, str]):
        return []
    def load_email(self, last_processed: Dict[str, str]):
        return []
    def load_lead(self, last_processed: Dict[str, str]):
        # Find the first JSON file in the lead directory that is not summary_store.json or .DS_Store
        for fname in os.listdir(self.lead_path):
            if fname.endswith('.json') and fname not in ('summary_store.json', '.DS_Store'):
                lead_file = os.path.join(self.lead_path, fname)
                try:
                    with open(lead_file, 'r') as f:
                        data = f.read()
                        parsed = json.loads(data)
                        # If the file is a list, return the first item
                        if isinstance(parsed, list) and len(parsed) > 0:
                            return parsed[0]
                        return parsed
                except Exception as e:
                    print(f"Error loading lead file {lead_file}: {e}")
                    return None
        return None

    def load_all(self, last_processed: Dict[str, str]) -> Dict[str, Any]:
        data = {}
        if not os.path.exists(self.lead_path):
            return data
        for fname in os.listdir(self.lead_path):
            if fname in ("summary_store.json", ".DS_Store"):
                continue
            fpath = os.path.join(self.lead_path, fname)
            key = os.path.splitext(fname)[0]
            try:
                if fname.endswith('.json'):
                    with open(fpath, 'r') as f:
                        content = f.read()
                        parsed = json.loads(content)
                        # If the file is a list, use the full list
                        if isinstance(parsed, list):
                            data[key] = parsed
                        else:
                            data[key] = parsed
                else:
                    # Try to read as text
                    with open(fpath, 'r') as f:
                        data[key] = f.read()
            except Exception as e:
                print(f"Error loading file {fpath}: {e}")
                data[key] = None
        return data 