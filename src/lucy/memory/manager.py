import re
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import numpy as np

from .embeddings import SafeEmbeddings
from .index import SklearnIndex


@dataclass
class MemoryEvent:
    id: int
    conversacion_id: str
    usuario_id: str
    timestamp: float
    contenido: str
    metadatos: Optional[Dict[str, Any]]


class MemoryManager:
    """
    Gestor de Memoria a Largo Plazo (simple, en memoria):
    - Inserta eventos con embeddings
    - Consulta por similitud top-k
    - Purga por conversación
    - Fallback cuando no hay embeddings avanzados
    """

    def __init__(self, config_manager):
        self.config_manager = config_manager
        self.config = config_manager.get_all()
        self._events: List[MemoryEvent] = []
        self._next_id = 1
        self._emb = SafeEmbeddings(model_name=(self.config.get('embeddings', {}) or {}).get('model'))
        self._index = SklearnIndex()
        self._vectors: List[np.ndarray] = []
        self._needs_rebuild = False

        # Parámetros
        self._enabled = (self.config.get('memory', {}) or {}).get('enabled', True)
        self._top_k_default = int((self.config.get('memory', {}) or {}).get('top_k', 5))
        self._mask_emails = bool((self.config.get('privacy', {}) or {}).get('mask_emails', False))

    def _mask_pii(self, text: str) -> str:
        if not self._mask_emails:
            return text
        # Enmascarado básico de correos
        return re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[email]", text)

    def add_event(self, conversacion_id: str, usuario_id: str, contenido: str, metadatos: Optional[Dict[str, Any]] = None) -> str:
        if not self._enabled:
            return "disabled"
        contenido_proc = self._mask_pii(contenido or "")
        ev = MemoryEvent(
            id=self._next_id,
            conversacion_id=str(conversacion_id or ""),
            usuario_id=str(usuario_id or ""),
            timestamp=time.time(),
            contenido=contenido_proc,
            metadatos=metadatos or {}
        )
        self._events.append(ev)
        self._next_id += 1

        # Actualizar embeddings
        try:
            # Ajustar vocabulario si usamos TF-IDF
            self._emb.fit_corpus([e.contenido for e in self._events])
            vec = self._emb.encode_text(ev.contenido)
        except Exception:
            vec = np.zeros((1,), dtype=float)
        self._vectors.append(vec)
        self._needs_rebuild = True

        return str(ev.id)

    def _rebuild_index(self) -> None:
        if not self._needs_rebuild:
            return
        if len(self._vectors) == 0:
            self._index.fit(np.zeros((0, 1), dtype=float), [])
            self._needs_rebuild = False
            return
        try:
            mat = self._pad_vectors(self._vectors)
            ids = [e.id for e in self._events]
            self._index.fit(mat, ids)
        finally:
            self._needs_rebuild = False

    def _pad_vectors(self, vectors: List[np.ndarray]) -> np.ndarray:
        # Asegurar misma dimensión para todos los vectores
        max_dim = max((v.shape[0] for v in vectors), default=1)
        padded = []
        for v in vectors:
            if v.shape[0] < max_dim:
                pad = np.zeros((max_dim - v.shape[0],), dtype=float)
                padded.append(np.concatenate([v, pad]))
            else:
                padded.append(v)
        return np.vstack(padded)

    def find_similar(self, query: str, top_k: Optional[int] = None, filtros: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        if not self._enabled:
            return []
        self._rebuild_index()
        k = int(top_k or self._top_k_default)
        try:
            q_vec = self._emb.encode_text(query or "")
        except Exception:
            q_vec = np.zeros((1,), dtype=float)
        results = self._index.search(q_vec, top_k=k)
        # Convertir a salida con metadatos
        out: List[Dict[str, Any]] = []
        for ev_id, score in results:
            ev = next((e for e in self._events if e.id == ev_id), None)
            if ev is None:
                continue
            # Filtros simples (conv_id)
            if filtros and "conv_id" in filtros and str(filtros["conv_id"]) != ev.conversacion_id:
                continue
            out.append({
                "id": ev.id,
                "contenido": ev.contenido,
                "score": round(float(score), 6),
                "timestamp": ev.timestamp,
                "conversacion_id": ev.conversacion_id,
                "usuario_id": ev.usuario_id,
                "metadatos": ev.metadatos or {}
            })
        return out

    def purge_conversation(self, conversacion_id: str) -> int:
        if not self._enabled:
            return 0
        before = len(self._events)
        # Filtrar eventos y vectores en conjunto
        zipped = list(zip(self._events, self._vectors))
        filtered = [(e, v) for (e, v) in zipped if e.conversacion_id != str(conversacion_id)]
        self._events = [e for (e, _) in filtered]
        self._vectors = [v for (_, v) in filtered]
        purged = before - len(self._events)
        self._needs_rebuild = True
        return purged

    def rebuild_index(self) -> None:
        self._needs_rebuild = True
        self._rebuild_index()

    def status(self) -> Dict[str, Any]:
        return {
            "enabled": self._enabled,
            "events": len(self._events),
            "provider": "sklearn",
            "embeddings": "sentence-transformers" if self._emb and self._emb._st_model is not None else "tfidf",
        }