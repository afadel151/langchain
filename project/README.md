# LangChain Conversational AI System

A full-stack conversational AI application built with LangChain, Nuxt.js, FastAPI, and MongoDB.

## 🏗️ Architecture

```
Frontend (Nuxt.js) → API (FastAPI) → LangChain Agent → AI Models
                           ↓
                    MongoDB (Chat History)
```

## ✨ Features

- **Real-time Conversations**: Event streaming for dynamic AI responses
- **Persistent Memory**: MongoDB-backed chat history storage
- **Token Management**: Intelligent token generation and queue handling
- **Async Processing**: Non-blocking conversation flow with asyncio tasks
- **Agent Orchestration**: LangChain agents with custom prompt templates
- **Multi-format Responses**: Handles AImessage, STEP_END, String, and Unknown tokens

## 🛠️ Tech Stack

| Component | Technology |
|-----------|------------|
| **Frontend** | Nuxt.js (Vue.js framework) |
| **Backend** | FastAPI (Python) |
| **Database** | MongoDB |
| **AI Framework** | LangChain |
| **LLM** | Gemini 2.0 Flash |

## 🚀 Getting Started

### Prerequisites
- uv installed 
- Python 3.8+
- Node.js 20+
- MongoDB or Docker image
- Gemini API key
- SerpAPI API key

### Installation

1. **Clone repository**
```bash
git clone https://github.com/afadel151/langchain.git
cd langchain/project
```

2. **Backend setup**
```bash
cd /api
uv sync (or uv pip install -r requirements.txt)
```

3. **Frontend setup**
```bash
cd ../frontend
bun install
```

### Environment Variables

**Backend (.env)**
```env
MONGODB_URI=mongodb://localhost:27017/conversational_ai
GOOGLE_API_KEY=your_gemini_api_key
PORT=8000
SERPAPI_API_KEY=<your_serpapi_api_key>
```

**Frontend (.env)**
```env
GOOGLE_API_KEY=<your_google_api_key>
```

### Running the Application

1. **Start MongoDB**


2. **Start backend**
```bash
cd /api
uvicorn main:app --reload 
```

3. **Start frontend**
```bash
cd frontend
bun dev
```

Access at `http://localhost:3000`

## 📁 Project Structure

```
project/
├── api/
│   ├── main.py              # FastAPI application
│   ├── db.py                # Database logic
│   ├── agent.py             # CustomAgentExecutor logic
│   ├── agent_tools.py       # Agent tools
│   ├── custom_requests.py   # Custom request classes
│   ├── callback.py          # QueueCallbackHandler class
│   ├── stream.py            # token generator logic
│   └── requirements.txt     # Python dependencies
│   └── pyproject.toml       # configuration 
│   └── docker-compose.yml   # Docker compose for MongoDB
├── frontend/
│   ├── pages/               # Nuxt.js pages
│   ├── components/          # Vue components
│   ├── shared/types         # TypeScript interfaces
│   └── package.json         # Node dependencies
└── README.md
```

## 🔄 Data Flow

1. **User Input**: Frontend captures user message
2. **API Call**: Nuxt.js invokes FastAPI endpoint
3. **Token Generation**: System generates conversation tokens
4. **Agent Processing**: LangChain agent processes with custom prompts
5. **Database Storage**: Conversation history saved to MongoDB
6. **Response Streaming**: Real-time response via event streaming
7. **Queue Handling**: Async callback management for smooth UX

## 🎯 Key Components

### Token Generator
Handles multiple response types:
- `AImessage`: AI-generated responses
- `STEP_END`: Process completion markers
- `String`: Text responses
- `Unknown`: Fallback handling

### Agent System
- Custom prompt templates
- Conversation context management
- Integration with Gemini 2.0 Flash
- Async invocation with task queuing

### Database Schema
MongoDB collections for:
- Conversation history

## 🔜 Next Steps

- **LangGraph Integration**: Visual workflow management
- **Multi-agent Orchestration**: Complex reasoning chains
- **Enhanced Memory**: Long-term conversation context
- **Enhanced Streaming**: Due to some issues in streaming

## 📝 API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/` | GET | Cheks for API |
| `/invoke` | POST | Invoke the Agent and stream the output |
| `/create_conversation` | POST | Create a new conversation with a new title |
| `/conversations` | GET | Get a list of existing conversations (titles and ids) |
| `/get_conversation` | GET | Retrieves a conversation by its ID |
| `/get_messages/{conversation_id}` | GET | Retrieves just the messages array for a conversation |

## 🤝 Contributing

1. Fork the repository
2. Create feature branch (`git checkout -b feature/amazing-feature`)
3. Commit changes (`git commit -m 'Add amazing feature'`)
4. Push to branch (`git push origin feature/amazing-feature`)
5. Open Pull Request

## 📄 License

This project is licensed under the MIT License.

## 🙏 Acknowledgments

- LangChain team for the amazing framework
- Google for Gemini API
- FastAPI and Nuxt.js communities