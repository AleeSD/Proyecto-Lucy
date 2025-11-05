"""Wrapper seguro para usar Hugging Face transformers si están disponibles"""

from typing import Any, Dict, Optional


class SafeHF:
    def __init__(self, task: str, model: Optional[str] = None):
        self.task = task
        self.model = model
        self._pipe = None
        try:
            from transformers import pipeline  # type: ignore
            self._pipe = pipeline(task=self.task, model=self.model) if self.model else pipeline(task=self.task)
        except Exception:
            self._pipe = None

    @property
    def available(self) -> bool:
        return self._pipe is not None

    def __call__(self, *args, **kwargs) -> Any:
        if self._pipe is None:
            return None
        return self._pipe(*args, **kwargs)