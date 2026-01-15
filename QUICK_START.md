# Quick Start Guide - Testing Bug Fixes

## ✅ The Fixes Are Already Applied!

I've already fixed both bugs in your code:

1. **Backend**: `backend\agents\critic_agent.py` (line 195) - No more auto-rejection for weak evidence
2. **Frontend**: `New Frontend\Courtroom Debate Interface\src\utils\dataTransformer.ts` (lines 240-314) - Dynamic disagreement scoring

---

## 🚀 How to Test

### Option 1: Use Your Existing Start Script

Just run your normal start script:

```bash
start_server.bat
```

This will:
- Start the backend on `http://127.0.0.1:8000`
- Use Google LLM provider (as configured in your .bat file)

### Option 2: Manual Start

```bash
cd backend
python run.py
```

Then in another terminal:
```bash
cd "New Frontend\Courtroom Debate Interface"
npm run dev
```

---

## 🧪 Test the Fixes

### Test 1: Check Disagreement Scores

1. Open the frontend in your browser
2. Input any text (e.g., "The project failed due to poor management")
3. Look at the disagreement scores in the UI
4. **Before fix**: All factors showed 90%
5. **After fix**: You should see different scores (e.g., 70%, 85%, 60%)

### Test 2: Check Auto-Rejection

1. Input text with weak evidence
2. Check the debate logs
3. **Before fix**: Factors auto-rejected with "insufficient evidence"
4. **After fix**: LLM evaluates the debate and makes decision

---

## 📊 What to Look For

### In the Frontend UI:
- Disagreement scores should vary (not all 90%)
- Factors should show proper debate evaluation

### In the API Response:
```json
{
  "factors": [
    {
      "disagreementScore": 0.7  // ✅ Not 0.9!
    }
  ],
  "debates": {
    "1": {
      "critique": {
        "resolution": "REJECTED",
        "justification": "Valid reason here"  // ✅ Not "insufficient evidence"
      }
    }
  }
}
```

---

## 🎯 That's It!

The fixes are already in your code. Just run your server normally and test!

**No Docker, no microservices, no complex setup needed.**
