import sys, os
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
import logging
from app.query import query_rag_system, conversation_history


def run_case(title, queries):
    print("\n" + "=" * 80)
    print(f"CASO: {title}")
    print("=" * 80)
    # Limpiar historial
    conversation_history.clear()
    for i, q in enumerate(queries, 1):
        print(f"\n[Q{i}] {q}")
        resp, sim, used_kb = query_rag_system.query_rag(q)
        print(f"[Resp{i}] sim={sim:.3f} used_kb={used_kb}")
        print(resp[:600] + ("..." if len(resp) > 600 else ""))
    print(f"\nHistorial (últimos {len(conversation_history)} mensajes):")
    for msg in conversation_history[-6:]:
        print(f"- {msg['role']}: {msg['content'][:120].replace('\n',' ')}")


def main():
    logging.basicConfig(level=logging.INFO)

    # Caso 1: Artículo específico seguido de pregunta ambigua
    run_case(
        "Seguimiento de artículo con pregunta ambigua",
        [
            "Explica en tus palabras el artículo 10 de la Ley 100 de 1993",
            "¿Y qué dice sobre la cobertura?",
        ],
    )

    # Caso 2: Referencia pronominal al artículo previo
    run_case(
        "Resolución de pronombres respecto al artículo previo",
        [
            "¿Qué establece el artículo 44 de la Ley 100 sobre seguridad social?",
            "¿Ese artículo aplica a trabajadores independientes?",
        ],
    )

    # Caso 3: Consulta general sobre la Ley seguida de objetivos
    run_case(
        "Contexto de ley y objetivos",
        [
            "¿Qué es la Ley 100 de 1993?",
            "¿Y cuáles son sus objetivos principales?",
        ],
    )


if __name__ == "__main__":
    main()