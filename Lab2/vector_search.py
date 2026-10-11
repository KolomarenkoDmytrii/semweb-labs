import time
import random
from pathlib import Path

from ollama import embed
import chromadb


def call_ollama_with_retry(
    api_call_func, *args, max_retries=4, initial_delay=1.0, max_delay=60.0, **kwargs
):
    delay = initial_delay
    for attempt in range(1, max_retries + 1):
        try:
            return api_call_func(*args, **kwargs)
        except Exception as e:
            if attempt == max_retries:
                raise e
            jitter = random.uniform(0, 1.0)
            sleep_time = min(delay + jitter, max_delay)
            print(
                f"[!] Помилка Ollama Embeddings API: {e}. Спроба {attempt} із {max_retries}. Повтор через {sleep_time:.2f} сек..."
            )
            time.sleep(sleep_time)
            delay *= 2


def get_embedding(text: str) -> list[float]:
    def _make_call():
        response = embed(model="embeddinggemma:300m", input=text)
        return response["embeddings"][0]

    return call_ollama_with_retry(_make_call)


def run_vector_search():
    print(
        "[*] Ініціалізація векторної бази даних ChromaDB та генерація ембедингів через Ollama (embeddinggemma-2:440m)..."
    )
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="linux_kernel_docs")

    for idx, doc in enumerate(Path("docs").iterdir()):
        text = doc.read_text()
        emb = get_embedding(text)
        collection.upsert(ids=[f"doc_{idx}"], embeddings=[emb], documents=[text])

    print("[*] Виконання пошуку за ключовими словами")
    keyword_queries = ["spinlock_t", "kernel module is", "memory management is"]
    for q in keyword_queries:
        print(f"\n--- [Пошуковий запит]: {q} ---")

        keyword_results = [
            line
            for doc_f in Path("docs").iterdir()
            for line in doc_f.read_text().splitlines()
            if q in line.lower()
        ]
        print("\n--- Результати пошуку за ключовими словами ---")
        for r in keyword_results:
            print(f" - {r}")
        print("=" * 10)

    vector_queries = [
        "Які примітиви є для багатопроцесорності?",
        "spinlock_t",
        "memory management is",
    ]
    print("[*] Виконання векторного пошуку")
    for query in vector_queries:
        print(f"\n--- [Пошуковий запит]: '{query}' ---")

        query_emb = get_embedding(query)
        results = collection.query(query_embeddings=[query_emb], n_results=2)

        print("\n--- Результати векторного пошуку ---")
        for doc in results["documents"][0]:
            print(f" - {doc}")

        print("=" * 10)


if __name__ == "__main__":
    run_vector_search()
