from __future__ import annotations

import importlib
import re
import sys
import unicodedata
from pathlib import Path


ROOT_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = Path("data/k4_ecommerce")
PACKAGE_NAME = "src.Le_Tri_Tung-2A202601458"


QUERIES = [
    (
        "Nguoi mua can lam gi khi muon doi tra san pham bi loi?",
        "k4-returns-policy",
        None,
    ),
    (
        "Nguoi ban can cung cap thong tin gi truoc khi bat dau ban hang?",
        "k4-seller-listing",
        {"customer_role": "seller"},
    ),
    (
        "Vi sao nguoi mua nen thanh toan trong nen tang?",
        "k4-payment-security",
        None,
    ),
    (
        "Khi don giao cham hoac that lac, nguoi mua nen cung cap thong tin gi?",
        "k4-shipping-support",
        None,
    ),
    (
        "Du lieu ca nhan duoc dung cho nhung muc dich nao?",
        "k4-privacy-policy",
        None,
    ),
]


CATEGORY_TERMS = {
    "returns": [
        "doi tra",
        "tra hang",
        "san pham loi",
        "khong dung mo ta",
        "bang chung",
        "yeu cau doi tra",
        "hinh anh",
        "video",
    ],
    "listing": [
        "nguoi ban",
        "dang ban",
        "bat dau ban hang",
        "thong tin dinh danh",
        "tai khoan ngan hang",
        "giay phep dang ky kinh doanh",
        "ma so thue",
        "san pham bi cam",
    ],
    "payment": [
        "thanh toan",
        "giao dich",
        "trong nen tang",
        "bang chung thanh toan",
        "hoan tien",
        "tranh chap",
        "phuong thuc thanh toan",
    ],
    "shipping": [
        "giao hang",
        "nhan hang",
        "don giao cham",
        "that lac",
        "ma don hang",
        "van chuyen",
        "doi tac giao nhan",
    ],
    "privacy": [
        "du lieu ca nhan",
        "muc dich",
        "xu ly don hang",
        "xac minh thanh toan",
        "ho tro khach hang",
        "khieu nai",
        "phat hien gian lan",
        "cai thien dich vu",
    ],
}


def strip_accents(text: str) -> str:
    text = text.lower().replace("đ", "d").replace("Đ", "d")
    text = unicodedata.normalize("NFD", text)
    return "".join(ch for ch in text if unicodedata.category(ch) != "Mn")


def parse_front_matter(text: str) -> tuple[dict, str]:
    if not text.startswith("---"):
        return {}, text

    parts = text.split("---", 2)
    if len(parts) < 3:
        return {}, text

    metadata = {}
    for raw in parts[1].splitlines():
        line = raw.strip()
        if not line or ":" not in line:
            continue
        key, value = line.split(":", 1)
        metadata[key.strip()] = value.split("#", 1)[0].strip().strip('"').strip("'")
    return metadata, parts[2].strip()


def load_documents(pkg):
    docs = []
    for path in sorted(DATA_DIR.glob("*.md")):
        metadata, body = parse_front_matter(path.read_text(encoding="utf-8"))
        docs.append(pkg.Document(metadata["doc_id"], body, metadata))
    return docs


def keyword_embedding(text: str) -> list[float]:
    cleaned = strip_accents(text)
    vector = []
    for category, terms in CATEGORY_TERMS.items():
        category_score = 0.0
        for term in terms:
            category_score += cleaned.count(term)
        if category in cleaned:
            category_score += 2.0
        vector.append(category_score)
    return vector


class HeadingParagraphChunker:
    def chunk(self, text: str) -> list[str]:
        sections = []
        current = []
        for line in text.splitlines():
            if line.startswith("#") and current:
                sections.append("\n".join(current).strip())
                current = [line]
            else:
                current.append(line)
        if current:
            sections.append("\n".join(current).strip())

        chunks = []
        for section in sections:
            chunks.extend(piece.strip() for piece in re.split(r"\n\s*\n", section) if piece.strip())
        return chunks


def chunk_documents(pkg, docs, chunker):
    chunk_docs = []
    for doc in docs:
        for index, content in enumerate(chunker.chunk(doc.content)):
            metadata = dict(doc.metadata)
            metadata["doc_id"] = doc.id
            metadata["chunk_index"] = index
            chunk_docs.append(pkg.Document(f"{doc.id}::chunk_{index}", content, metadata))
    return chunk_docs


def score_results(results, gold_doc_id):
    ids = [result["metadata"]["doc_id"] for result in results]
    if ids and ids[0] == gold_doc_id:
        return 2
    if gold_doc_id in ids:
        return 1
    return 0


def main() -> int:
    sys.path.insert(0, str(ROOT_DIR))
    pkg = importlib.import_module(PACKAGE_NAME)
    docs = load_documents(pkg)
    strategies = {
        "Loan_fixed_no_overlap": pkg.FixedSizeChunker(chunk_size=300, overlap=0),
        "Tung_recursive": pkg.RecursiveChunker(chunk_size=300),
        "Bao_sentence_2": pkg.SentenceChunker(max_sentences_per_chunk=2),
        "Trang_fixed_overlap": pkg.FixedSizeChunker(chunk_size=500, overlap=80),
        "VuXuanAnh_heading_paragraph": HeadingParagraphChunker(),
    }

    print("## Group Retrieval Benchmark")
    print()
    print("Embedding: deterministic keyword/category embedding for repeatable classroom benchmark.")
    print()

    for strategy_name, chunker in strategies.items():
        store = pkg.EmbeddingStore(embedding_fn=keyword_embedding)
        store.add_documents(chunk_documents(pkg, docs, chunker))
        total = 0

        print(f"### {strategy_name}")
        print()
        print("| # | points | top-3 doc_ids | top-3 scores |")
        print("|---|---:|---|---|")
        for index, (query, gold_doc_id, metadata_filter) in enumerate(QUERIES, start=1):
            if metadata_filter:
                results = store.search_with_filter(query, top_k=3, metadata_filter=metadata_filter)
            else:
                results = store.search(query, top_k=3)
            points = score_results(results, gold_doc_id)
            total += points
            ids = ", ".join(result["metadata"]["doc_id"] for result in results)
            scores = ", ".join(f"{result['score']:.2f}" for result in results)
            print(f"| {index} | {points} | {ids} | {scores} |")
        print()
        print(f"Total: {total}/10")
        print()

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
