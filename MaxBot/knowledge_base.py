import json
import re
from pathlib import Path
from typing import List, Dict, Any


class LocalKnowledgeBase:
    def __init__(self, path: str = "pages_knowledge.json"):
        self.path = Path(path)

        if not self.path.exists():
            raise FileNotFoundError(
                f"Файл базы знаний не найден: {self.path}"
            )

        with self.path.open("r", encoding="utf-8") as f:
            self.documents: List[Dict[str, Any]] = json.load(f)

        if not isinstance(self.documents, list):
            raise ValueError("pages_knowledge.json должен содержать список объектов")

        self.index_record = self._find_index_record()

    def _find_index_record(self) -> Dict[str, Any] | None:
        for doc in self.documents:
            if doc.get("type") == "index":
                return doc
        return None

    def _normalize_text(self, text: str) -> str:
        text = (text or "").lower().strip()
        text = text.replace("ё", "е")
        text = re.sub(r"\s+", " ", text)
        return text

    def _tokenize(self, text: str) -> set[str]:
        text = self._normalize_text(text)
        return set(re.findall(r"[a-zA-Zа-яА-Я0-9]+", text))

    def _build_searchable_text(self, doc: Dict[str, Any]) -> str:
        parts = [
            doc.get("title", ""),
            doc.get("description", ""),
            doc.get("text", ""),
            doc.get("slug", ""),
            doc.get("source_file", ""),
            " ".join(doc.get("phones", [])),
            " ".join(doc.get("emails", [])),
        ]

        if doc.get("type") == "index":
            for course in doc.get("courses", []):
                parts.extend([
                    course.get("title", ""),
                    course.get("description", ""),
                    course.get("age", ""),
                    course.get("url", ""),
                ])

        if doc.get("type") == "course_page":
            parts.extend(doc.get("sections", []))

        return " ".join(p for p in parts if p).strip()

    def _score_document(self, query: str, doc: Dict[str, Any]) -> int:
        query_norm = self._normalize_text(query)
        query_tokens = self._tokenize(query)

        searchable_text = self._build_searchable_text(doc)
        searchable_norm = self._normalize_text(searchable_text)
        searchable_tokens = self._tokenize(searchable_text)

        score = 0

        # Совпадения по токенам
        overlap = query_tokens & searchable_tokens
        score += len(overlap) * 3

        # Бонус за прямое вхождение запроса
        if query_norm and query_norm in searchable_norm:
            score += 15

        # Бонус за совпадение в заголовке
        title_norm = self._normalize_text(doc.get("title", ""))
        if query_norm and query_norm in title_norm:
            score += 20

        # Бонус за частичное совпадение токенов в title
        title_tokens = self._tokenize(doc.get("title", ""))
        score += len(query_tokens & title_tokens) * 5

        # Бонус для course_page, если пользователь спрашивает про конкретику
        if doc.get("type") == "course_page":
            score += 2

        return score

    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        query = (query or "").strip()
        if not query:
            return []

        scored = []

        for doc in self.documents:
            score = self._score_document(query, doc)
            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)

        return [doc for _, doc in scored[:top_k]]

    def get_context_for_query(self, query: str, top_k: int = 3, max_chars: int = 4000) -> str:
        docs = self.search(query, top_k=top_k)

        if not docs:
            return ""

        context_parts = []
        total_len = 0

        for doc in docs:
            block_parts = [
                f"Источник: {doc.get('source_file', '')}",
                f"Заголовок: {doc.get('title', '')}",
                f"Описание: {doc.get('description', '')}",
                f"Текст: {doc.get('text', '')}",
            ]

            if doc.get("type") == "course_page" and doc.get("sections"):
                block_parts.append("Разделы: " + " | ".join(doc.get("sections", [])[:10]))

            block = "\n".join(p for p in block_parts if p).strip()

            if not block:
                continue

            if total_len + len(block) > max_chars:
                remaining = max_chars - total_len
                if remaining > 200:
                    context_parts.append(block[:remaining])
                break

            context_parts.append(block)
            total_len += len(block)

        return "\n\n".join(context_parts).strip()

    def get_index_courses(self) -> List[Dict[str, Any]]:
        if not self.index_record:
            return []

        courses = self.index_record.get("courses", [])
        if not isinstance(courses, list):
            return []

        unique = []
        seen = set()

        for course in courses:
            key = (
                self._normalize_text(course.get("title", "")),
                self._normalize_text(course.get("url", "")),
            )

            if key in seen:
                continue

            seen.add(key)
            unique.append(course)

        return unique

    def get_course_names(self) -> List[str]:
        names = []

        for course in self.get_index_courses():
            title = course.get("title", "").strip()
            if title:
                names.append(title)

        for doc in self.documents:
            if doc.get("type") == "course_page":
                title = doc.get("title", "").strip()
                if title:
                    names.append(title)

        names = sorted(set(names))
        return names

    def get_page_by_slug(self, slug: str) -> Dict[str, Any] | None:
        slug = self._normalize_text(slug)

        for doc in self.documents:
            if self._normalize_text(doc.get("slug", "")) == slug:
                return doc

        return None

    def get_page_by_source_file(self, source_file: str) -> Dict[str, Any] | None:
        source_file = self._normalize_text(source_file)

        for doc in self.documents:
            if self._normalize_text(doc.get("source_file", "")) == source_file:
                return doc

        return None

    def stats(self) -> Dict[str, Any]:
        index_count = sum(1 for d in self.documents if d.get("type") == "index")
        course_page_count = sum(1 for d in self.documents if d.get("type") == "course_page")

        return {
            "total_documents": len(self.documents),
            "index_pages": index_count,
            "course_pages": course_page_count,
            "has_index": self.index_record is not None,
            "index_courses_count": len(self.get_index_courses()),
        }
