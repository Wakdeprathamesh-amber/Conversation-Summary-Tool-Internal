import os
import json
from typing import Dict, Any, Optional

class SummaryStore:
    """Persistent storage for lead summaries and processing timestamps"""
    def __init__(self, lead_id: str, data_dir: str = "data"):
        self.lead_id = lead_id
        self.data_dir = data_dir
        self.summary_path = os.path.join(data_dir, lead_id, "summary_store.json")
        os.makedirs(os.path.join(data_dir, lead_id), exist_ok=True)

    def load(self) -> Optional[Dict[str, Any]]:
        if not os.path.exists(self.summary_path):
            return None
        with open(self.summary_path, "r") as f:
            return json.load(f)

    def save(self, summary: Dict[str, Any], last_processed: Dict[str, str]):
        data = {
            "summary": summary,
            "last_processed": last_processed
        }
        with open(self.summary_path, "w") as f:
            json.dump(data, f, indent=2)

    def update_last_processed(self, last_processed: Dict[str, str]):
        data = self.load() or {"summary": {}, "last_processed": {}}
        data["last_processed"].update(last_processed)
        with open(self.summary_path, "w") as f:
            json.dump(data, f, indent=2)

    def get_last_processed(self) -> Dict[str, str]:
        data = self.load() or {"summary": {}, "last_processed": {}}
        return data.get("last_processed", {})

    def get_summary(self) -> Dict[str, Any]:
        data = self.load() or {"summary": {}, "last_processed": {}}
        return data.get("summary", {}) 