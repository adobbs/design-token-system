from pathlib import Path
from typing import List
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Application settings with environment variable support"""
    
    # Basic app settings
    DEBUG: bool = True
    PORT: int = 8000
    
    # Security
    ALLOWED_ORIGINS: List[str] = ["*"]  # Configure for production
    
    # Directories
    BASE_DIR: Path = Path(__file__).parent.parent
    TOKENS_DIR: Path = BASE_DIR / "tokens"
    BUILD_DIR: Path = BASE_DIR / "dist"
    
    # Supported platforms
    PLATFORMS: List[str] = ["web", "ios", "android", "flutter"]
    
    # WebSocket settings
    WEBSOCKET_PING_INTERVAL: int = 30  # seconds
    MAX_WEBSOCKET_CONNECTIONS: int = 1000
    
    # Style Dictionary settings
    STYLE_DICTIONARY_CONFIG: str = "style-dictionary.config.js"
    
    # Token validation
    VALID_TOKEN_TYPES: List[str] = [
        "color", "dimension", "fontFamily", "fontWeight", 
        "shadow", "number", "duration", "cubicBezier"
    ]
    
    class Config:
        env_file = ".env"
        case_sensitive = True

# Create global settings instance
settings = Settings()