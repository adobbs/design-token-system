# Design Token System

A FastAPI-based design token management system with Style Dictionary integration.

## Goal
Provide a reference architecture for build-your-own design token management.

## Project Status
In progress. Server and client implementations forthcoming.

## Setup

1. Create virtual environment: `python -m venv venv`
2. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
3. Install Python deps: `pip install -r requirements.txt`
4. Install Node deps: `npm install`
5. Run the server: `python main.py`

## API Endpoints

- `GET /tokens` - Get all tokens
- `PUT /tokens/{path}` - Update a token
- `POST /build` - Build tokens for all platforms
- `GET /docs` - API documentation

## Usage

Visit `http://localhost:8000/docs` for interactive API documentation.