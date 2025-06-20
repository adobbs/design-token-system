from datetime import datetime
from typing import Dict, List, Any, Set
from fastapi import Request

class UpdateBroadcaster:
    """Broadcasting system for token updates via Server-Sent Events"""
    
    def __init__(self):
        # SSE connections - store as Request objects
        self.sse_connections: Set[Request] = set()
        
        # Track update history for clients that reconnect
        self.update_history: List[Dict[str, Any]] = []
        self.max_history_size = 100
        
        # Current version/hash for quick comparison
        self.current_version = 1
        self.current_hash = None
    
    def add_sse_connection(self, request: Request):
        """Add an SSE connection"""
        self.sse_connections.add(request)
        print(f"📡 SSE client connected. Total: {len(self.sse_connections)}")
    
    def remove_sse_connection(self, request: Request):
        """Remove an SSE connection"""
        self.sse_connections.discard(request)
        print(f"📡 SSE client disconnected. Total: {len(self.sse_connections)}")
    
    async def broadcast_token_update(self, changed_paths: List[str], new_values: Dict[str, Any], tokens_hash: str):
        """Broadcast token updates via SSE"""
        self.current_version += 1
        self.current_hash = tokens_hash
        
        update_data = {
            "type": "TOKEN_UPDATE",
            "version": self.current_version,
            "hash": tokens_hash,
            "data": {
                "changed_paths": changed_paths,
                "new_values": new_values
            },
            "timestamp": datetime.now().isoformat()
        }
        
        # Add to history for reconnecting clients
        self._add_to_history(update_data)
        
        # Broadcast to SSE clients
        await self._broadcast_sse(update_data)
        
        print(f"📡 Update broadcasted to {len(self.sse_connections)} SSE clients")
        print(f"   Changed paths: {changed_paths}")
    
    async def _broadcast_sse(self, update_data: Dict[str, Any]):
        """Send update to all SSE connections"""
        if not self.sse_connections:
            print("📡 No SSE clients to notify")
            return
        
        # Store the message to be sent by SSE generators
        self._latest_update = update_data
        
        # Note: Actual SSE message sending happens in the SSE endpoint generator
        # This method just stores the update and marks connections for cleanup
        
        # Check for disconnected clients
        disconnected = []
        for request in self.sse_connections.copy():
            try:
                if await request.is_disconnected():
                    disconnected.append(request)
            except Exception:
                disconnected.append(request)
        
        # Clean up disconnected clients
        for request in disconnected:
            self.remove_sse_connection(request)
    
    def get_latest_update(self):
        """Get the latest update for SSE generators"""
        return getattr(self, '_latest_update', None)
    
    def clear_latest_update(self):
        """Clear the latest update after it's been sent"""
        if hasattr(self, '_latest_update'):
            delattr(self, '_latest_update')
    
    def _add_to_history(self, update_data: Dict[str, Any]):
        """Add update to history for reconnecting clients"""
        self.update_history.append(update_data)
        
        # Trim history if too large
        if len(self.update_history) > self.max_history_size:
            self.update_history = self.update_history[-self.max_history_size:]
    
    def get_updates_since_version(self, since_version: int) -> List[Dict[str, Any]]:
        """Get all updates since a specific version"""
        return [
            update for update in self.update_history 
            if update.get("version", 0) > since_version
        ]
    
    def get_updates_since_hash(self, client_hash: str) -> List[Dict[str, Any]]:
        """Get updates since a specific hash (if client is out of sync)"""
        if client_hash == self.current_hash:
            return []  # Client is up to date
        
        # If hash doesn't match, return recent updates
        return self.update_history[-10:] if self.update_history else []
    
    def get_current_status(self) -> Dict[str, Any]:
        """Get current broadcasting status"""
        return {
            "current_version": self.current_version,
            "current_hash": self.current_hash,
            "sse_clients": len(self.sse_connections),
            "update_history_size": len(self.update_history),
            "last_update": self.update_history[-1]["timestamp"] if self.update_history else None
        }

# Global broadcaster instance
broadcaster = UpdateBroadcaster()