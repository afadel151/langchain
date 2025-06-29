from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from langchain_mistralai import ChatMistralAI
from pydantic import BaseModel
import uvicorn
from custom_requests import InvokeRequest, CreateConversationRequest, GetConversationRequest
from debug import DebugQueueCallbackHandler, debug_agent_invoke
load_dotenv() 
import asyncio 
from agent import CustomAgentExecutor, execute_tool
from messages import QueueCallbackHandler
from stream import token_generator
from langchain_core.runnables import ConfigurableField
from langchain_core.messages import AIMessage
from db import DatabaseConnection
database = DatabaseConnection()
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
    
from agent_tools import add, subtract, multiply, exponential, final_answer, serpapi 
tools = [add, subtract, multiply, exponential, final_answer, serpapi]
name2tool = {tool.name: tool.coroutine for tool in tools}

    

@app.get("/")
def read_root():
    return {"message": "API is running!"}


@app.post("/invoke")
async def invoke_fixed(request: InvokeRequest):
    print(f"Fixed invoke called: {request}")
    
    # Use the improved callback handler
    streamer = QueueCallbackHandler()
    
    return StreamingResponse(
        token_generator(agent_executor, request.conversation_id, request.content, streamer),
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
    conversation_id = database.create_conversation(request.title)
    return {"conversation_id": conversation_id}




    
    
@app.post("/stream")
def stream_response(prompt: str):
    for chunk in llm.stream(prompt):
        print(chunk.content)

@app.get("/conversations")
def get_conversations():
    """Returns a list of conversations from the database."""
    conversations =  database.list_conversations()
    return  conversations


@app.get("/get_conversation")
def get_conversation_by_id(conversation_id: str):
    """Retrieves a conversation by its ID."""
    print(f"Retrieving conversation with ID: {conversation_id}")
    conversation = database.get_conversation(conversation_id)
    if not conversation:
        return {"error": "Conversation not found"}
    
    # Return the messages array which now contains Q&A pairs
    return {
        "conversation_id": conversation["_id"],
        "title": conversation.get("title", "Untitled"),
        "messages": conversation.get("messages", []),
        "created_at": conversation.get("created_at"),
        "updated_at": conversation.get("updated_at")
    }
@app.get("/get_messages/{conversation_id}")
def get_messages_only(conversation_id: str):
    """Retrieves just the messages array for a conversation."""
    conversation = database.get_conversation(conversation_id)
    if not conversation:
        return {"error": "Conversation not found"}
    
    return conversation.get("messages", [])
@app.get("/conversation_stats/{conversation_id}")
def get_conversation_statistics(conversation_id: str):
    """Get statistics about a conversation."""
    stats = database.get_conversation_stats(conversation_id)
    return stats


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8000)
    
    
    



@app.post("/debug-invoke")
async def debug_invoke(request: InvokeRequest):
    """Debug endpoint to test agent without streaming complications"""
    print(f"=== DEBUG INVOKE ===")
    print(f"Request: {request}")
    
    # Test direct agent invocation
    direct_result = await debug_agent_invoke(agent_executor, request.content, request.conversation_id)
    
    # Test with debug callback handler
    debug_streamer = DebugQueueCallbackHandler()
    
    try:
        # Run agent with debug callback
        task = asyncio.create_task(agent_executor.invoke(
            request.content,
            request.conversation_id,
            streamer=debug_streamer,
            verbose=True
        ))
        
        # Collect all tokens
        tokens = []
        async for token in debug_streamer:
            if token == "<<HEARTBEAT>>":
                continue
            tokens.append(token)
            if len(tokens) > 20:  # Prevent infinite loop
                break
        
        result = await task
        
        return {
            "direct_result": str(direct_result),
            "tokens_received": [str(t) for t in tokens],
            "final_result": str(result)
        }
        
    except Exception as e:
        print(f"Error in debug invoke: {e}")
        import traceback
        traceback.print_exc()
        return {"error": str(e)}
    

# Simple test endpoint
@app.get("/test-tools")
async def test_tools():
    """Test if your tools are working"""
    print("=== TESTING TOOLS ===")
    
    # Test tool execution directly
    if 'tools' in globals() and tools:
        print(f"Available tools: {[tool.name for tool in tools]}")
        
        # Try to create a fake tool call for testing
        fake_ai_message = AIMessage(
            content="",
            tool_calls=[{
                "id": "test_123",
                "name": tools[0].name if tools else "unknown",
                "args": {"query": "test query"}
            }]
        )
        
        try:
            result = await execute_tool(fake_ai_message, name2tool)
            return {
                "tools_available": [tool.name for tool in tools],
                "test_execution": str(result)
            }
        except Exception as e:
            return {
                "tools_available": [tool.name for tool in tools],
                "test_execution_error": str(e)
            }
    else:
        return {"error": "No tools found"}
    