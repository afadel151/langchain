from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel
import uvicorn
from langchain_core.messages import HumanMessage
load_dotenv() 
import asyncio 
from agent import CustomAgentExecutor
from messages import QueueCallbackHandler
from stream import token_generator
from db import create_conversation,list_conversations
from langchain_core.runnables import ConfigurableField
agent_executor = CustomAgentExecutor()
app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"], 
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
llm = ChatMistralAI(
        model="mistral-large-latest",
        temperature=0,
        max_retries=2,
        streaming=True,
    ).configurable_fields(
    callbacks=ConfigurableField(
        id="callbacks",
        name="callbacks",
        description="A list of callbacks to use for streaming",
    )
)
class InvokeRequest(BaseModel):
    content: str
    conversation_id: str
class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"
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
def add_conversation(request: CreateConversationRequest):
    """Creates a new conversation in the database with the given title."""
    print(f"Creating conversation with title: {request.title}")
    conversation_id = create_conversation(request.title)
    return {"conversation_id": conversation_id}

@app.post("/stream")
def stream_response(prompt: str):
    for chunk in llm.stream(prompt):
        print(chunk.content)

@app.get("/conversations")
async def get_conversations():
    """Returns a list of conversations from the database."""
    conversations = list_conversations()
    return  conversations

if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)