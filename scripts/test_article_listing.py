import sys, os
from pathlib import Path

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from app.query import query_rag_system

q = "¿Qué artículos hablan sobre peticiones en la Ley 100 de 1993?"
resp = query_rag_system.query_rag(q)

if isinstance(resp, tuple):
    print("RESP:")
    print(resp[0])
    print("\nSIM:", resp[1])
    print("USED_KB:", resp[2])
else:
    print("RESP:")
    print(resp)