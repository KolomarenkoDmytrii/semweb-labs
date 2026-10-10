import time
import random
from pathlib import Path

from ollama import embed
import chromadb

DOCUMENTS = [
    "У 2024 році компанія EcoCity Inc. розгорнула міську мережу датчиків на базі IoT у Києві. Система контролює якість повітря в реальному часі. Головний інженер проєкту, Андрій Мельник, зазначив, що платформа працює на протоколі LoRaWAN.",
    "Протокол LoRaWAN забезпечує енергоефективний зв'язок на великих відстанях. EcoCity Inc. співпрацює з університетом КПІ для аналізу великих масивів даних за допомогою нейромереж.",
    "У Львові аналогічний проєкт реалізує стартап SmartEco, використовуючи обладнання від Cisco. Андрій Мельник раніше консультував SmartEco щодо архітектури мереж у 2022 році.",
    "Мережі IoT генерують терабайти даних. Для їх обробки у Києві та Львові застосовують хмарні сервіси Amazon Web Services (AWS). AWS забезпечує високу масштабованість та безпеку.",
    "Університет КПІ підписав меморандум з AWS про підготовку фахівців з хмарних технологій та штучного інтелекту у 2023 році. Координатором програми став професор Іван Ковальчук.",
    "Системи моніторингу повітря безпосередньо впливають на зниження рівня захворюваності дихальних шляхів, що підтверджено дослідженнями медичного центру у Львові.",
    "Cisco та EcoCity Inc. спільно розробляють нові стандарти безпеки для IoT-пристроїв. Технічний директор Cisco, Олена Шевченко, підкреслила важливість шифрування даних.",
    "Розвиток Smart City ініціатив в Україні фінансується міжнародними фондами, зокрема Європейським банком реконструкції та розвитку (ЄБРР), який підтримав проєкти у Києві у 2023 році.",
]


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

    query = "For what spinlock_t is used?"
    print(f"\n[Пошуковий запит]: {query}")

    keyword_results = [
        line
        for doc_f in Path("docs").iterdir()
        for line in doc_f.read_text().splitlines()
        if "spinlock_t" in line or "spinlock" in line.lower()
    ]
    print("\n--- Результати Keyword-пошуку ---")
    for r in keyword_results:
        print(f" - {r}")

    query = "Які примітиви є для багатопроцесорності?"
    print(f"\n[Пошуковий запит]: {query}")
    query_emb = get_embedding(query)
    results = collection.query(query_embeddings=[query_emb], n_results=2)
    print("\n--- Результати Векторного (Семантичного) пошуку ---")
    for doc in results["documents"][0]:
        print(f" - {doc}")


if __name__ == "__main__":
    run_vector_search()
