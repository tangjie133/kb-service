#!/usr/bin/env python3
"""KB Service FastAPI application"""

import asyncio
import logging
from contextlib import asynccontextmanager
from typing import List, Optional

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from config import settings
from github_sync import GitHubSync
from document_processor import DocumentProcessor
from embedding_service import OllamaEmbedding
from vector_store import VectorStore
from llm_service import OllamaLLM

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Global components
sync: GitHubSync = None
processor: DocumentProcessor = None
embedder: OllamaEmbedding = None
vector_store: VectorStore = None
llm: OllamaLLM = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager"""
    global sync, processor, embedder, vector_store, llm
    
    logger.info("Initializing KB Service...")
    
    # Initialize components
    sync = GitHubSync(
        settings.GITHUB_REPO,
        "./knowledge",
        settings.GITHUB_TOKEN
    )
    
    processor = DocumentProcessor(
        chunk_size=settings.CHUNK_SIZE,
        chunk_overlap=settings.CHUNK_OVERLAP
    )
    
    embedder = OllamaEmbedding(
        host=settings.OLLAMA_HOST,
        model=settings.EMBEDDING_MODEL
    )
    
    vector_store = VectorStore(
        persist_path=settings.VECTOR_DB_PATH,
        collection_name=settings.COLLECTION_NAME
    )
    
    llm = OllamaLLM(
        host=settings.OLLAMA_HOST,
        model=settings.LLM_MODEL
    )
    
    # Initial sync
    logger.info("Performing initial sync...")
    await asyncio.to_thread(initial_sync)
    
    # Start background sync
    sync.start_watch(on_files_changed, settings.SYNC_INTERVAL)
    
    logger.info("KB Service ready!")
    
    yield
    
    # Cleanup
    logger.info("Shutting down...")


def initial_sync():
    """Initial sync and processing"""
    changed = sync.sync()
    if changed or vector_store.get_stats()["total_documents"] == 0:
        process_all_files()


def on_files_changed(changed_files: List):
    """Callback when files change"""
    logger.info(f"Processing {len(changed_files)} changed files...")
    for file_path in changed_files:
        process_file(file_path)


def process_file(file_path):
    """Process a single file"""
    try:
        # Delete old chunks
        vector_store.delete_by_source(str(file_path))
        
        # Process new chunks
        chunks = processor.process_file(file_path)
        if not chunks:
            return
        
        # Generate embeddings
        texts = [c.content for c in chunks]
        embeddings = embedder.embed_batch(texts)
        
        if embeddings:
            # Store
            vector_store.add_documents(chunks, embeddings)
            logger.info(f"Processed {file_path}: {len(chunks)} chunks")
        
    except Exception as e:
        logger.error(f"Error processing {file_path}: {e}")


def process_all_files():
    """Process all knowledge files"""
    files = sync.get_knowledge_files()
    logger.info(f"Processing {len(files)} files...")
    
    for file_path in files:
        process_file(file_path)
    
    logger.info("All files processed")


# FastAPI app
app = FastAPI(
    title="Knowledge Base Service",
    description="RAG-based knowledge retrieval service with Ollama",
    version="1.0.0",
    lifespan=lifespan
)


# Pydantic models
class QueryRequest(BaseModel):
    query: str = Field(..., description="User query")
    top_k: int = Field(default=5, ge=1, le=20, description="Number of results")
    generate_answer: bool = Field(default=True, description="Generate LLM answer")


class QueryResult(BaseModel):
    id: str
    content: str
    source_file: str
    similarity: float
    metadata: dict


class QueryResponse(BaseModel):
    query: str
    results: List[QueryResult]
    answer: Optional[str] = None
    stats: dict


class SyncResponse(BaseModel):
    status: str
    updated_files: int
    message: str


# API endpoints
@app.post("/query", response_model=QueryResponse)
async def query(request: QueryRequest):
    """
    Query knowledge base
    """
    try:
        # Embed query
        query_emb = await asyncio.to_thread(embedder.embed, request.query)
        
        if not query_emb:
            raise HTTPException(status_code=500, detail="Failed to embed query")
        
        # Search
        results = await asyncio.to_thread(
            vector_store.search,
            query_emb,
            top_k=request.top_k,
            threshold=settings.SIMILARITY_THRESHOLD
        )
        
        # Format results
        formatted_results = [
            QueryResult(
                id=r["id"],
                content=r["content"],
                source_file=r["metadata"].get("source_file", "unknown"),
                similarity=r["similarity"],
                metadata=r["metadata"]
            )
            for r in results
        ]
        
        # Generate answer if requested
        answer = None
        if request.generate_answer and results:
            answer = await asyncio.to_thread(
                llm.generate,
                request.query,
                results
            )
        
        return QueryResponse(
            query=request.query,
            results=formatted_results,
            answer=answer,
            stats={
                "total_documents": vector_store.get_stats()["total_documents"],
                "results_found": len(results)
            }
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Query failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/sync", response_model=SyncResponse)
async def trigger_sync():
    """
    Manually trigger sync
    """
    try:
        changed = await asyncio.to_thread(sync.sync)
        
        if changed:
            for file_path in changed:
                await asyncio.to_thread(process_file, file_path)
        
        return SyncResponse(
            status="success",
            updated_files=len(changed),
            message=f"Synced {len(changed)} files"
        )
        
    except Exception as e:
        logger.error(f"Sync failed: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/health")
async def health():
    """
    Health check
    """
    return {
        "status": "ok",
        "vector_db": vector_store.get_stats(),
        "github_repo": settings.GITHUB_REPO
    }


@app.get("/stats")
async def stats():
    """
    Service statistics
    """
    return {
        "vector_db": vector_store.get_stats(),
        "github_repo": settings.GITHUB_REPO,
        "ollama_host": settings.OLLAMA_HOST,
        "embedding_model": settings.EMBEDDING_MODEL,
        "llm_model": settings.LLM_MODEL
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=settings.API_HOST,
        port=settings.API_PORT
    )
