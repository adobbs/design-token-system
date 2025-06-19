# Design Token System

A FastAPI-based design token management system with real-time updates and multi-platform builds.

## 🚧 Status

Project under active development.

## 🎯 Goal

Provide a **production-ready reference architecture** for building your own design token management system. Features real-time updates via Server-Sent Events, multi-platform builds with Style Dictionary, and a clean, scalable codebase.

## ✨ Features

- **Real-time updates** - Server-Sent Events with HTTP polling fallback
- **Multi-platform builds** - Web (CSS), iOS (Swift), Android (XML)
- **Version tracking** - Clients never miss updates during reconnections
- **Token validation** - Comprehensive validation for colors, dimensions, and token references
- **Mobile optimized** - Adaptive polling with battery-conscious intervals
- **Admin-friendly** - Live preview capabilities for non-technical users

## 🏛️ Architecture

```
app/
├── main.py                   # FastAPI app setup
├── core/
│   ├── config.py             # Settings management
│   ├── update_broadcaster.py # SSE broadcasting system
│   ├── token_manager.py      # Token business logic
│   └── style_dictionary.py   # Build system integration
├── api/
│   ├── tokens.py             # Token CRUD endpoints
│   ├── sse.py                # Real-time updates
│   └── platforms.py          # Build & download endpoints
└── models/
    └── tokens.py             # Data validation models
```

## 🚀 Quick Start

### 1. Environment Setup
```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows

# Install Python dependencies
pip install -r requirements.txt

# Install Node.js dependencies (for Style Dictionary)
npm install
```

### 2. Start the Server
```bash
python app/main.py
```

The API will be available at:
- **HTTP API**: `http://localhost:8000`
- **Real-time updates**: `http://localhost:8000/sse/events`
- **API docs**: `http://localhost:8000/docs`

## 📡 API Endpoints

### Token Management
```
GET    /tokens                 # Get all design tokens
GET    /tokens/{path}          # Get specific token
PUT    /tokens/{path}          # Update token (triggers real-time broadcast)
DELETE /tokens/{path}          # Delete token
POST   /tokens/batch           # Batch update multiple tokens
```

### Real-time Updates
```
GET    /sse/events             # Server-Sent Events stream
GET    /sse/status             # Connection statistics
GET    /sse/updates/sync       # Polling fallback endpoint
```

### Platform Builds
```
POST   /platforms/build        # Build all platforms
POST   /platforms/build/{platform}  # Build specific platform
GET    /platforms/{platform}/download  # Download main file (e.g., tokens.css)
GET    /platforms/{platform}/files    # List all files for platform
```

## 💻 Client Usage

### JavaScript Client
```javascript
// Initialize with real-time updates
const tokenClient = new DesignTokenClient('http://localhost:8000', {
  preferredProtocol: 'sse', // SSE with polling fallback
  onTokenUpdate: (update) => {
    console.log('🎨 Tokens updated:', update.changedPaths);
    // CSS variables updated automatically
  },
  onConnectionChange: (status) => {
    console.log('🔌 Connection:', status.method);
  }
});

await tokenClient.initialize();
```

### React Hook
```javascript
function MyComponent() {
  const { tokens, connectionStatus, loading } = useDesignTokens();
  
  if (loading) return <div>Loading tokens...</div>;
  
  return (
    <div>
      <p>Status: {connectionStatus.connected ? 'Connected' : 'Disconnected'}</p>
      <p>Method: {connectionStatus.method}</p>
      {/* Your component using design tokens */}
    </div>
  );
}
```

### HTTP API Usage
```bash
# Update a color token
curl -X PUT http://localhost:8000/tokens/color/semantic/primary \
  -H "Content-Type: application/json" \
  -d '{
    "token_path": "color.semantic.primary",
    "value": "#ff6b6b", 
    "type": "color",
    "description": "Updated primary brand color"
  }'

# Build tokens for web platform
curl -X POST http://localhost:8000/platforms/build/web

# Download CSS file
curl http://localhost:8000/platforms/web/download -o tokens.css
```

## 🎨 Token Format

Uses the [W3C Design Tokens Community Group](https://www.w3.org/community/design-tokens/) specification:

```json
{
  "$schema": "https://schemas.designtokens.org/latest",
  "$version": "1.0.0",
  "color": {
    "primitive": {
      "blue": {
        "500": {"$value": "#3b82f6", "$type": "color"}
      }
    },
    "semantic": {
      "primary": {
        "$value": "{color.primitive.blue.500}",
        "$type": "color",
        "$description": "Primary brand color"
      }
    }
  },
  "spacing": {
    "semantic": {
      "md": {
        "$value": "1rem",
        "$type": "dimension",
        "$description": "Medium spacing"
      }
    }
  }
}
```

## 🏗️ Platform Outputs

### Web (CSS Custom Properties)
```css
:root {
  --color-semantic-primary: #3b82f6;
  --spacing-semantic-md: 1rem;
}
```

### iOS (Swift)
```swift
public class DesignTokens {
    public static let colorSemanticPrimary = UIColor(hex: 0x3b82f6)
    public static let spacingSemanticMd: CGFloat = 16.0
}
```

### Android (XML Resources)
```xml
<resources>
  <color name="color_semantic_primary">#3b82f6</color>
  <dimen name="spacing_semantic_md">16dp</dimen>
</resources>
```

## 🔄 Real-time Updates

### How It Works
1. Designer updates a token via API
2. Server calculates changes and broadcasts via SSE
3. All connected clients receive updates instantly
4. CSS custom properties updated automatically
5. UI reflects changes without page reload

### Connection Strategy
- **Web apps**: Server-Sent Events → HTTP polling fallback
- **Mobile apps**: Adaptive HTTP polling (battery optimized)
- **Admin tools**: SSE for real-time preview

### Missed Update Recovery
- Version tracking ensures clients detect missed updates
- Automatic sync when reconnecting
- Hash-based change detection for reliability

## 📱 Mobile Considerations

### Battery Optimization
```javascript
// Adaptive polling intervals
const intervals = {
  active: 30000,      // 30s when app is active
  background: 300000, // 5min when backgrounded
  lowBattery: 600000  // 10min when battery < 20%
};
```

### App State Handling
- Pauses polling when app backgrounded
- Resumes when app becomes active
- Handles network changes gracefully

## 🛠️ Development

### Project Structure
- **`app/core/`** - Business logic (no FastAPI dependencies)
- **`app/api/`** - HTTP endpoints and SSE streams
- **`app/models/`** - Pydantic validation models
- **`tokens/`** - Token storage (JSON files)
- **`dist/`** - Built platform outputs

### Adding New Platforms
1. Update `style_dictionary.py` config
2. Add platform to `settings.PLATFORMS`
3. Define output format in Style Dictionary config
4. Test build pipeline

### Testing
```bash
# Run token validation tests
python -m pytest tests/test_tokens.py

# Test real-time updates
python -m pytest tests/test_sse.py

# Test platform builds  
python -m pytest tests/test_builds.py
```

## 📦 Dependencies

### Python
- `fastapi` - Web framework
- `sse-starlette` - Server-Sent Events
- `pydantic` - Data validation
- `uvicorn` - ASGI server

### Node.js
- `style-dictionary` - Token transformation

## 🚂 Production Deployment

### Environment Variables
```bash
DEBUG=false
PORT=8000
ALLOWED_ORIGINS=https://yourdomain.com
TOKENS_DIR=/app/tokens
BUILD_DIR=/app/dist
```

### Docker
```dockerfile
FROM python:3.11-slim
# Install Node.js for Style Dictionary
RUN apt-get update && apt-get install -y nodejs npm
WORKDIR /app
COPY requirements.txt package.json ./
RUN pip install -r requirements.txt && npm install
COPY . .
EXPOSE 8000
CMD ["python", "app/main.py"]
```

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🤙 Attribution

If you use this project in your work, a link back to this repository is appreciated but not required.

## 🙏 Acknowledgments

- [W3C Design Tokens Community Group](https://www.w3.org/community/design-tokens/) for the specification
- [Style Dictionary](https://amzn.github.io/style-dictionary/) for token transformation
- [Server-Sent Events](https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events) for real-time updates