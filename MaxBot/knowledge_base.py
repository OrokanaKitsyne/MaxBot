import re
import requests
from bs4 import BeautifulSoup


class WebsiteKnowledgeBase:
    def __init__(self):
        self.pages = [
            "https://algoritmika.org/ru",
            "https://algoritmika.org/ru/coding/pc",
            "https://algoritmika.org/ru/coding/creative",
            "https://algoritmika.org/ru/coding/videocontent",
            "https://algoritmika.org/ru/coding/graphicdesign",
            "https://algoritmika.org/ru/coding/gamedesign",
            "https://algoritmika.org/ru/coding/websites",
            "https://algoritmika.org/ru/coding/unity",
            "https://algoritmika.org/ru/coding/pytpro",
            "https://algoritmika.org/ru/coding/frontend",
            "https://algoritmika.org/ru/math",
        ]
        self.documents = []

    def load(self):
        self.documents = []

        for url in self.pages:
            try:
                response = requests.get(url, timeout=20)
                response.raise_for_status()

                soup = BeautifulSoup(response.text, "html.parser")

                for tag in soup(["script", "style", "noscript"]):
                    tag.decompose()

                text = soup.get_text(separator=" ", strip=True)
                text = re.sub(r"\s+", " ", text).strip()

                chunks = self.split_text(text, chunk_size=700)

                for chunk in chunks:
                    self.documents.append({
                        "url": url,
                        "text": chunk
                    })

                print(f"LOADED: {url} | chunks={len(chunks)}", flush=True)

            except Exception as e:
                print(f"LOAD ERROR: {url} | {e}", flush=True)

    def split_text(self, text: str, chunk_size: int = 700):
        words = text.split()
        chunks = []

        for i in range(0, len(words), chunk_size):
            chunk = " ".join(words[i:i + chunk_size]).strip()
            if chunk:
                chunks.append(chunk)

        return chunks

    def search(self, query: str, top_k: int = 3):
        query_words = set(re.findall(r"\w+", query.lower()))
        scored = []

        for doc in self.documents:
            doc_words = set(re.findall(r"\w+", doc["text"].lower()))
            score = len(query_words & doc_words)

            if score > 0:
                scored.append((score, doc))

        scored.sort(key=lambda x: x[0], reverse=True)
        return [doc for _, doc in scored[:top_k]]
