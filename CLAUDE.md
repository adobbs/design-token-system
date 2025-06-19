# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a design token management system built with FastAPI and Style Dictionary integration. The project provides a reference architecture for build-your-own design token management with API endpoints for token manipulation and multi-platform build output.

## Development Commands

### Python Environment Setup
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # Linux/Mac
venv\Scripts\activate     # Windows

# Install Python dependencies
pip install -r requirements.txt
```

### Node.js Setup
```bash
# Install Node dependencies
npm install
```

### Development Server
```bash
# Run the FastAPI development server
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

### Current Implementation Status
- **In Progress**: The project is in early development phase
- **Tokens Defined**: Comprehensive design token system exists in `tokens/tokens.json`
- **Server Missing**: Main FastAPI application (`main.py`) not yet implemented

### Token System Structure
The design token system follows W3C Design Tokens Community Group specification with three hierarchical layers:

1. **Primitive Tokens**: Raw values (colors, dimensions, typography scales)
2. **Semantic Tokens**: Purpose-driven tokens referencing primitives using `{token.reference}` syntax
3. **Component Tokens**: Component-specific tokens for buttons, inputs, cards, etc.

### Expected API Architecture
The planned FastAPI server should implement these endpoints:
- `GET /tokens` - Retrieve all design tokens
- `PUT /tokens/{path}` - Update specific token values
- `POST /build` - Trigger Style Dictionary build for all platforms
- `GET /docs` - Automatic FastAPI documentation

### Design Token Categories
- **Color**: Primitive palettes, semantic colors, component color schemes
- **Spacing**: Dimension values for layout and component spacing
- **Typography**: Font families, sizes, weights, semantic text styles  
- **Border Radius**: Corner rounding values
- **Shadow**: Drop shadow definitions
- **Size**: Width/height values for components and icons

### Platform Extensions
The token system includes custom extensions (`com.acme.designsystem`) defining:
- Platform-specific output formats (Web, iOS, Android, Figma)
- Governance policies with approval workflows
- Usage analytics and deprecation management
- Theme system with light/dark mode support

## Key Files

- `tokens/tokens.json` - Complete design token system definition
- `requirements.txt` - Python dependencies (FastAPI, Pydantic, Uvicorn)
- `package.json` - Node.js dependencies and npm scripts
- `main.py` - Main FastAPI application entry point (to be implemented)

## Development Notes

- The project uses a hybrid Python/Node.js architecture
- Design tokens follow strict hierarchical organization with reference syntax
- Multi-platform build support requires Style Dictionary integration
- API server provides interactive documentation at `/docs` endpoint