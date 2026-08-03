from typing import Callable

from .store import EmbeddingStore


class KnowledgeBaseAgent:
    """
    An agent that answers questions using a vector knowledge base.

    Retrieval-augmented generation (RAG) pattern:
        1. Retrieve top-k relevant chunks from the store.
        2. Build a prompt with the chunks as context.
        3. Call the LLM to generate an answer.
    """

    def __init__(self, store: EmbeddingStore, llm_fn: Callable[[str], str]) -> None:
        self.store = store
        self.llm_fn = llm_fn

    def answer(self, question: str, top_k: int = 3) -> str:
        # Bước 1: Truy xuất top-k chunks liên quan từ store
        results = self.store.search(question, top_k=top_k)

        # Bước 2: Xây dựng context từ kết quả
        context_parts = []
        for i, r in enumerate(results, 1):
            context_parts.append(f"[{i}] {r['content']}")
        context = "\n\n".join(context_parts)

        # Bước 3: Tạo prompt theo mô hình RAG
        prompt = (
            f"Based on the following context, answer the question.\n\n"
            f"Context:\n{context}\n\n"
            f"Question: {question}\n\n"
            f"Answer:"
        )

        # Bước 4: Gọi LLM và trả kết quả
        return self.llm_fn(prompt)
