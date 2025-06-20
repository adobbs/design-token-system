# Pydantic models for token validation

from typing import Union, List, Optional, Dict, Any
from pydantic import BaseModel, Field, field_validator

from core.config import settings

class TokenUpdate(BaseModel):
    """Model for updating a single token"""
    token_path: str = Field(..., description="Dot-notation path to token (e.g., 'color.semantic.primary')")
    value: Union[str, int, float, List[str]] = Field(..., description="Token value")
    type: str = Field(..., description="Token type (color, dimension, etc.)")
    description: Optional[str] = Field(None, description="Optional description")
    
    @field_validator('type')
    @classmethod
    def validate_token_type(cls, v):
        if v not in settings.VALID_TOKEN_TYPES:
            raise ValueError(f'Invalid token type "{v}". Valid types: {settings.VALID_TOKEN_TYPES}')
        return v
    
    @field_validator('value')
    @classmethod
    def validate_color_value(cls, v, info):
        token_type = info.data.get('type') if info.data else None
        
        if token_type == 'color' and isinstance(v, str):
            # Basic hex color validation
            if v.startswith('#'):
                if len(v) not in [4, 7, 9]:  # #fff, #ffffff, #ffffffff
                    raise ValueError('Hex colors must be 3, 6, or 8 characters after #')
                try:
                    int(v[1:], 16)  # Validate hex characters
                except ValueError:
                    raise ValueError('Invalid hex color format')
            elif not (v.startswith('rgb') or v.startswith('hsl') or v.startswith('{')):
                # Allow rgb(), hsl(), or token references like {color.primitive.blue.500}
                raise ValueError('Color values must be hex (#fff), rgb(), hsl(), or token references')
        
        elif token_type == 'dimension' and isinstance(v, str):
            # Allow CSS units or token references
            if not (v.endswith(('px', 'rem', 'em', '%', 'vh', 'vw', 'pt', 'pc', 'in', 'cm', 'mm')) or 
                    v.startswith('{') or v.replace('.', '').replace('-', '').isdigit()):
                raise ValueError('Dimension values must have valid CSS units or be token references')
        
        return v
    
    @field_validator('token_path')
    @classmethod
    def validate_token_path(cls, v):
        # Basic path validation
        if not v or '..' in v or v.startswith('.') or v.endswith('.'):
            raise ValueError('Invalid token path format')
        
        # Check for valid characters
        valid_chars = set('abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789.-_')
        if not all(c in valid_chars for c in v):
            raise ValueError('Token path contains invalid characters')
        
        return v

class TokenBatchUpdate(BaseModel):
    """Model for batch token updates"""
    tokens: List[TokenUpdate] = Field(..., description="List of token updates")
    
    @field_validator('tokens')
    @classmethod
    def validate_tokens_not_empty(cls, v):
        if not v:
            raise ValueError('Token list cannot be empty')
        if len(v) > 100:  # Reasonable limit for batch operations
            raise ValueError('Cannot update more than 100 tokens at once')
        return v

class TokenMetadata(BaseModel):
    """Model for token metadata"""
    created: Optional[str] = None
    modified: Optional[str] = None
    author: Optional[str] = None
    version: Optional[int] = None
    hash: Optional[str] = None
    platforms: Optional[List[str]] = None
    description: Optional[str] = None

class TokenCollection(BaseModel):
    """Model for a complete token collection"""
    schema_: Optional[str] = Field(None, alias="$schema")
    version: Optional[str] = Field(None, alias="$version")
    metadata: Optional[Dict[str, Any]] = Field(None, alias="$metadata")
    tokens: Dict[str, Any] = Field(..., description="Token data")
    
    class Config:
        validate_by_name = True

class BuildRequest(BaseModel):
    """Model for build requests"""
    platforms: Optional[List[str]] = Field(None, description="Platforms to build")
    force_rebuild: bool = Field(False, description="Force rebuild even if no changes")
    
    @field_validator('platforms')
    @classmethod
    def validate_platforms(cls, v):
        if v is not None:
            available = settings.PLATFORMS + ['scss', 'json']
            invalid = [p for p in v if p not in available]
            if invalid:
                raise ValueError(f'Invalid platforms: {invalid}. Available: {available}')
        return v

class PlatformFile(BaseModel):
    """Model for platform file information"""
    name: str = Field(..., description="File name")
    path: str = Field(..., description="Relative path from build directory")
    size: int = Field(..., description="File size in bytes")
    modified: str = Field(..., description="Last modified timestamp")
    extension: str = Field(..., description="File extension")

class BuildResult(BaseModel):
    """Model for build results"""
    success: bool = Field(..., description="Whether the build succeeded")
    platform: str = Field(..., description="Platform name")
    build_time: str = Field(..., description="Build timestamp")
    output_files: List[str] = Field(..., description="List of output files")
    file_sizes: Dict[str, int] = Field(default_factory=dict, description="File sizes in bytes")
    build_duration_ms: int = Field(..., description="Build duration in milliseconds")
    error: Optional[str] = Field(None, description="Error message if build failed")

class ConnectionStatus(BaseModel):
    """Model for connection status"""
    connected: bool = Field(..., description="Whether client is connected")
    method: str = Field(..., description="Connection method (sse, polling)")
    current_version: Optional[int] = Field(None, description="Current token version")
    current_hash: Optional[str] = Field(None, description="Current token hash")

class UpdateNotification(BaseModel):
    """Model for update notifications"""
    type: str = Field(..., description="Notification type")
    version: Optional[int] = Field(None, description="Token version")
    hash: Optional[str] = Field(None, description="Token hash")
    changed_paths: List[str] = Field(default_factory=list, description="Changed token paths")
    new_values: Dict[str, Any] = Field(default_factory=dict, description="New token values")
    timestamp: str = Field(..., description="Update timestamp")

class SyncRequest(BaseModel):
    """Model for sync requests"""
    current_version: Optional[int] = Field(None, description="Client's current version")
    current_hash: Optional[str] = Field(None, description="Client's current hash")
    since_timestamp: Optional[str] = Field(None, description="Get updates since timestamp")

class SyncResponse(BaseModel):
    """Model for sync responses"""
    current_version: int = Field(..., description="Server's current version")
    current_hash: str = Field(..., description="Server's current hash")
    sync_needed: bool = Field(..., description="Whether client needs to sync")
    updates: List[UpdateNotification] = Field(default_factory=list, description="Available updates")
    full_reload_needed: bool = Field(False, description="Whether full reload is needed")