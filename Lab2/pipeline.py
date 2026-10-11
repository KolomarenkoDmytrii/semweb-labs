import subprocess
import sys

from extract import extract_knowledge_to_file
from vector_search import run_vector_search
from graph_rag import run_graph_rag

# def run_script(script_name):
#     print(f"\n==============================")
#     print(f"[*] Запуск скрипта: {script_name}")
#     print(f"==============================")
#     result = subprocess.run([sys.executable, script_name])
#     if result.returncode != 0:
#         print(f"[!] Помилка під час виконання {script_name}")
#         sys.exit(result.returncode)

if __name__ == "__main__":
    print("=== ПОЧАТОК ВИКОНАННЯ ЛАБОРАТОРНОЇ РОБОТИ №02 ===")

    # 1. Екстракція фактів
    # run_script("extract.py")
    #print("=== 1. Екстракція фактів ===")
    extract_knowledge_to_file()

    # 2. Векторний пошук
    # run_script("vector_search.py")
    print("=== 2. Векторний пошук ===")
    run_vector_search()

    # 3. Граф знань та GraphRAG
    # run_script("graph_rag.py")
    print("=== 3. Граф знань та GraphRAG ===")
    run_graph_rag()

    print("\n=== УСПІШНО ЗАВЕРШЕНО ВСІ ЕТАПИ ПАЙПЛАЙНУ ===")
