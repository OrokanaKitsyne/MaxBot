import json
from typing import List, Dict, Any


class LocalKnowledgeBase:
    def __init__(self, path="pages_knowledge.json"):
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)

                self.documents: List[str] = []

                # full_text
                if isinstance(data, dict):
                    if "full_text" in data:
                        self.documents.append(data["full_text"])

                    # sections
                    for section in data.get("sections", []):
                        if "raw_text" in section:
                            self.documents.append(section["raw_text"])

                    # courses
                    for course in data.get("courses", []):
                        if "raw_text" in course:
                            self.documents.append(course["raw_text"])

                else:
                    self.documents = []

        except Exception as e:
            print(f"Ошибка загрузки {path}: {e}")
            self.documents = []

    def get_context_for_query(self, query: str, top_k: int = 3, max_chars: int = 3500) -> str:
        if not self.documents or not query:
            return ""

        query_lower = query.lower()
        matches = []

        for text in self.documents:
            if query_lower in text.lower():
                matches.append(text)

        result = "\n\n".join(matches[:top_k])
        return result[:max_chars]
