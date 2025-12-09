# 🚀 AI-Native Coding Interview Platform

A complete full-stack application for conducting AI-powered coding interviews with real-time assistance, code execution, and proctoring features.

## 📋 Architecture Overview

### **Backend (Python + FastAPI)**
- **FastAPI** for REST API and WebSocket server
- **Socket.io** for real-time bidirectional communication
- **Azure OpenAI** for AI interviewer intelligence
- **Judge0** for secure JavaScript code execution
- **Pydantic** for data validation and settings management

### **Frontend (Next.js 14)**
- **Next.js 14** with App Router and TypeScript
- **Monaco Editor** for professional code editing
- **Socket.io Client** for real-time updates
- **Tailwind CSS** for modern, responsive UI
- **Lucide React** for beautiful icons

---

## 🎯 Key Features

### 1. **AI Interviewer**
- Greets candidates and explains problems clearly
- Answers clarifying questions naturally
- Provides contextual hints when candidates are stuck
- **Stuck Detection**: Automatically offers help after 3 consecutive errors
- Never reveals complete solutions

### 2. **Live Code Execution**
- Monaco Editor with JavaScript syntax highlighting
- Real-time code execution via Judge0 API
- Automated test cases with pass/fail feedback
- Execution time and memory usage tracking
- Color-coded console output (stdout/stderr)

### 3. **Real-time Communication**
- WebSocket-based bidirectional messaging
- **Voice Interaction**: Speak to the AI and hear responses read aloud (Web Speech API)
- Debounced code updates (500ms) to reduce network load
- Live chat with AI interviewer
- Instant execution results

### 4. **Proctoring Features**
- **Paste Detection**: Monitors large clipboard pastes
- **Tab Switch Tracking**: Logs when candidate leaves the interview tab
- All events stored for integrity analysis

### 5. **Professional IDE Experience**
- Fixed tab layout: `solution.js` (editable) and `tests.js` (read-only)
- Auto-completion and IntelliSense
- Dark theme optimized for long sessions
- Resizable panels

---

## 🛠️ Setup Instructions

### **Prerequisites**
- **Python 3.9+** (for backend)
- **Node.js 18+** (for frontend)
- **Azure OpenAI API Key** ([Get it here](https://azure.microsoft.com/en-us/products/ai-services/openai-service))
- **Judge0 API Key** ([Get it here](https://rapidapi.com/judge0-official/api/judge0-ce))

---

### **Backend Setup**

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Create `.env` file:**
   ```bash
   # Copy the example file
   copy .env.example .env  # Windows
   cp .env.example .env    # macOS/Linux
   ```

5. **Edit `.env` with your credentials:**
   ```env
   AZURE_OPENAI_API_KEY=your_azure_openai_api_key_here
   AZURE_OPENAI_ENDPOINT=https://your-resource.openai.azure.com/
   AZURE_OPENAI_DEPLOYMENT=gpt-4
   AZURE_OPENAI_API_VERSION=2024-02-15-preview
   
   JUDGE0_API_KEY=your_judge0_api_key_here
   JUDGE0_ENDPOINT=https://judge0-ce.p.rapidapi.com
   
   CORS_ORIGINS=["http://localhost:3000"]
   DEBUG=True
   ```

6. **Run the backend server:**
   ```bash
   uvicorn app.main:socket_app --reload --port 8000
   ```

   You should see:
   ```
   INFO:     Uvicorn running on http://0.0.0.0:8000
   INFO:     Application startup complete.
   ```

---

### **Frontend Setup**

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Create `.env.local` file:**
   ```bash
   echo NEXT_PUBLIC_WS_URL=http://localhost:8000 > .env.local
   ```

4. **Run the development server:**
   ```bash
   npm run dev
   ```

   You should see:
   ```
   ▲ Next.js 15.1.3
   - Local:        http://localhost:3000
   ```

5. **Open your browser:**
   Navigate to [http://localhost:3000](http://localhost:3000)

---

## 🎮 How to Use

### **Starting an Interview**

1. Open [http://localhost:3000](http://localhost:3000)
2. (Optional) Enter your name
3. Click **"Start Interview"**
4. You'll be redirected to the interview page with a unique session ID

### **During the Interview**

#### **Editor Panel (Left)**
- Write your JavaScript solution in the `solution.js` tab
- View test cases in the `tests.js` tab (read-only)
- Code auto-saves and syncs to the backend every 500ms

#### **Console Panel (Bottom Left)**
- Click **"Run Code"** to execute your solution
- See test results with color-coded output:
  - 🟢 **Green**: Successful output (stdout)
  - 🔴 **Red**: Errors (stderr)
  - 🔵 **Blue**: System messages
- Clear console with the trash icon

#### **Chat Panel (Right)**
- Ask the AI interviewer clarifying questions
- Request hints if you're stuck
- The AI will **automatically** send a hint after 3 consecutive errors
- Hints are highlighted with a 💡 lightbulb icon

### **Example Workflow**

1. **Read the problem** in the AI's welcome message
2. **Ask questions**: "Can I assume the array is sorted?"
3. **Write code** in the editor
4. **Run tests** to see if your solution works
5. **Get help**: If stuck, the AI will proactively offer hints
6. **Iterate** until all tests pass ✅

---

## 📂 Project Structure

```
ai-interview-platform/
├── backend/
│   ├── app/
│   │   ├── __init__.py
│   │   ├── main.py                 # FastAPI entry point
│   │   ├── config.py               # Environment config
│   │   ├── models/
│   │   │   └── session.py          # Data models
│   │   ├── services/
│   │   │   └── judge0_service.py   # Code execution
│   │   ├── agents/
│   │   │   └── interviewer_agent.py # AI logic
│   │   └── websocket/
│   │       └── socket_manager.py   # WebSocket events
│   ├── requirements.txt
│   └── .env.example
│
├── frontend/
│   ├── app/
│   │   ├── layout.tsx
│   │   ├── page.tsx                # Landing page
│   │   └── interview/
│   │       └── [sessionId]/
│   │           └── page.tsx        # Main interview UI
│   ├── components/
│   │   ├── Editor/
│   │   │   ├── MonacoEditor.tsx
│   │   │   └── TabManager.tsx
│   │   ├── Console/
│   │   │   └── OutputConsole.tsx
│   │   └── Chat/
│   │       └── ChatPanel.tsx
│   ├── lib/
│   │   ├── socket.ts               # Socket.io client
│   │   └── utils.ts                # Utilities
│   ├── types/
│   │   └── index.ts                # TypeScript types
│   └── package.json
│
└── README.md
```

---

## 🔧 Technical Deep Dive

### **WebSocket Event Flow**

#### **Client → Server Events**
| Event | Data | Purpose |
|-------|------|---------|
| `join_session` | `{ session_id, candidate_name }` | Initialize interview session |
| `code_update` | `{ code }` | Sync code changes (debounced) |
| `run_code` | `{ code }` | Execute code with Judge0 |
| `chat_message` | `{ message }` | Send message to AI |
| `proctoring_event` | `{ type, metadata }` | Log integrity events |

#### **Server → Client Events**
| Event | Data | Purpose |
|-------|------|---------|
| `session_joined` | `SessionData` | Send initial session state |
| `execution_started` | `{}` | Notify execution began |
| `execution_complete` | `ExecutionResult` | Return test results |
| `chat_response` | `ChatMessage` | AI interviewer response |

### **Stuck Detection Algorithm**

```python
# Backend logic in socket_manager.py
if result.stderr or not result.test_passed:
    error_msg = result.stderr or "Tests failed"
    
    if session.last_error_message == error_msg:
        session.consecutive_errors += 1
    else:
        session.consecutive_errors = 1
        session.last_error_message = error_msg
    
    # Trigger hint after 3 same errors
    if session.consecutive_errors >= 3 and not session.hint_given:
        await trigger_stuck_hint(sid, session_id, session)
```

### **Judge0 Integration**

1. **Submit code** with test cases as additional files
2. **Poll** for results every 1 second (max 30 seconds)
3. **Parse** stdout to count passed tests
4. **Return** execution time, memory, and pass/fail status

### **AI Interviewer Prompting**

The AI agent uses a system prompt that:
- Defines its role as a friendly technical interviewer
- Provides context (current code, recent errors, problem title)
- Instructs it to give hints, not solutions
- Maintains a supportive tone

---

## 🎨 UI/UX Highlights

### **Color Scheme**
- **Background**: Dark gray (`#0d1117`)
- **Panels**: Medium gray (`#161b22`)
- **Accents**: Blue (`#58a6ff`), Green (`#3fb950`), Red (`#f85149`)
- **Borders**: Subtle gray (`#30363d`)

### **Responsive Layout**
- **70/30 split**: Editor (left) vs Chat (right)
- **Resizable console**: Takes 33% of editor height
- **Fixed header**: Problem title, timer, run button

### **Accessibility**
- High contrast text
- Keyboard shortcuts in Monaco
- Clear visual feedback for all actions

---

## 🚀 Next Steps & Enhancements

### **Phase 1 (Current MVP)**
- ✅ Basic AI interviewer
- ✅ Code execution with Judge0
- ✅ Real-time WebSocket communication
- ✅ Paste and tab-switch detection

### **Phase 2 (Future)**
- [ ] **Database persistence** (MongoDB/PostgreSQL)
- [ ] **Multiple problems** with difficulty levels
- [ ] **Audio streaming** for voice interviews
- [ ] **Video recording** (periodic snapshots)
- [ ] **Final report generation** with AI analysis
- [ ] **Admin dashboard** for recruiters
- [ ] **Multi-language support** (Python, Java, C++)

### **Phase 3 (Production)**
- [ ] **Authentication** (OAuth, JWT)
- [ ] **Rate limiting** and abuse prevention
- [ ] **CDN deployment** for global access
- [ ] **Kubernetes** for scalability
- [ ] **Analytics** and performance monitoring

---

## 🐛 Troubleshooting

### **Backend Issues**

#### **"Module not found" errors**
```bash
# Ensure virtual environment is activated
venv\Scripts\activate  # Windows
source venv/bin/activate  # macOS/Linux

# Reinstall dependencies
pip install -r requirements.txt
```

#### **"Azure OpenAI authentication failed"**
- Verify your API key in `.env`
- Check endpoint URL format: `https://YOUR-RESOURCE.openai.azure.com/`
- Ensure deployment name matches your Azure resource

#### **"Judge0 API error"**
- Confirm API key is valid on RapidAPI
- Check rate limits (free tier: 50 requests/day)
- Verify endpoint: `https://judge0-ce.p.rapidapi.com`

### **Frontend Issues**

#### **"WebSocket connection failed"**
- Ensure backend is running on port 8000
- Check `.env.local` has correct `NEXT_PUBLIC_WS_URL`
- Verify CORS settings in backend `config.py`

#### **Monaco Editor not loading**
- Clear Next.js cache: `rm -rf .next`
- Reinstall dependencies: `npm install`
- Check browser console for errors

#### **"Cannot find module '@/...'"**
- Ensure `tsconfig.json` has path alias configured
- Restart Next.js dev server

---

## 📊 Performance Metrics

### **Target Benchmarks**
- **Code execution**: < 5 seconds (including Judge0 polling)
- **WebSocket latency**: < 100ms for code updates
- **AI response time**: < 3 seconds for chat messages
- **Page load**: < 2 seconds (initial render)

### **Optimization Tips**
- Use debouncing (500ms) for code updates
- Implement lazy loading for Monaco Editor
- Cache AI responses for common questions
- Use Redis for session storage in production

---

## 🤝 Contributing

This is a learning project! Feel free to:
- Add new coding problems
- Improve AI prompts
- Enhance UI/UX
- Add more proctoring features
- Write tests

---

## 📄 License

MIT License - Feel free to use this for learning and personal projects!

---

## 🙏 Acknowledgments

- **FastAPI** for the amazing Python framework
- **Next.js** for the best React experience
- **Monaco Editor** for VS Code-quality editing
- **Azure OpenAI** for powerful AI capabilities
- **Judge0** for secure code execution

---

## 📧 Support

If you encounter issues:
1. Check this README's troubleshooting section
2. Review browser console and backend logs
3. Verify all API keys are correctly configured

---

**Built with ❤️ for learning and innovation**

Happy Interviewing! 🎉
