import json
import asyncio
from datetime import datetime
from typing import Optional
from fastapi import APIRouter, Request, Query
from sse_starlette import EventSourceResponse

from core.update_broadcaster import broadcaster
from core.token_manager import token_manager

router = APIRouter()

@router.get("/events")
async def stream_token_updates(
    request: Request,
    since_version: Optional[int] = Query(None, description="Get updates since this version"),
    client_hash: Optional[str] = Query(None, description="Client's current token hash")
):
    """
    Server-Sent Events endpoint for real-time token updates.
    
    More reliable than WebSockets for design token updates.
    Automatically handles reconnection and missed updates.
    """
    
    async def event_generator():
        # Add this client to SSE connections
        broadcaster.add_sse_connection(request)
        
        try:
            # Send initial connection confirmation
            yield {
                "event": "connected",
                "data": json.dumps({
                    "type": "CONNECTED",
                    "message": "Connected to design token updates via SSE",
                    "current_version": broadcaster.current_version,
                    "current_hash": broadcaster.current_hash,
                    "timestamp": datetime.now().isoformat()
                })
            }
            
            # If client provided version, send missed updates
            if since_version is not None:
                missed_updates = broadcaster.get_updates_since_version(since_version)
                if missed_updates:
                    yield {
                        "event": "missed-updates",
                        "data": json.dumps({
                            "type": "MISSED_UPDATES",
                            "count": len(missed_updates),
                            "updates": missed_updates
                        })
                    }
                    # Small delay between missed updates
                    await asyncio.sleep(0.1)
            
            # If client provided hash and it doesn't match, send recent updates
            elif client_hash and client_hash != broadcaster.current_hash:
                recent_updates = broadcaster.get_updates_since_hash(client_hash)
                if recent_updates:
                    yield {
                        "event": "sync-required",
                        "data": json.dumps({
                            "type": "SYNC_REQUIRED",
                            "message": "Client hash mismatch, syncing recent updates",
                            "updates": recent_updates
                        })
                    }
            
            # Send current status
            yield {
                "event": "status",
                "data": json.dumps({
                    "type": "STATUS",
                    "data": broadcaster.get_current_status()
                })
            }
            
            # Keep connection alive and send updates
            last_heartbeat = asyncio.get_event_loop().time()
            
            while True:
                if await request.is_disconnected():
                    break
                
                # Check for new updates
                latest_update = broadcaster.get_latest_update()
                if latest_update:
                    yield {
                        "event": "token-update",
                        "data": json.dumps(latest_update)
                    }
                    broadcaster.clear_latest_update()
                
                # Send periodic heartbeat (every 30 seconds)
                current_time = asyncio.get_event_loop().time()
                if current_time - last_heartbeat > 30:
                    yield {
                        "event": "heartbeat",
                        "data": json.dumps({
                            "type": "HEARTBEAT",
                            "timestamp": current_time,
                            "client_count": len(broadcaster.sse_connections)
                        })
                    }
                    last_heartbeat = current_time
                
                # Short sleep to prevent busy waiting
                await asyncio.sleep(1)
                
        except asyncio.CancelledError:
            # Client disconnected gracefully
            pass
        except Exception as e:
            print(f"❌ SSE error: {e}")
            try:
                yield {
                    "event": "error",
                    "data": json.dumps({
                        "type": "ERROR",
                        "message": str(e)
                    })
                }
            except:
                pass  # Connection likely closed
        finally:
            # Clean up connection
            broadcaster.remove_sse_connection(request)
    
    return EventSourceResponse(event_generator())

@router.get("/status")
async def get_sse_status():
    """Get SSE connection and update status"""
    return {
        "sse_clients": len(broadcaster.sse_connections),
        "current_status": broadcaster.get_current_status(),
        "token_metadata": token_manager.get_token_metadata()
    }

@router.get("/updates/since/{version}")
async def get_updates_since_version(version: int):
    """Get all updates since a specific version (HTTP fallback for polling)"""
    updates = broadcaster.get_updates_since_version(version)
    return {
        "since_version": version,
        "current_version": broadcaster.current_version,
        "updates_count": len(updates),
        "updates": updates,
        "needs_full_sync": len(updates) == 0 and version < broadcaster.current_version
    }

@router.get("/updates/sync")
async def sync_check(client_hash: Optional[str] = Query(None)):
    """Check if client needs to sync (HTTP fallback for polling)"""
    current_metadata = token_manager.get_token_metadata()
    
    response = {
        "current_version": broadcaster.current_version,
        "current_hash": broadcaster.current_hash,
        "server_metadata": current_metadata,
        "sync_needed": False,
        "updates": []
    }
    
    if client_hash and client_hash != broadcaster.current_hash:
        response["sync_needed"] = True
        response["updates"] = broadcaster.get_updates_since_hash(client_hash)
        
        # If no updates found but hash mismatch, full reload needed
        if not response["updates"]:
            response["full_reload_needed"] = True
    
    return response

@router.post("/polling/register")
async def register_polling_client(client_info: dict):
    """Register a polling client (for analytics/monitoring)"""
    # This is optional - helps track how many clients are using polling vs SSE
    return {
        "status": "registered",
        "polling_interval_seconds": 30,  # Recommended polling interval
        "fallback_endpoint": "/sse/updates/sync"
    }