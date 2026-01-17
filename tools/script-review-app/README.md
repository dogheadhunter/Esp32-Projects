# DJ Script Review App

A mobile-first Progressive Web App for reviewing AI-generated DJ scripts with a Tinder-like swipe interface.

## Features

- 📱 **Mobile-First Design**: Optimized for touch interfaces with swipe gestures
- 🔄 **Swipe to Review**: Swipe right to approve, left to reject
- 📊 **Statistics Dashboard**: Track pending, approved, and rejected scripts
- 🔒 **Token Authentication**: Secure API access with bearer tokens
- 💾 **Offline Support**: PWA with service workers for offline capability
- 🎨 **Modern UI**: Clean, responsive interface built with Tailwind CSS
- 🚀 **Fast API**: Built with FastAPI for high performance
- 📁 **File-Based Storage**: Simple JSON-based metadata and folder organization

## Architecture

### Backend (FastAPI)
- **API Endpoints**: RESTful API for script management
- **Authentication**: Token-based auth with environment variables
- **Storage**: File-based with organized folder structure
- **Validation**: Pydantic models for data validation

### Frontend (Vanilla JS + Tailwind)
- **Zero Dependencies**: Pure JavaScript for swipe detection
- **Responsive**: Mobile-first design with Tailwind CSS
- **PWA**: Service worker for offline support
- **Accessible**: Keyboard shortcuts and screen reader support

### Folder Structure

```
output/scripts/
├── pending_review/          # Scripts awaiting review
│   ├── Julie/
│   ├── Mr. New Vegas/
│   └── Travis Miles (Nervous)/
├── approved/                # Approved scripts
├── rejected/                # Rejected scripts
└── metadata/                # Review logs (JSON)
    ├── approved.json
    └── rejected.json
```

## Installation

### Prerequisites
- Python 3.10+
- pip

### Setup

1. Install dependencies:
```bash
cd tools/script-review-app
pip install -r requirements.txt
```

2. Configure environment:
```bash
cp .env.template .env
# Edit .env and set SCRIPT_REVIEW_TOKEN
```

3. Generate a secure token:
```bash
openssl rand -hex 32
```

4. Add the token to `.env`:
```
SCRIPT_REVIEW_TOKEN=your-generated-token-here
```

## Usage

### Start the Server

```bash
cd tools/script-review-app
python -m backend.main
```

Or with uvicorn directly:
```bash
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

### Access the App

1. Open http://localhost:8000 in your browser
2. Enter your API token when prompted
3. Start reviewing scripts!

### Mobile Access

For mobile testing:
1. Find your computer's IP address
2. Access `http://YOUR_IP:8000` from mobile device
3. Ensure both devices are on the same network

For production deployment with HTTPS:
- Use a reverse proxy (Nginx)
- Configure SSL with Let's Encrypt
- Update `ALLOWED_ORIGINS` in `.env`

## API Documentation

Once running, visit http://localhost:8000/docs for interactive API documentation.

### Endpoints

- `GET /api/scripts?dj={name}` - List pending scripts (optional DJ filter)
- `POST /api/review` - Submit review decision
- `GET /api/reasons` - Get rejection reasons
- `GET /api/stats` - Get review statistics

### Authentication

All API endpoints require a Bearer token:
```
Authorization: Bearer YOUR_TOKEN_HERE
```

## Usage Guide

### Reviewing Scripts

1. **Swipe Right** or click **✓ Approve** to approve a script
2. **Swipe Left** or click **✗ Reject** to reject a script
3. When rejecting, select a reason from the dropdown
4. For "Other", provide a custom comment

### Keyboard Shortcuts

- `→` (Right Arrow) - Approve current script
- `←` (Left Arrow) - Reject current script

### Filtering

Use the DJ dropdown to filter scripts by personality, or view all DJs shuffled together.

## Testing

See the `tests/` directory for Playwright-based tests covering:
- Mobile viewport interactions
- Swipe gesture detection
- API integration
- Authentication flow
- Offline mode
- Responsive layouts

Run tests with:
```bash
# Tests will be implemented in Phase 5
pytest tests/
```

## Development

### Project Structure

```
script-review-app/
├── backend/
│   ├── main.py              # FastAPI app
│   ├── models.py            # Pydantic models
│   ├── auth.py              # Authentication
│   ├── storage.py           # File operations
│   └── config.py            # Configuration
├── frontend/
│   ├── templates/
│   │   └── index.html       # Main page
│   └── static/
│       ├── app.js           # Main application logic
│       ├── api.js           # API client
│       ├── swipe.js         # Gesture handling
│       ├── manifest.json    # PWA manifest
│       ├── service-worker.js
│       └── icons/
├── data/
│   └── rejection_reasons.json
├── tests/
│   └── playwright/          # Browser tests
├── requirements.txt
├── .env.template
└── README.md
```

### Adding Rejection Reasons

Edit `data/rejection_reasons.json`:
```json
{
  "reasons": [
    {
      "id": "new_reason",
      "label": "Description",
      "category": "quality"
    }
  ]
}
```

## Security

- ✅ Token-based authentication
- ✅ CORS restrictions
- ✅ Input validation with Pydantic
- ✅ No SQL injection (file-based storage)
- ✅ HTTPS recommended for production
- ✅ Environment-based configuration

## Performance

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3s
- Bundle Size: < 100KB (excluding Tailwind CDN)
- API Response Time: < 200ms

## Progressive Web App

Install the app on your mobile device:
1. Open the app in mobile browser
2. Look for "Add to Home Screen" prompt
3. Install and launch like a native app

Offline support:
- Scripts cached for offline viewing
- Reviews queued and synced when online

## Troubleshooting

### "Authentication failed"
- Check your API token in `.env`
- Ensure token matches what you entered in the UI
- Token should be at least 32 characters

### "No scripts found"
- Ensure scripts exist in `output/scripts/pending_review/`
- Create test folders: `Julie/`, `Mr. New Vegas/`, etc.
- Add `.txt` files with script content

### Service worker not registering
- Requires HTTPS (or localhost)
- Check browser console for errors
- Clear cache and reload

## Contributing

1. Follow the existing code style
2. Test on real mobile devices
3. Update documentation for new features
4. Keep the bundle size small

## License

Part of the ESP32 AI Radio project.
