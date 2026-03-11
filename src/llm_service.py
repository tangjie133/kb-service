#!/usr/bin/env python3
"""Ollama LLM service for generating responses"""

import requests
from typing import List, Dict, Optional
import logging

logger = logging.getLogger(__name__)


class OllamaLLM:
    """Ollama LLM client"""
    
    def __init__(self, host: str = "http://localhost:11434", model: str = "qwen2.5"):
        self.host = host.rstrip('/')
        self.model = model
        self.generate_url = f"{self.host}/api/generate"
    
    def generate(
        self, 
        query: str, 
        context: List[Dict],
        system_prompt: Optional[str] = None,
        stream: bool = False
    ) -> str:
        """
        Generate response based on query and retrieved context
        """
        # Build prompt with context
        prompt = self._build_prompt(query, context)
        
        # Default system prompt
        if not system_prompt:
            system_prompt = """你是一个技术支持助手。基于提供的知识库内容回答用户问题。
如果知识库中没有相关信息，请明确说明。
回答要简洁、准确、有帮助。"""
        
        try:
            # Combine system prompt and user prompt
            full_prompt = f"{system_prompt}\n\n{prompt}"
            
            response = requests.post(
                self.generate_url,
                json={
                    "model": self.model,
                    "prompt": full_prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.3,
                        "num_predict": 2048
                    }
                },
                timeout=120
            )
            response.raise_for_status()
            
            result = response.json()
            return result.get("response", "")
            
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return f"抱歉，生成回复时出错: {e}"
    
    def _build_prompt(self, query: str, context: List[Dict]) -> str:
        """
        Build prompt with retrieved context
        """
        prompt_parts = [
            "基于以下知识库内容回答问题：\n",
            "=" * 50
        ]
        
        for i, ctx in enumerate(context, 1):
            meta = ctx.get("metadata", {})
            source = meta.get("source_file", "未知来源")
            title = meta.get("title", "无标题")
            
            prompt_parts.extend([
                f"\n[参考 {i}]",
                f"来源: {source}",
                f"标题: {title}",
                f"内容:\n{ctx['content']}\n"
            ])
        
        prompt_parts.extend([
            "=" * 50,
            f"\n用户问题: {query}\n",
            "请基于以上知识库内容回答。如果知识库中没有答案，请明确说明。"
        ])
        
        return "\n".join(prompt_parts)
    
    def generate_simple(self, prompt: str) -> str:
        """
        Simple generation without context
        """
        try:
            response = requests.post(
                self.generate_url,
                json={
                    "model": self.model,
                    "prompt": prompt,
                    "stream": False
                },
                timeout=60
            )
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Simple generation failed: {e}")
            return ""
