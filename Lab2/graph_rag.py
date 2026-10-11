import json
import os
import time
import random
from pathlib import Path

import community as community_louvain
import networkx as nx
from ollama import chat
from pyvis.network import Network

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
                f"[!] Помилка LLM у GraphRAG (Ollama): {e}. Спроба {attempt} із {max_retries}. Повтор через {sleep_time:.2f} сек..."
            )
            time.sleep(sleep_time)
            delay *= 2


def get_embedding(text):
    def _make_call():
        response = embed(model="embeddinggemma:300m", input=text)
        return response["embeddings"][0]

    return call_ollama_with_retry(_make_call)


def visualize_graph(G, partition, output_filename="graph_visualization.html"):
    """Функція візуалізації графа знань та спільнот за допомогою PyVis"""
    print(f"[*] Генерація інтерактивної візуалізації графа ({output_filename})...")

    net = Network(
        directed=False,
        height="800px",
        width="100%",
        bgcolor="#f8f9fa",
        font_color="#2d3436",
    )

    net.barnes_hut(gravity=-2000, central_gravity=0.3, spring_length=150)
    net.show_buttons(filter_=["physics"])

    # Палітра кольорів для виявлених спільнот
    community_colors = [
        "#e74c3c",
        "#3498db",
        "#2ecc71",
        "#f1c40f",
        "#9b59b6",
        "#1abc9c",
        "#e67e22",
        "#34495e",
        "#d35400",
    ]

    # Додавання вузлів з урахуванням спільнот
    for node in G.nodes():
        comm_id = partition.get(node, 0)
        color = community_colors[comm_id % len(community_colors)]
        net.add_node(
            node,
            label=node,
            title=f"Сутність: {node} (Спільнота #{comm_id})",
            color=color,
            shape="dot",
            size=20,
        )

    # Додавання ребер (зв'язків) із додатковим описом у підказках
    for u, v, data in G.edges(data=True):
        rel = data.get("relation", "")
        desc = data.get("description", "")
        net.add_edge(
            u,
            v,
            label=rel,
            title=f"Зв'язок: {rel}\nКонтекст: {desc}",
            color="#b2bec3",
            arrowStrikethrough=False,
        )

    net.show(output_filename, notebook=False)
    print(f"[+] Візуалізацію успішно збережено у файл: {output_filename}")


def run_graph_rag():
    print("[*] === Побудова графа знань та виконання GraphRAG через Ollama (gemma4:e4b)... ===")

    if not os.path.exists("facts.json"):
        print("[!] Файл facts.json не знайдено. Спочатку запустіть extract.py.")
        return

    with open("facts.json", "r", encoding="utf-8") as f:
        data = json.load(f)

    facts = data.get("facts", [])

    G = nx.Graph()
    print(f"DEBUG: len(facts)={len(facts)}")
    for fact in facts:
        subj = fact.get("subject")
        obj = fact.get("object")
        rel = fact.get("relation")
        desc = fact.get("description")
        if subj and obj:
            G.add_edge(subj, obj, relation=rel, description=desc)

    print(
        f"[+] Граф побудовано: Вузлів = {G.number_of_nodes()}, Ребер = {G.number_of_edges()}"
    )

    # Виявлення спільнот за алгоритмом Лувена
    partition = community_louvain.best_partition(G)
    communities = {}
    for node, comm_id in partition.items():
        communities.setdefault(comm_id, []).append(node)

    print(f"[+] Виявлено спільнот: {len(communities)}")

    # Візуалізація графа (викликаємо щойно додану функцію)
    visualize_graph(G, partition, output_filename="graph_visualization.html")

    community_summaries = []
    for comm_id, nodes in communities.items():
        subgraph_edges = []
        for u, v, data_edge in G.subgraph(nodes).edges(data=True):
            subgraph_edges.append(
                f"{u} -[{data_edge.get('relation')}]-> {v} ({data_edge.get('description')})"
            )

        prompt = (
            f"Заборонено писати процес міркувань, внутрішні думки чи роздуми. Видавай лише фінальний результат або відповідь. "
            f"Зроби стисле резюме наступної спільноти сутностей у графі знань документації про ядро Linux:\n"
            f"Сутності: {', '.join(nodes)}\n"
            f"Зв'язки:\n" + "\n".join(subgraph_edges)
        )

        def _make_summary_call():
            response = chat(
                model="gemma4:e4b",
                messages=[{"role": "user", "content": prompt}],
                options={"temperature": 0.1, "num_predict": 128000},
            )
            return response.message.content

        summary_text = call_ollama_with_retry(_make_summary_call)
        community_summaries.append(f"Спільнота {comm_id}: {summary_text}")

    global_question = "Які ключові сутності та технології задіяні в роботі Linux і як вони пов'язані між собою?"

    map_reduce_prompt = (
        f"Глобальне запитання: {global_question}\n\n"
        "На основі резюме спільнот графа знань нижче сформуй узагальнену, повну та структуровану відповідь:\n"
        + "\n".join(community_summaries)
    )

    def _make_final_call():
        response = chat(
            model="gemma4:e4b",
            messages=[{"role": "user", "content": map_reduce_prompt}],
            options={"num_predict": 128000},
        )
        return response.message.content

    final_text = call_ollama_with_retry(_make_final_call)

    with open("graph_summary.md", "w", encoding="utf-8") as summary_file:
        summary_file.write(final_text)

    print("\n[+] Фінальну відповідь збережено у файл graph_summary.md")


def run_vector_rag():
    print("[*] === Виконання VectorRAG... ===")
    print(
        "[*] Ініціалізація векторної бази даних ChromaDB та генерація ембедингів через Ollama (embeddinggemma:300m)..."
    )
    chroma_client = chromadb.Client()
    collection = chroma_client.get_or_create_collection(name="linux_kernel_docs")

    for idx, doc in enumerate(Path("docs").iterdir()):
        text = doc.read_text()
        emb = get_embedding(text)
        collection.upsert(ids=[f"doc_{idx}"], embeddings=[emb], documents=[text])

    query = "Які ключові сутності та технології задіяні в роботі Linux"
    query_emb = get_embedding(query)
    results = collection.query(query_embeddings=[query_emb], n_results=3)["documents"][0]
    question = f"Які ключові сутності та технології задіяні в роботі Linux і як вони пов'язані між собою? Дай відповідь на основі цих документів:\n{"\n----\n".join(results)}"

    def _make_final_call():
        response = chat(
            model="gemma4:e4b",
            messages=[{"role": "user", "content": question}],
            options={"num_predict": 128000},
        )
        return response.message.content

    final_text = call_ollama_with_retry(_make_final_call)

    with open("vector_summary.md", "w", encoding="utf-8") as summary_file:
        summary_file.write(final_text)

    print("\n[+] Фінальну відповідь збережено у файл vector_summary.md")


def run_rag():
    run_graph_rag()
    run_vector_rag()

if __name__ == "__main__":
    run_rag()
