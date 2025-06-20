# Token management API endpoints

from typing import Dict, Any, List
from fastapi import APIRouter, HTTPException, BackgroundTasks

from models.tokens import TokenUpdate, TokenBatchUpdate
from core.token_manager import token_manager

router = APIRouter()

@router.get("/", response_model=Dict[str, Any])
async def get_all_tokens():
    """Get all design tokens"""
    return await token_manager.load_tokens()

@router.get("/{token_path:path}")
async def get_token(token_path: str):
    """Get a specific token by path (e.g., 'color/semantic/primary')"""
    # Convert URL path to dot notation
    dot_path = token_path.replace('/', '.')
    return await token_manager.get_token_by_path(dot_path)

@router.put("/{token_path:path}")
async def update_token(token_path: str, update: TokenUpdate):
    """Update a specific token"""
    dot_path = token_path.replace('/', '.')
    
    return await token_manager.update_token(
        dot_path, 
        update.value, 
        update.type, 
        update.description
    )

@router.delete("/{token_path:path}")
async def delete_token(token_path: str):
    """Delete a specific token"""
    dot_path = token_path.replace('/', '.')
    return await token_manager.delete_token(dot_path)

@router.post("/batch")
async def batch_update_tokens(updates: TokenBatchUpdate):
    """Update multiple tokens at once"""
    results = []
    
    for update in updates.tokens:
        try:
            result = await token_manager.update_token(
                update.token_path,
                update.value,
                update.type,
                update.description
            )
            results.append({
                "success": True,
                "token_path": update.token_path,
                "result": result
            })
        except Exception as e:
            results.append({
                "success": False,
                "token_path": update.token_path,
                "error": str(e)
            })
    
    successful = len([r for r in results if r["success"]])
    
    return {
        "total_updates": len(updates.tokens),
        "successful": successful,
        "failed": len(results) - successful,
        "results": results
    }