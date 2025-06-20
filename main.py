from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import asyncio

from api import tokens, platforms, sse
from core.config import settings
from core.update_broadcaster import broadcaster
from core.token_manager import token_manager
from core.style_dictionary import style_builder

def create_app() -> FastAPI:
    """Create and configure FastAPI application"""
    
    app = FastAPI(
        title="Design Token API",
        description="Design token management with real-time push updates",
        version="1.0.0"
    )

    # CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.ALLOWED_ORIGINS,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Include routers
    app.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
    app.include_router(platforms.router, prefix="/platforms", tags=["platforms"]) 
    app.include_router(platforms.router, prefix="/build", tags=["build"])
    app.include_router(sse.router, prefix="/sse", tags=["server-sent-events"])

    # Root endpoint
    @app.get("/")
    async def root():
        return {
            "message": "Design Token API",
            "version": "1.0.0",
            "endpoints": {
                "tokens": "/tokens",
                "sse": "/sse/events",
                "platforms": "/platforms",
                "build": "/build",
                "docs": "/docs"
            }
        }

    # Startup tasks
    @app.on_event("startup")
    async def startup():
        """Initialize the application"""
        # Ensure directories exist
        settings.TOKENS_DIR.mkdir(exist_ok=True)
        settings.BUILD_DIR.mkdir(exist_ok=True)
        
        # Load initial tokens
        await token_manager.load_tokens()
        
        # Setup Style Dictionary
        await style_builder.setup_style_dictionary()
        
        print(f"🚀 Design Token API started")
        print(f"📄 HTTP API: http://localhost:{settings.PORT}")
        print(f"📡 Server-Sent Events: http://localhost:{settings.PORT}/sse/events")
        print(f"📁 Tokens: {settings.TOKENS_DIR}")
        print(f"🏗️  Builds: {settings.BUILD_DIR}")

    return app

# Create the app instance
app = create_app()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app", 
        host="0.0.0.0", 
        port=settings.PORT, 
        reload=settings.DEBUG
    )