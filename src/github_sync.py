#!/usr/bin/env python3
"""GitHub repository sync module"""

import git
import shutil
from pathlib import Path
from typing import List, Optional, Callable
import logging
import time
import threading

logger = logging.getLogger(__name__)


class GitHubSync:
    """Sync knowledge base from GitHub"""
    
    def __init__(self, repo_url: str, local_path: str, token: Optional[str] = None):
        self.repo_url = repo_url
        self.local_path = Path(local_path)
        self.token = token
        
        # Add token to URL if provided
        if token and "github.com" in repo_url:
            self.repo_url = repo_url.replace(
                "https://github.com/",
                f"https://{token}@github.com/"
            )
    
    def sync(self) -> List[Path]:
        """
        Sync repository, return changed files
        """
        try:
            if self.local_path.exists():
                return self._pull()
            else:
                self._clone()
                # First clone, all markdown files are new
                return list(self.local_path.rglob("*.md"))
        except Exception as e:
            logger.error(f"Sync failed: {e}")
            return []
    
    def _clone(self):
        """Clone repository"""
        logger.info(f"Cloning {self.repo_url} to {self.local_path}")
        
        # Clean up if exists
        if self.local_path.exists():
            shutil.rmtree(self.local_path)
        
        self.local_path.parent.mkdir(parents=True, exist_ok=True)
        git.Repo.clone_from(self.repo_url, self.local_path)
        logger.info("Clone completed")
    
    def _pull(self) -> List[Path]:
        """Pull updates"""
        logger.info(f"Pulling updates from {self.repo_url}")
        
        repo = git.Repo(self.local_path)
        
        # Get current HEAD
        old_head = repo.head.commit.hexsha
        
        # Pull
        origin = repo.remotes.origin
        pull_info = origin.pull()
        
        # Get new HEAD
        new_head = repo.head.commit.hexsha
        
        # Check if changed
        if old_head == new_head:
            logger.info("No updates")
            return []
        
        # Get changed files
        changed = repo.git.diff("--name-only", old_head, new_head)
        changed_files = [
            self.local_path / f.strip()
            for f in changed.split("\n")
            if f.strip().endswith(".md")
        ]
        
        logger.info(f"Updated files: {len(changed_files)}")
        return changed_files
    
    def get_knowledge_files(self) -> List[Path]:
        """Get all markdown files"""
        if not self.local_path.exists():
            return []
        return list(self.local_path.rglob("*.md"))
    
    def start_watch(self, callback: Callable, interval: int = 300):
        """
        Start watching for changes in background thread
        """
        def watch_loop():
            while True:
                try:
                    changed = self.sync()
                    if changed:
                        callback(changed)
                except Exception as e:
                    logger.error(f"Watch error: {e}")
                
                time.sleep(interval)
        
        thread = threading.Thread(target=watch_loop, daemon=True)
        thread.start()
        logger.info(f"Started watching (interval: {interval}s)")
