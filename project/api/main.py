from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
load_dotenv() 
import asyncio 
from agent import CustomAgentExecutor
from messages import QueueCallbackHandler
from stream import token_generator
from db import create_conversation
agent_executor = CustomAgentExecutor()
app = FastAPI()
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # ou ["*"] pour tout autoriser
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
def read_root():
    return {"message": "API is running!"}


@app.post("/invoke")
async def invoke(content: str):
    queue: asyncio.Queue = asyncio.Queue()
    streamer = QueueCallbackHandler(queue)
    # return the streaming response
    return StreamingResponse(
        token_generator(agent_executor,content, streamer),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/create_conversation")
def create_conversation(title: str = "New Conversation"):
    """Creates a new conversation in the database with the given title."""
    conversation_id = create_conversation(title)
    return {"conversation_id": conversation_id}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)