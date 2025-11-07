from typing import List, Tuple

import numpy as np


class SklearnIndex:
    """
    Índice vectorial simple basado en `NearestNeighbors` (cosine).
    Se reconstruye cuando cambian los datos.
    """

    def __init__(self):
        self._vectors: np.ndarray = np.zeros((0, 1), dtype=float)
        self._ids: List[int] = []
        self._nn = None

    def fit(self, vectors: np.ndarray, ids: List[int]) -> None:
        self._vectors = vectors if vectors is not None else np.zeros((0, 1), dtype=float)
        self._ids = list(ids)
        try:
            from sklearn.neighbors import NearestNeighbors
            if self._vectors.shape[0] == 0:
                self._nn = None
                return
            # Normalizar para evitar problemas si TF-IDF produce vectores vacíos
            self._nn = NearestNeighbors(n_neighbors=min(len(self._ids), 5), metric='cosine')
            self._nn.fit(self._vectors)
        except Exception:
            self._nn = None

    def search(self, query_vec: np.ndarray, top_k: int = 5) -> List[Tuple[int, float]]:
        if self._nn is None or query_vec is None or query_vec.size == 0:
            return []
        q = query_vec.reshape(1, -1)
        try:
            distances, indices = self._nn.kneighbors(q, n_neighbors=min(top_k, len(self._ids)))
        except Exception:
            return []
        results: List[Tuple[int, float]] = []
        for dist, idx in zip(distances[0], indices[0]):
            ev_id = self._ids[int(idx)]
            similarity = float(1.0 - dist)
            results.append((ev_id, similarity))
        # Ordenar por similitud descendente
        results.sort(key=lambda x: x[1], reverse=True)
        return results