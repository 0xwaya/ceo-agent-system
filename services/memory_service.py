"""Opt-in local lexical memory; never mines source files or installs agent hooks."""

import hashlib
import json
import threading
from pathlib import Path
from uuid import uuid4


def scenario_key(owner, agent, scenario):
    context = {key: value for key, value in scenario.items() if key != "updated_at"}
    digest = hashlib.sha256(json.dumps(context, sort_keys=True).encode()).hexdigest()
    return hashlib.sha256(f"{owner}:{agent}:{digest}".encode()).hexdigest()


class MemoryService:
    def __init__(self, root):
        self.root = Path(root)
        self.lock = threading.RLock()

    def _collection(self, key):
        from mempalace.backends.sqlite_exact import SQLiteExactBackend

        self.root.mkdir(parents=True, mode=0o700, exist_ok=True)
        self.root.chmod(0o700)
        backend = SQLiteExactBackend()
        collection = backend.get_or_create_collection(str(self.root / key), "conversation")
        return backend, collection

    def remember(self, key, user, assistant):
        with self.lock:
            backend, collection = self._collection(key)
            try:
                # A constant storage vector is required by this backend. Retrieval
                # is lexical only; these are not semantic embeddings.
                collection.add(
                    ids=[uuid4().hex],
                    documents=[json.dumps({"user": user, "assistant": assistant})],
                    embeddings=[[1.0]],
                    metadatas=[{"wing": key, "room": "conversation", "hall": "exchanges"}],
                )
            finally:
                backend.close()

    def recall(self, key, query, max_chars=3000):
        if not (self.root / key).exists():
            return []
        with self.lock:
            backend, collection = self._collection(key)
            try:
                result = collection.lexical_search(query=query, n_results=3)
                texts = []
                remaining = max_chars
                for hit in result.hits:
                    if hit.score > 0 and len(hit.document) <= remaining:
                        texts.append(hit.document)
                        remaining -= len(hit.document)
                return texts
            finally:
                backend.close()

    def clear(self, key):
        if not (self.root / key).exists():
            return
        with self.lock:
            backend, collection = self._collection(key)
            try:
                records = collection.get()
                if records["ids"]:
                    collection.delete(ids=records["ids"])
            finally:
                backend.close()
