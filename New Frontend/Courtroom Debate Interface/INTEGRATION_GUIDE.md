# Frontend-Backend Integration - Quick Start Guide

## Prerequisites

1. **Backend Server** must be running on `http://localhost:8000`
2. **Node.js** and **npm** installed

## Setup Instructions

### 1. Install Frontend Dependencies

```bash
cd "New Frontend/Courtroom Debate Interface"
npm install
```

### 2. Start Backend Server

In a separate terminal:

```bash
cd backend
python -m uvicorn api.main:app --reload
```

The backend should be running at `http://localhost:8000`

### 3. Start Frontend Development Server

```bash
cd "New Frontend/Courtroom Debate Interface"
npm run dev
```

The frontend will be available at `http://localhost:5173` (or the port shown in terminal)

## Testing the Integration

### Test 1: Text Analysis

1. Open the frontend in your browser
2. Enter a problem statement in the text area (e.g., "Should we invest in renewable energy?")
3. Click submit
4. Observe:
   - Real-time progress updates showing factor extraction, debate, synthesis
   - Factors being debated by agents
   - Final verdict with recommendations

### Test 2: Verify Data Flow

1. Open browser DevTools (F12)
2. Go to Network tab
3. Submit an analysis
4. Look for:
   - POST request to `/api/analyze/text`
   - EventSource connection to `/api/analyze/stream/...`
   - SSE messages streaming in

### Test 3: Error Handling

1. Stop the backend server
2. Try to submit an analysis
3. Verify error message appears in the UI

## What Changed

### Files Created:
- `src/services/api.ts` - API client with HTTP and SSE support
- `src/utils/dataTransformer.ts` - Transforms backend responses to frontend types
- `src/config/config.ts` - Configuration management
- `.env.development` - Development environment variables
- `.env.production` - Production environment variables

### Files Modified:
- `src/App.tsx` - Replaced mock data with real API integration
- `src/components/CourthouseDebate.tsx` - Added real-time progress display
- `src/types/aether.ts` - Added ProgressUpdate interface

### Design Preservation:
- ✅ All original UI components unchanged
- ✅ All styling preserved
- ✅ All animations and interactions intact
- ✅ Only data source changed from hardcoded to dynamic

## Troubleshooting

### Frontend won't start
- Run `npm install` to ensure all dependencies are installed
- Check for port conflicts (default is 5173)

### Backend connection errors
- Verify backend is running: `curl http://localhost:8000`
- Check `.env.development` has correct API URL
- Ensure CORS is enabled in backend (already configured)

### No real-time updates
- Check browser console for SSE connection errors
- Verify EventSource is supported in your browser
- Check backend logs for streaming errors

### Data not displaying correctly
- Open browser console and check for transformation errors
- Verify backend response format matches expected structure
- Check `dataTransformer.ts` for any mapping issues

## API Endpoints Used

- `POST /api/analyze/text` - Analyze text input
- `POST /api/analyze/file` - Analyze uploaded file
- `GET /api/analyze/stream/{session_id}` - Real-time SSE streaming
- `GET /api/history` - Get analysis history
- `GET /api/history/{id}` - Get specific analysis

## Next Steps

1. Test with various problem statements
2. Verify all debate messages display correctly
3. Check that final recommendations match backend logic
4. Test file upload functionality (if ProblemInput supports it)
5. Verify error scenarios are handled gracefully
