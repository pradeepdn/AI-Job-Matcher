"""
services/embeddings.py
───────────────────────
Thin wrapper around sentence-transformers for encoding text into embedding vectors.

Usage:
    svc = EmbeddingService()
    vec  = svc.encode("Python developer with FastAPI experience")
    vecs = svc.encode_batch(["job 1 description", "job 2 description"])
"""

from __future__ import annotations

import logging
from typing import List, Union

import numpy as np

import config

logger = logging.getLogger(__name__)


class EmbeddingService:
    """
    Encodes text into dense embedding vectors using a sentence-transformers model.

    The model is loaded lazily on first use to avoid slowing down app startup.
    """

    def __init__(self, model_name: str | None = None) -> None:
        self.model_name = model_name or config.EMBEDDING_MODEL
        self._model = None  # lazy-loaded

    @property
    def model(self):
        """Lazy-load the sentence-transformers model."""
        if self._model is None:
            logger.info("Loading embedding model: %s", self.model_name)
            try:
                from sentence_transformers import SentenceTransformer
            except ImportError as exc:
                raise ImportError(
                    "sentence-transformers is required. Run: pip install sentence-transformers"
                ) from exc
            self._model = SentenceTransformer(self.model_name)
            logger.info("Embedding model loaded successfully.")
        return self._model

    def encode(self, text: str) -> np.ndarray:
        """
        Encode a single text string into an embedding vector.

        Args:
            text: Input text to encode.

        Returns:
            1-D numpy array of floats (embedding vector).
        """
        if not text or not text.strip():
            raise ValueError("Cannot encode empty or whitespace-only text.")
        vec = self.model.encode(text, convert_to_numpy=True, normalize_embeddings=True)
        return vec

    def encode_batch(self, texts: List[str], batch_size: int = 32) -> np.ndarray:
        """
        Encode a list of texts into an embedding matrix.

        Args:
            texts: List of input texts.
            batch_size: Number of texts to process in each forward pass.

        Returns:
            2-D numpy array of shape (len(texts), embedding_dim).
        """
        if not texts:
            raise ValueError("texts list must not be empty.")

        logger.info("Encoding %d texts with batch_size=%d", len(texts), batch_size)
        matrix = self.model.encode(
            texts,
            batch_size=batch_size,
            convert_to_numpy=True,
            normalize_embeddings=True,
            show_progress_bar=len(texts) > 20,
        )
        return matrix
