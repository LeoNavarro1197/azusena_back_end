import os
import sys
import time
from typing import List, Tuple, Union

# Ensure app module is importable
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

from app.query import query_rag_system

Queries: List[str] = [
    "transparencia en la gestión hospitalaria",
    "tecnología biomédica en clínicas y su regulación",
    "principios del sistema de seguridad social",
    "financiamiento de EPS según la ley",
    "auditorías médicas obligatorias",
    "explicame con tus palabras el significado del artículo 1 de la ley 100 de 1993",
    "calidad en la atención de salud",
    "EPS y su régimen de financiamiento",
    "¿Qué opinas sobre la auditoría clínica?"
]


def print_result(idx: int, query: str, result: Union[str, Tuple[str, float, bool]]):
    print("=" * 80)
    print(f"[{idx}] Consulta: {query}")
    if isinstance(result, tuple):
        resp, similarity, kb_used = result
        print(f"- Similaridad: {similarity:.3f}")
        print(f"- KB utilizada: {kb_used}")
        print("- Respuesta:\n")
        print(resp)
    else:
        print("- Respuesta:\n")
        print(result)
    print("=" * 80)


def run_tests(queries: List[str]):
    ok = 0
    err = 0
    kb_count = 0
    sims = []

    start = time.time()
    for i, q in enumerate(queries, 1):
        try:
            result = query_rag_system.query_rag(q)
            print_result(i, q, result)
            if isinstance(result, tuple):
                _, sim, kb = result
                sims.append(sim)
                kb_count += 1 if kb else 0
            ok += 1
        except Exception as e:
            err += 1
            print(f"[ERROR] Consulta '{q}' fallo: {e}")
    elapsed = time.time() - start

    print("\nResumen:")
    print(f"- Total: {len(queries)}")
    print(f"- OK: {ok}")
    print(f"- Error: {err}")
    print(f"- KB usada: {kb_count}")
    if sims:
        print(f"- Similaridad promedio (donde aplica): {sum(sims)/len(sims):.3f}")
    print(f"- Tiempo total: {elapsed:.2f}s")


if __name__ == "__main__":
    run_tests(Queries)