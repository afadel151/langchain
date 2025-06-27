from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
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
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
class InvokeRequest(BaseModel):
    content: str
    conversation_id: str
@app.get("/")
def read_root():
    return {"message": "API is running!"}


@app.post("/invoke")
async def invoke(request: InvokeRequest):
    print(f"Received request: {request}")
    queue: asyncio.Queue = asyncio.Queue()
    streamer = QueueCallbackHandler(queue)
    return StreamingResponse(
        token_generator(agent_executor,request.conversation_id,request.content, streamer),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "Connection": "keep-alive",
        }
    )

@app.post("/create_conversation")
def add_conversation(title: str = "New Conversation"):
    """Creates a new conversation in the database with the given title."""
    conversation_id = create_conversation(title)
    return {"conversation_id": conversation_id}
if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)