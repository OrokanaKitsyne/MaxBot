import json
import re
from typing import List, Dict


class LocalKnowledgeBase:
    def __init__(self, path: str = "knowledge.json"):
        with open(path, "r", encoding="utf-8") as f:
            self.documents = json.load(f)

    def search(self, query: str, top_k: int = 5) -> List[Dict]:
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []

        for doc in self.documents:
            text = doc.get("text", "").lower()
            words = set(re.findall(r"\w+", text))
            score = len(query_words & words)

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
