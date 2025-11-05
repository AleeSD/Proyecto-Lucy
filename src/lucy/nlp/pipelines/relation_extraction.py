import re
from typing import List, Dict


def extract_relations(text: str) -> List[Dict[str, str]]:
    relations: List[Dict[str, str]] = []
    # Patrones simples español/inglés
    # "X trabaja en Y" / "X works at Y"
    patterns = [
        re.compile(r"\b([A-ZÁÉÍÓÚ][a-záéíóú]+)\s+[A-ZÁÉÍÓÚ][a-záéíóú]+\s+trabaja\s+en\s+([A-Z][A-Za-z]+)", re.UNICODE),
        re.compile(r"\b([A-Z][a-z]+)\s+[A-Z][a-z]+\s+works\s+at\s+([A-Z][A-Za-z]+)")
    ]
    for p in patterns:
        for m in p.finditer(text):
            relations.append({"subject": m.group(1), "relation": "employment", "object": m.group(2)})
    return relations