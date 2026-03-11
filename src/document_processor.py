#!/usr/bin/env python3
"""Document processing and chunking"""

import re
from typing import List, Dict, Optional
from dataclasses import dataclass
from pathlib import Path
import yaml


@dataclass
class DocumentChunk:
    """Document chunk with metadata"""
    id: str
    content: str
    metadata: Dict
    source_file: str
    start_line: int
    end_line: int


class DocumentProcessor:
    """Process markdown documents into chunks"""
    
    def __init__(self, chunk_size: int = 500, chunk_overlap: int = 50):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
    
    def process_file(self, file_path: Path) -> List[DocumentChunk]:
        """
        Process a single markdown file
        """
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Extract metadata
            metadata = self._extract_metadata(content)
            metadata['filename'] = file_path.name
            
            # Remove metadata section for chunking
            body = self._remove_metadata(content)
            
            # Split into chunks
            chunks = self._split_text(body)
            
            # Create DocumentChunk objects
            doc_chunks = []
            for i, chunk_content in enumerate(chunks):
                chunk_id = f"{file_path.stem}_{i}"
                
                # Calculate line numbers
                start_pos = body.find(chunk_content)
                start_line = body[:start_pos].count('\n') + 1
                end_line = start_line + chunk_content.count('\n')
                
                doc_chunks.append(DocumentChunk(
                    id=chunk_id,
                    content=chunk_content.strip(),
                    metadata=metadata.copy(),
                    source_file=str(file_path),
                    start_line=start_line,
                    end_line=end_line
                ))
            
            return doc_chunks
            
        except Exception as e:
            print(f"Error processing {file_path}: {e}")
            return []
    
    def _extract_metadata(self, content: str) -> Dict:
        """Extract YAML frontmatter and other metadata"""
        metadata = {}
        
        # YAML frontmatter
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                try:
                    metadata = yaml.safe_load(parts[1]) or {}
                    # Remove frontmatter from content tracking
                except yaml.YAMLError:
                    pass
        
        # Extract title from first H1
        title_match = re.search(r'^# (.+)$', content, re.MULTILINE)
        if title_match and 'title' not in metadata:
            metadata['title'] = title_match.group(1).strip()
        
        # Extract tags
        tags_match = re.search(r'[Tt]ags?:\s*\[?([^\]]+)\]?', content)
        if tags_match:
            tags_str = tags_match.group(1)
            metadata['tags'] = [t.strip() for t in tags_str.split(',')]
        
        # Extract category from path
        # e.g., hardware/sensor.md -> category: hardware
        
        return metadata
    
    def _remove_metadata(self, content: str) -> str:
        """Remove YAML frontmatter from content"""
        if content.startswith('---'):
            parts = content.split('---', 2)
            if len(parts) >= 3:
                return parts[2].strip()
        return content
    
    def _split_text(self, text: str) -> List[str]:
        """
        Split text into overlapping chunks
        Strategy: Split by paragraphs, then combine
        """
        # Split by double newlines (paragraphs)
        paragraphs = re.split(r'\n\n+', text)
        paragraphs = [p.strip() for p in paragraphs if p.strip()]
        
        if not paragraphs:
            return []
        
        chunks = []
        current_chunk = []
        current_length = 0
        
        for para in paragraphs:
            para_length = len(para)
            
            # If adding this paragraph exceeds chunk size
            if current_length + para_length > self.chunk_size and current_chunk:
                # Save current chunk
                chunks.append('\n\n'.join(current_chunk))
                
                # Keep overlap
                overlap_chunks = []
                overlap_length = 0
                for p in reversed(current_chunk):
                    if overlap_length + len(p) > self.chunk_overlap:
                        break
                    overlap_chunks.insert(0, p)
                    overlap_length += len(p)
                
                current_chunk = overlap_chunks + [para]
                current_length = overlap_length + para_length
            else:
                current_chunk.append(para)
                current_length += para_length + 2  # +2 for \n\n
        
        # Don't forget the last chunk
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        return chunks
