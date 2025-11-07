from typing import List, Optional

import numpy as np


class SafeEmbeddings:
    """
    Proveedor de embeddings seguro:
    - Intenta usar `sentence-transformers` si está disponible y configurado.
    - Fallback a TF-IDF simple basado en corpus observado.
    """

    def __init__(self, model_name: Optional[str] = None):
        self.model_name = model_name
        self._st_model = None
        self._tfidf = None
        self._vocabulary_built = False

        # Intentar cargar sentence-transformers
        if self.model_name:
            try:
                from sentence_transformers import SentenceTransformer
                self._st_model = SentenceTransformer(self.model_name)
            except Exception:
                self._st_model = None

        if self._st_model is None:
            # Preparar TF-IDF si no hay modelo de ST
            try:
                from sklearn.feature_extraction.text import TfidfVectorizer
                self._tfidf = TfidfVectorizer(max_features=2048)
            except Exception:
                self._tfidf = None

    @property
    def available(self) -> bool:
        return self._st_model is not None or self._tfidf is not None

    def encode_text(self, text: str) -> np.ndarray:
        if self._st_model is not None:
            vec = self._st_model.encode([text])
            return np.array(vec[0], dtype=float)
        # Fallback TF-IDF: si no hay vocabulario, crear mínimo
        if self._tfidf is None:
            return np.zeros((1,), dtype=float)
        if not self._vocabulary_built:
            # Construir vocabulario mínimo con el texto
            self._tfidf.fit([text])
            self._vocabulary_built = True
        vec = self._tfidf.transform([text]).toarray()[0]
        return np.array(vec, dtype=float)

    def fit_corpus(self, texts: List[str]) -> None:
        if self._st_model is not None:
            # Sentence-Transformers no requiere fit
            return
        if self._tfidf is not None:
            try:
                self._tfidf.fit(texts)
                self._vocabulary_built = True
            except Exception:
                # Ignorar errores de fitting
                pass

    def encode_corpus(self, texts: List[str]) -> np.ndarray:
        if self._st_model is not None:
            vecs = self._st_model.encode(texts)
            return np.array(vecs, dtype=float)
        if self._tfidf is None:
            return np.zeros((len(texts), 1), dtype=float)
        if not self._vocabulary_built:
            self.fit_corpus(texts)
        mat = self._tfidf.transform(texts).toarray()
        return np.array(mat, dtype=float)