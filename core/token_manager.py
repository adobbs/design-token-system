import json
import hashlib
import asyncio
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, List, Tuple, Optional

from fastapi import HTTPException

from core.config import settings

class TokenManager:
    """Manages design token storage and updates"""
    
    def __init__(self):
        self.tokens_file = settings.TOKENS_DIR / "tokens.json"
        self.build_cache = {}
    
    async def load_tokens(self) -> Dict[str, Any]:
        """Load tokens from JSON file"""
        if not self.tokens_file.exists():
            # Create default tokens if file doesn't exist
            default_tokens = self._create_default_tokens()
            await self.save_tokens(default_tokens, notify_clients=False)
            return default_tokens
        
        try:
            with open(self.tokens_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except (json.JSONDecodeError, IOError) as e:
            raise HTTPException(
                status_code=500, 
                detail=f"Failed to load tokens: {str(e)}"
            )
    
    async def save_tokens(self, tokens: Dict[str, Any], notify_clients: bool = True) -> None:
        """Save tokens to JSON file and notify clients via all channels"""
        # Load previous tokens to detect changes
        old_tokens = {}
        if self.tokens_file.exists() and notify_clients:
            try:
                with open(self.tokens_file, 'r', encoding='utf-8') as f:
                    old_tokens = json.load(f)
            except Exception:
                pass  # If we can't load old tokens, treat everything as new
        
        # Add metadata
        if "$metadata" not in tokens:
            tokens["$metadata"] = {}
        
        tokens["$metadata"]["modified"] = datetime.now().isoformat()
        tokens["$metadata"]["version"] = tokens["$metadata"].get("version", 0) + 1
        
        # Calculate hash for change detection
        tokens_hash = self._calculate_tokens_hash(tokens)
        tokens["$metadata"]["hash"] = tokens_hash
        
        # Write to file
        try:
            with open(self.tokens_file, 'w', encoding='utf-8') as f:
                json.dump(tokens, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to save tokens: {str(e)}"
            )
        
        # Detect changes and notify clients via all channels
        if old_tokens and notify_clients:
            changed_paths, new_values = self._detect_token_changes(old_tokens, tokens)
            if changed_paths:
                # Import here to avoid circular import
                from core.update_broadcaster import broadcaster
                await broadcaster.broadcast_token_update(changed_paths, new_values, tokens_hash)
        
        # Invalidate build cache
        self.build_cache.clear()
        print(f"💾 Tokens saved to {self.tokens_file} (v{tokens['$metadata']['version']})")
    
    def _detect_token_changes(self, old_tokens: Dict[str, Any], new_tokens: Dict[str, Any]) -> Tuple[List[str], Dict[str, Any]]:
        """Detect which tokens have changed between versions"""
        changed_paths = []
        new_values = {}
        
        def compare_tokens(old_obj: Any, new_obj: Any, current_path: str = ""):
            if isinstance(new_obj, dict):
                if "$value" in new_obj:
                    # This is a token - compare values
                    old_value = None
                    if isinstance(old_obj, dict) and "$value" in old_obj:
                        old_value = old_obj["$value"]
                    
                    # Check if value changed
                    if old_value != new_obj["$value"]:
                        changed_paths.append(current_path)
                        new_values[current_path] = new_obj
                        print(f"🔄 Token changed: {current_path} = {new_obj['$value']}")
                else:
                    # Recurse into nested objects
                    for key, value in new_obj.items():
                        if not key.startswith("$"):  # Skip metadata
                            new_path = f"{current_path}.{key}" if current_path else key
                            old_child = old_obj.get(key, {}) if isinstance(old_obj, dict) else {}
                            compare_tokens(old_child, value, new_path)
        
        compare_tokens(old_tokens, new_tokens)
        return changed_paths, new_values
    
    async def get_token_by_path(self, token_path: str) -> Any:
        """Get a specific token value using dot notation"""
        tokens = await self.load_tokens()
        
        # Navigate through the nested structure
        current = tokens
        path_parts = token_path.split('.')
        
        for part in path_parts:
            if isinstance(current, dict) and part in current:
                current = current[part]
            else:
                raise HTTPException(
                    status_code=404, 
                    detail=f"Token not found at path: {token_path}"
                )
        
        return current
    
    async def update_token(self, token_path: str, value: Any, token_type: str, description: Optional[str] = None) -> Dict[str, Any]:
        """Update a specific token value"""
        # Validate token type
        if token_type not in settings.VALID_TOKEN_TYPES:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid token type '{token_type}'. Valid types: {settings.VALID_TOKEN_TYPES}"
            )
        
        tokens = await self.load_tokens()
        
        # Navigate to the parent object, creating path if needed
        path_parts = token_path.split('.')
        current = tokens
        
        for part in path_parts[:-1]:
            if part not in current:
                current[part] = {}
            elif not isinstance(current[part], dict):
                raise HTTPException(
                    status_code=400,
                    detail=f"Cannot create token at path '{token_path}': '{part}' is not an object"
                )
            current = current[part]
        
        # Update the final token
        final_key = path_parts[-1]
        
        # Create DTCG-compliant token structure
        token_obj = {
            "$value": value,
            "$type": token_type
        }
        
        if description:
            token_obj["$description"] = description
        
        current[final_key] = token_obj
        
        # Save the updated tokens (this will trigger broadcasts to all clients)
        await self.save_tokens(tokens)
        
        print(f"✅ Token updated: {token_path} = {value}")
        
        return {
            "token_path": token_path,
            "updated_value": token_obj,
            "timestamp": datetime.now().isoformat()
        }
    
    async def delete_token(self, token_path: str) -> Dict[str, Any]:
        """Delete a specific token"""
        tokens = await self.load_tokens()
        
        # Navigate to the parent object
        path_parts = token_path.split('.')
        current = tokens
        
        for part in path_parts[:-1]:
            if not isinstance(current, dict) or part not in current:
                raise HTTPException(
                    status_code=404,
                    detail=f"Token not found at path: {token_path}"
                )
            current = current[part]
        
        # Delete the final token
        final_key = path_parts[-1]
        if final_key not in current:
            raise HTTPException(
                status_code=404,
                detail=f"Token not found at path: {token_path}"
            )
        
        deleted_token = current.pop(final_key)
        
        # Save the updated tokens
        await self.save_tokens(tokens)
        
        print(f"🗑️  Token deleted: {token_path}")
        
        return {
            "token_path": token_path,
            "deleted_value": deleted_token,
            "timestamp": datetime.now().isoformat()
        }
    
    def _calculate_tokens_hash(self, tokens: Dict[str, Any]) -> str:
        """Calculate a hash of the tokens for change detection"""
        # Create a copy without metadata for consistent hashing
        tokens_copy = {k: v for k, v in tokens.items() if not k.startswith("$")}
        tokens_str = json.dumps(tokens_copy, sort_keys=True)
        return hashlib.md5(tokens_str.encode()).hexdigest()
    
    def get_token_metadata(self) -> Dict[str, Any]:
        """Get token metadata including version and hash"""
        try:
            tokens = asyncio.run(self.load_tokens())
            return tokens.get("$metadata", {})
        except Exception:
            return {}
    
    def _create_default_tokens(self) -> Dict[str, Any]:
        """Create a minimal default token set"""
        return {
            "$schema": "https://schemas.designtokens.org/latest",
            "$version": "1.0.0",
            "$metadata": {
                "created": datetime.now().isoformat(),
                "author": "design-token-api",
                "platforms": settings.PLATFORMS
            },
            "color": {
                "primitive": {
                    "blue": {
                        "500": {"$value": "#3b82f6", "$type": "color"}
                    },
                    "gray": {
                        "900": {"$value": "#111827", "$type": "color"},
                        "100": {"$value": "#f3f4f6", "$type": "color"}
                    }
                },
                "semantic": {
                    "primary": {
                        "$value": "{color.primitive.blue.500}",
                        "$type": "color",
                        "$description": "Primary brand color"
                    },
                    "text": {
                        "$value": "{color.primitive.gray.900}",
                        "$type": "color",
                        "$description": "Primary text color"
                    },
                    "background": {
                        "$value": "{color.primitive.gray.100}",
                        "$type": "color",
                        "$description": "Background color"
                    }
                }
            },
            "spacing": {
                "primitive": {
                    "4": {"$value": "1rem", "$type": "dimension"},
                    "8": {"$value": "2rem", "$type": "dimension"}
                },
                "semantic": {
                    "md": {
                        "$value": "{spacing.primitive.4}",
                        "$type": "dimension",
                        "$description": "Medium spacing"
                    },
                    "lg": {
                        "$value": "{spacing.primitive.8}",
                        "$type": "dimension",
                        "$description": "Large spacing"
                    }
                }
            }
        }

# Global token manager instance
token_manager = TokenManager()