#!/usr/bin/env python3
"""ChromaDB vector storage"""

import chromadb
from chromadb.config import Settings
from typing import List, Dict, Optional
from .document_processor import DocumentChunk
import logging

logger = logging.getLogger(__name__)


class VectorStore:
    """ChromaDB vector store for document chunks"""
    
    def __init__(self, persist_path: str, collection_name: str = "knowledge"):
        self.persist_path = persist_path
        
        # Initialize ChromaDB
        self.client = chromadb.PersistentClient(
            path=persist_path,
            settings=Settings(
                anonymized_telemetry=False
            )
        )
        
        # Get or create collection
        self.collection = self.client.get_or_create_collection(
            name=collection_name,
            metadata={"hnsw:space": "cosine"}
        )
        
        logger.info(f"Vector store initialized: {collection_name}")
    
    def add_documents(self, chunks: List[DocumentChunk], embeddings: List[List[float]]):
        """
        Add documents to vector store
        """
        if not chunks or not embeddings:
            return
        
        if len(chunks) != len(embeddings):
            raise ValueError("Chunks and embeddings must have same length")
        
        ids = [c.id for c in chunks]
        documents = [c.content for c in chunks]
        
        # Prepare metadata
        metadatas = []
        for chunk in chunks:
            meta = {
                **chunk.metadata,
                "source_file": chunk.source_file,
                "start_line": chunk.start_line,
                "end_line": chunk.end_line
            }
            # Ensure all values are valid types for ChromaDB
            meta = self._clean_metadata(meta)
            metadatas.append(meta)
        
        # Add to collection
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=documents,
            metadatas=metadatas
        )
        
        logger.info(f"Added {len(chunks)} documents")
    
    def search(
        self, 
        query_embedding: List[float], 
        top_k: int = 5,
        threshold: float = 0.7
    ) -> List[Dict]:
        """
        Search similar documents
        """
        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=top_k,
            include=["documents", "metadatas", "distances"]
        )
        
        # Format results
        hits = []
        for i in range(len(results['ids'][0])):
            distance = results['distances'][0][i]
            similarity = 1 - distance  # Convert distance to similarity
            
            # Filter by threshold
            if similarity < threshold:
                continue
            
            hits.append({
                "id": results['ids'][0][i],
                "content": results['documents'][0][i],
                "metadata": results['metadatas'][0][i],
                "similarity": similarity
            })
        
        # Sort by similarity
        hits.sort(key=lambda x: x["similarity"], reverse=True)
        
        return hits
    
    def delete_by_source(self, source_file: str):
        """
        Delete all chunks from a source file
        """
        try:
            self.collection.delete(
                where={"source_file": source_file}
            )
            logger.info(f"Deleted documents from {source_file}")
        except Exception as e:
            logger.error(f"Delete failed: {e}")
    
    def get_stats(self) -> Dict:
        """
        Get collection statistics
        """
        count = self.collection.count()
        return {
            "total_documents": count
        }
    
    def _clean_metadata(self, metadata: Dict) -> Dict:
        """
        Clean metadata for ChromaDB (only str, int, float, bool)
        """
        cleaned = {}
        for key, value in metadata.items():
            if isinstance(value, (str, int, float, bool)):
                cleaned[key] = value
            elif isinstance(value, list):
                # Convert list to comma-separated string
                cleaned[key] = ", ".join(str(v) for v in value)
            else:
                cleaned[key] = str(value)
        return cleaned
