# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a production-ready design token management system built with FastAPI and Style Dictionary integration. Features real-time updates via Server-Sent Events, multi-platform builds, and a clean, scalable architecture.

## Development Commands

### Environment Setup
```bash
# Create and activate virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# venv\Scripts\activate   # Windows

# Install dependencies
pip install -r requirements.txt
npm install
```

### Development Server
```bash
# Run the FastAPI development server (with auto-reload)
python main.py

# Alternative using npm script
npm run dev
```

### Design Token Build
```bash
# Build tokens for all platforms using Style Dictionary
npm run build-tokens
```

## Architecture

### Core Application Structure
The application follows a layered architecture with clear separation of concerns:

- **`main.py`** - FastAPI application bootstrap, CORS setup, router registration
- **`core/`** - Business logic layer (framework-agnostic)
  - `config.py` - Centralized settings with environment variable support
  - `token_manager.py` - Core token CRUD operations and file management
  - `update_broadcaster.py` - Server-Sent Events broadcasting system
  - `style_dictionary.py` - Build system integration for multi-platform output
- **`api/`** - HTTP endpoints and SSE streams
  - `tokens.py` - Token management endpoints with real-time updates
  - `sse.py` - Server-Sent Events with polling fallback
  - `platforms.py` - Build triggering and file download endpoints
- **`models/`** - Pydantic validation models for type safety

### Key Architectural Patterns
- **Dependency Injection**: Core business logic is injected into API routes
- **Event Broadcasting**: All token updates trigger real-time broadcasts to connected clients
- **Version Tracking**: Clients can detect missed updates during reconnections
- **Async Build System**: Platform builds run asynchronously with status tracking

### Real-time Update System
The system broadcasts token changes via Server-Sent Events:
1. Token update via API triggers change detection
2. `update_broadcaster.py` calculates delta and broadcasts to all connected clients
3. Clients receive updates with version information for missed update recovery
4. HTTP polling fallback available for environments where SSE isn't supported

### Token System Structure
Follows W3C Design Tokens Community Group specification:
1. **Primitive Tokens**: Raw values (colors, dimensions, typography scales)
2. **Semantic Tokens**: Purpose-driven tokens referencing primitives using `{token.reference}` syntax
3. **Component Tokens**: Component-specific tokens for buttons, inputs, cards, etc.

### Multi-Platform Build System
Style Dictionary integration supports multiple output formats:
- **Web**: CSS custom properties, SCSS variables
- **iOS**: Swift color/dimension definitions
- **Android**: XML resource files
- **Flutter**: Dart constants

## API Endpoints

### Token Management
- `GET /tokens` - Retrieve all design tokens
- `GET /tokens/{path}` - Get specific token by path
- `PUT /tokens/{path}` - Update token (triggers real-time broadcast)
- `DELETE /tokens/{path}` - Delete token
- `POST /tokens/batch` - Batch update multiple tokens

### Real-time Updates
- `GET /sse/events` - Server-Sent Events stream for real-time updates
- `GET /sse/status` - Connection statistics
- `GET /sse/updates/sync` - HTTP polling fallback endpoint

### Platform Builds
- `POST /platforms/build` - Build all platforms
- `POST /platforms/build/{platform}` - Build specific platform
- `GET /platforms/{platform}/download` - Download built files
- `GET /platforms/{platform}/files` - List available files for platform

## Key Files

- `tokens/tokens.json` - W3C DTCG-compliant design token definitions
- `main.py` - FastAPI application entry point
- `core/config.py` - Settings management with supported platforms list
- `dist/` - Built platform outputs (created after first build)

## Development Notes

- The project uses hybrid Python/Node.js architecture (Python for API, Node.js for Style Dictionary)
- All business logic in `core/` is framework-agnostic for easier testing
- Real-time updates use SSE with HTTP polling fallback for mobile compatibility
- Token validation prevents invalid color values, malformed references, and unsupported types
- Platform builds are cached and only rebuilt when tokens change