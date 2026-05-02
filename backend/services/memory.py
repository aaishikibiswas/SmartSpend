import json
from datetime import datetime

class MemoryManager:
    def __init__(self):
        # Maps session_id -> list of message dicts
        self.sessions: dict[str, list[dict]] = {}

    def get_history(self, session_id: str, limit: int = 10) -> list[dict]:
        """Retrieve recent conversational history for a given session."""
        if session_id not in self.sessions:
            return []
        return self.sessions[session_id][-limit:]

    def add_message(self, session_id: str, role: str, content: str):
        if session_id not in self.sessions:
            self.sessions[session_id] = []
        
        self.sessions[session_id].append({
            "role": role,
            "content": content,
            "timestamp": datetime.utcnow().isoformat()
        })
        
        # Keep size reasonable to prevent out of memory issues
        if len(self.sessions[session_id]) > 50:
            self.sessions[session_id] = self.sessions[session_id][-50:]

# Global simple purely in-memory store instance
memory_store = MemoryManager()
