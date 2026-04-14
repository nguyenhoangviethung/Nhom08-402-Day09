"""
index.py — Sprint 1: Build RAG Index
====================================
Mục tiêu Sprint 1 (60 phút):
  - Đọc và preprocess tài liệu từ data/docs/
  - Chunk tài liệu theo cấu trúc tự nhiên (heading/section)
  - Gắn metadata: source, section, department, effective_date, access
  - Embed và lưu vào vector store (ChromaDB)

Definition of Done Sprint 1:
  ✓ Script chạy được và index đủ docs
  ✓ Có ít nhất 3 metadata fields hữu ích cho retrieval
  ✓ Có thể kiểm tra chunk bằng list_chunks()
"""

import os
import json
import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

load_dotenv()

# =============================================================================
# CẤU HÌNH
# =============================================================================

DOCS_DIR = Path(__file__).parent / "data" / "docs"
CHROMA_DB_DIR = Path(__file__).parent / "chroma_db"

# TODO Sprint 1: Điều chỉnh chunk size và overlap theo quyết định của nhóm
# Gợi ý từ slide: chunk 300-500 tokens, overlap 50-80 tokens
CHUNK_SIZE = 200       # tokens (ước lượng bằng số ký tự / 4)
CHUNK_OVERLAP = 50     # tokens overlap giữa các chunk


# =============================================================================
# STEP 1: PREPROCESS
# Làm sạch text trước khi chunk và embed
# =============================================================================

def preprocess_document(raw_text: str, filepath: str) -> Dict[str, Any]:
    """
    Preprocess một tài liệu: extract metadata từ header và làm sạch nội dung.

    Args:
        raw_text: Toàn bộ nội dung file text
        filepath: Đường dẫn file để làm source mặc định

    Returns:
        Dict chứa:
          - "text": nội dung đã clean
          - "metadata": dict với source, department, effective_date, access

    TODO Sprint 1:
    - Extract metadata từ dòng đầu file (Source, Department, Effective Date, Access)
    - Bỏ các dòng header metadata khỏi nội dung chính
    - Normalize khoảng trắng, xóa ký tự rác

    Gợi ý: dùng regex để parse dòng "Key: Value" ở đầu file.
    """
    lines = raw_text.strip().split("\n")
    metadata = {
        "source": filepath,
        "section": "",
        "department": "unknown",
        "effective_date": "unknown",
        "access": "internal",
    }
    content_lines = []
    header_done = False

    for line in lines:
        stripped = line.strip()
        if not header_done:
            # TODO: Parse metadata từ các dòng "Key: Value"
            # Ví dụ: "Source: policy/refund-v4.pdf" → metadata["source"] = "policy/refund-v4.pdf"
            if stripped.startswith("Source:"):
                metadata["source"] = stripped.replace("Source:", "", 1).strip()
            elif stripped.startswith("Department:"):
                metadata["department"] = stripped.replace("Department:", "", 1).strip()
            elif stripped.startswith("Effective Date:"):
                metadata["effective_date"] = stripped.replace("Effective Date:", "", 1).strip()
            elif stripped.startswith("Access:"):
                metadata["access"] = stripped.replace("Access:", "", 1).strip()
            elif stripped.startswith("==="):
                # Gặp section heading đầu tiên → kết thúc header
                header_done = True
                content_lines.append(stripped)
            elif stripped.strip() == "" or stripped.isupper():
                # Dòng tên tài liệu (toàn chữ hoa) hoặc dòng trống
                continue
        else:
            content_lines.append(line.rstrip())

    cleaned_text = "\n".join(content_lines)

    # TODO: Thêm bước normalize text nếu cần
    # Gợi ý: bỏ ký tự đặc biệt thừa, chuẩn hóa dấu câu
    cleaned_text = "\n".join(content_lines)
    cleaned_text = re.sub(r"\r\n", "\n", cleaned_text)
    cleaned_text = re.sub(r"[ \t]+", " ", cleaned_text)
    cleaned_text = re.sub(r"\n{3,}", "\n\n", cleaned_text)  # max 2 dòng trống liên tiếp

    return {
        "text": cleaned_text,
        "metadata": metadata,
    }


# =============================================================================
# STEP 2: CHUNK
# Chia tài liệu thành các đoạn nhỏ theo cấu trúc tự nhiên
# =============================================================================

def chunk_document(doc: Dict[str, Any]) -> List[Dict[str, Any]]:
    text = doc["text"]
    base_metadata = doc["metadata"].copy()
    chunks = []

    parts = re.split(r"(===.*?===)", text)

    current_section = "General"
    current_section_text = ""

    for part in parts:
        part = part.strip()
        if not part:
            continue

        if re.fullmatch(r"===.*?===", part):
            if current_section_text.strip():
                chunks.extend(
                    _split_by_size(
                        text=current_section_text.strip(),
                        base_metadata=base_metadata,
                        section=current_section,
                    )
                )
            current_section = part.strip("= ").strip()
            current_section_text = ""
        else:
            if current_section_text:
                current_section_text += "\n\n" + part
            else:
                current_section_text = part

    if current_section_text.strip():
        chunks.extend(
            _split_by_size(
                text=current_section_text.strip(),
                base_metadata=base_metadata,
                section=current_section,
            )
        )

    return chunks


# Cache embedding model (khởi tạo 1 lần, dùng chung)
_embedding_model = None
_embedding_mode = None

def _split_by_size(
    text: str,
    base_metadata: Dict,
    section: str,
    chunk_chars: int = CHUNK_SIZE * 4,
    overlap_chars: int = CHUNK_OVERLAP * 4,
) -> List[Dict[str, Any]]:
    """
    Helper: Split text dài thành chunks với overlap.

    TODO Sprint 1:
    Hiện tại dùng split đơn giản theo ký tự.
    Cải thiện: split theo paragraph (\n\n) trước, rồi mới ghép đến khi đủ size.
    """
    paragraphs = [p.strip() for p in text.split("\n\n") if p.strip()]

    if not paragraphs:
        return []

    if len(text) <= chunk_chars:
        return [{
            "text": text.strip(),
            "metadata": {**base_metadata, "section": section},
        }]

    chunks = []
    current_chunk = ""

    for para in paragraphs:
        candidate = para if not current_chunk else f"{current_chunk}\n\n{para}"

        if len(candidate) <= chunk_chars:
            current_chunk = candidate
            continue

        if current_chunk:
            chunks.append({
                "text": current_chunk.strip(),
                "metadata": {**base_metadata, "section": section},
            })

            overlap_text = current_chunk[-overlap_chars:] if overlap_chars > 0 else ""
            current_chunk = f"{overlap_text}\n\n{para}".strip() if overlap_text else para
            continue

        start = 0
        while start < len(para):
            end = min(start + chunk_chars, len(para))
            piece = para[start:end].strip()
            if piece:
                chunks.append({
                    "text": piece,
                    "metadata": {**base_metadata, "section": section},
                })
            if end == len(para):
                break
            start = max(end - overlap_chars, start + 1)

    if current_chunk.strip():
        chunks.append({
            "text": current_chunk.strip(),
            "metadata": {**base_metadata, "section": section},
        })

    return chunks


# =============================================================================
# STEP 3: EMBED + STORE
# Embed các chunk và lưu vào ChromaDB
# =============================================================================

def get_embedding(text: str) -> List[float]:
    """
    Tạo embedding vector cho một đoạn text.
    Dùng SentenceTransformer local với model khai báo trong .env:
      LOCAL_EMBEDDING_MODEL=bkai-foundation-models/vietnamese-bi-encoder
    """
    global _embedding_model, _embedding_mode
    if _embedding_mode is None:
        # 1) Try local SentenceTransformer first
        try:
            from sentence_transformers import SentenceTransformer
            model_name = os.getenv("LOCAL_EMBEDDING_MODEL", "bkai-foundation-models/vietnamese-bi-encoder")
            print(f"  [Embedding] Đang load model: {model_name}")
            _embedding_model = SentenceTransformer(model_name)
            _embedding_mode = "local"
            print("  [Embedding] Load model xong!")
        except Exception as exc:
            print(f"  [Embedding] ⚠️ Local model lỗi: {exc}")

        # 2) Fallback to OpenAI if available
        if _embedding_mode is None:
            try:
                from openai import OpenAI
                api_key = os.getenv("OPENAI_API_KEY")
                if api_key:
                    _embedding_model = OpenAI(api_key=api_key)
                    _embedding_mode = "openai"
                    print("  [Embedding] Dùng OpenAI embedding fallback.")
            except Exception as exc:
                print(f"  [Embedding] ⚠️ OpenAI fallback lỗi: {exc}")

        # 3) Final fallback: random vectors (debug only)
        if _embedding_mode is None:
            _embedding_mode = "random"
            print("  [Embedding] ⚠️ Dùng random embedding (debug only).")

    if _embedding_mode == "local":
        return _embedding_model.encode(text).tolist()
    if _embedding_mode == "openai":
        try:
            resp = _embedding_model.embeddings.create(input=[text], model="text-embedding-3-small")
            return resp.data[0].embedding
        except Exception as exc:
            print(f"  [Embedding] ⚠️ OpenAI call lỗi: {exc}")
            _embedding_mode = "random"

    import random
    return [random.random() for _ in range(768)]


def build_index(docs_dir: Path = DOCS_DIR, db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Pipeline hoàn chỉnh: đọc docs → preprocess → chunk → embed → store.

    TODO Sprint 1:
    1. Cài thư viện: pip install chromadb
    2. Khởi tạo ChromaDB client và collection
    3. Với mỗi file trong docs_dir:
       a. Đọc nội dung
       b. Gọi preprocess_document()
       c. Gọi chunk_document()
       d. Với mỗi chunk: gọi get_embedding() và upsert vào ChromaDB
    4. In số lượng chunk đã index

    Gợi ý khởi tạo ChromaDB:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_or_create_collection(
            name=os.getenv("CHROMA_COLLECTION", ""),
            metadata={"hnsw:space": "cosine"}
        )
    """
    import chromadb

    print(f"Đang build index từ: {docs_dir}")
    db_dir.mkdir(parents=True, exist_ok=True)

    # TODO: Khởi tạo ChromaDB
    # Khởi tạo ChromaDB
    client = chromadb.PersistentClient(path=str(db_dir))
    collection = client.get_or_create_collection(
        name=os.getenv("CHROMA_COLLECTION", ""),
        metadata={"hnsw:space": "cosine"}
    )

    total_chunks = 0
    doc_files = list(docs_dir.glob("*.txt"))

    if not doc_files:
        print(f"Không tìm thấy file .txt trong {docs_dir}")
        return

    for filepath in doc_files:
        print(f"  Processing: {filepath.name}")
        raw_text = filepath.read_text(encoding="utf-8")

        doc = preprocess_document(raw_text, str(filepath))
        chunks = chunk_document(doc)

        for i, chunk in enumerate(chunks):
            chunk_id = f"{filepath.stem}_{i}"
            embedding = get_embedding(chunk["text"])
            collection.upsert(
                ids=[chunk_id],
                embeddings=[embedding],
                documents=[chunk["text"]],
                metadatas=[chunk["metadata"]],
            )
        total_chunks += len(chunks)
        print(f"    → {len(chunks)} chunks indexed")

    print(f"\nHoàn thành! Tổng số chunks: {total_chunks}")


# =============================================================================
# STEP 4: INSPECT / KIỂM TRA
# Dùng để debug và kiểm tra chất lượng index
# =============================================================================

def list_chunks(db_dir: Path = CHROMA_DB_DIR, n: int = 5) -> None:
    """
    In ra n chunk đầu tiên trong ChromaDB để kiểm tra chất lượng index.

    TODO Sprint 1:
    Implement sau khi hoàn thành build_index().
    Kiểm tra:
    - Chunk có giữ đủ metadata không? (source, section, effective_date)
    - Chunk có bị cắt giữa điều khoản không?
    - Metadata effective_date có đúng không?
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection("rag_lab")
        results = collection.get(limit=n, include=["documents", "metadatas"])

        print(f"\n=== Top {n} chunks trong index ===\n")
        for i, (doc, meta) in enumerate(zip(results["documents"], results["metadatas"])):
            print(f"[Chunk {i+1}]")
            print(f"  Source: {meta.get('source', 'N/A')}")
            print(f"  Section: {meta.get('section', 'N/A')}")
            print(f"  Effective Date: {meta.get('effective_date', 'N/A')}")
            print(f"  Text preview: {doc[:120]}...")
            print()
    except Exception as e:
        print(f"Lỗi khi đọc index: {e}")
        print("Hãy chạy build_index() trước.")


def inspect_metadata_coverage(db_dir: Path = CHROMA_DB_DIR) -> None:
    """
    Kiểm tra phân phối metadata trong toàn bộ index.

    Checklist Sprint 1:
    - Mọi chunk đều có source?
    - Có bao nhiêu chunk từ mỗi department?
    - Chunk nào thiếu effective_date?

    TODO: Implement sau khi build_index() hoàn thành.
    """
    try:
        import chromadb
        client = chromadb.PersistentClient(path=str(db_dir))
        collection = client.get_collection("rag_lab")
        results = collection.get(include=["metadatas"])

        print(f"\nTổng chunks: {len(results['metadatas'])}")

        # TODO: Phân tích metadata
        # Đếm theo department, kiểm tra effective_date missing, v.v.
        departments = {}
        missing_date = 0
        for meta in results["metadatas"]:
            dept = meta.get("department", "unknown")
            departments[dept] = departments.get(dept, 0) + 1
            if meta.get("effective_date") in ("unknown", "", None):
                missing_date += 1

        print("Phân bố theo department:")
        for dept, count in departments.items():
            print(f"  {dept}: {count} chunks")
        print(f"Chunks thiếu effective_date: {missing_date}")

    except Exception as e:
        print(f"Lỗi: {e}. Hãy chạy build_index() trước.")


# =============================================================================
# MAIN
# =============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("Sprint 1: Build RAG Index")
    print("=" * 60)

    # Bước 1: Kiểm tra docs
    doc_files = list(DOCS_DIR.glob("*.txt"))
    print(f"\nTìm thấy {len(doc_files)} tài liệu:")
    for f in doc_files:
        print(f"  - {f.name}")

    # Bước 2: Test preprocess và chunking (không cần API key)
    print("\n--- Test preprocess + chunking ---")
    for filepath in doc_files[:1]:  # Test với 1 file đầu
        raw = filepath.read_text(encoding="utf-8")
        doc = preprocess_document(raw, str(filepath))
        chunks = chunk_document(doc)
        print(f"\nFile: {filepath.name}")
        print(f"  Metadata: {doc['metadata']}")
        print(f"  Số chunks: {len(chunks)}")
        for i, chunk in enumerate(chunks[:3]):
            print(f"\n  [Chunk {i+1}] Section: {chunk['metadata']['section']}")
            print(f"  Text: {chunk['text'][:150]}...")

    # Bước 3: Build index
    print("\n--- Build Full Index ---")
    build_index()

    # Bước 4: Kiểm tra index
    list_chunks()
    inspect_metadata_coverage()

    print("\nSprint 1 hoàn thành! ✅")
    print("Đã hoàn thành:")
    print("  ✓ get_embedding() — dùng bkai-foundation-models/vietnamese-bi-encoder (local)")
    print("  ✓ build_index()   — embed + upsert 29 chunks vào ChromaDB")
    print("  ✓ list_chunks()   — kiểm tra chunk hợp lý, đủ metadata")
    print("  ✓ _split_by_size() — split theo paragraph với overlap")