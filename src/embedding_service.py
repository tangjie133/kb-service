#!/usr/bin/env python3
"""Ollama embedding service"""

import requests
import time
from typing import List, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaEmbedding:
    """Ollama embedding client"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "nomic-embed-text"):
        self.host = host.rstrip('/')
        self.model = model
        self.embed_url = f"{self.host}/api/embeddings"
        self._check_connection()
    
    def _check_connection(self):
        """Check if Ollama is available"""
        try:
            response = requests.get(f"{self.host}/api/tags", timeout=5)
            if response.status_code == 200:
                models = response.json().get("models", [])
                model_names = [m["name"] for m in models]
                if self.model not in model_names:
                    logger.warning(f"Model {self.model} not found in Ollama. Run: ollama pull {self.model}")
                else:
                    logger.info(f"Ollama connected, model {self.model} available")
            else:
                logger.error(f"Ollama returned status {response.status_code}")
        except requests.exceptions.ConnectionError:
            logger.error(f"Cannot connect to Ollama at {self.host}")
            logger.info("Make sure Ollama is running: ollama serve")
        except Exception as e:
            logger.error(f"Error checking Ollama: {e}")
    
    def embed(self, text: str) -> Optional[List[float]]:
        """
        Embed single text
        """
        try:
            response = requests.post(
                self.embed_url,
                json={
                    "model": self.model,
                    "prompt": text
                },
                timeout=30
            )
            response.raise_for_status()
            result = response.json()
            return result.get("embedding")
            
        except Exception as e:
            logger.error(f"Embedding failed: {e}")
            return None
    
    def embed_batch(self, texts: List[str], delay: float = 0.1) -> List[List[float]]:
        """
        Embed multiple texts with rate limiting
        """
        embeddings = []
        
        for i, text in enumerate(texts):
            emb = self.embed(text)
            if emb:
                embeddings.append(emb)
            else:
                logger.warning(f"Failed to embed text {i}")
            
            # Rate limiting
            if i < len(texts) - 1:
                time.sleep(delay)
        
        return embeddings
    
    def embed_query(self, query: str) -> Optional[List[float]]:
        """
        Embed a query (may use different prompt)
        """
        # For now, same as regular embed
        return self.embed(query)
