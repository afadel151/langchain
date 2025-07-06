from fastapi import APIRouter
from pydantic import BaseModel
import asyncio
from callback import QueueCallbackHandler
from debug import DebugQueueCallbackHandler
from debug import debug_agent_invoke
from langchain_core.messages import AIMessage

router = APIRouter()
from agent import CustomAgentExecutor, agent_executor, execute_tool
class InvokeRequest(BaseModel):
    content: str
    conversation_id: str
from agent_tools import add, subtract, multiply, exponential, final_answer, serpapi 
tools = [add, subtract, multiply, exponential, final_answer, serpapi]
name2tool = {tool.name: tool.coroutine for tool in tools}
@router.post("/debug-invoke")
async def debug_invoke(request: InvokeRequest):
    """Debug endpoint to test agent without streaming complications"""
    print(f"=== DEBUG INVOKE ===")
    print(f"Request: {request}")
    direct_result = await debug_agent_invoke(agent_executor, request.content, request.conversation_id)
    debug_streamer = DebugQueueCallbackHandler()
    
    try:
        task = asyncio.create_task(agent_executor.invoke(
            request.content,
            request.conversation_id,
            streamer=debug_streamer,
            verbose=True
        ))
        tokens = []
        async for token in debug_streamer:
            if token == "<<HEARTBEAT>>":
                continue
            tokens.append(token)
            if len(tokens) > 20: 
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
@router.get("/test-tools")
async def test_tools():
    """Test if your tools are working"""
    print("=== TESTING TOOLS ===")
    if 'tools' in globals() and tools:
        print(f"Available tools: {[tool.name for tool in tools]}")
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
        
async def enhanced_token_generator(agent_executor: CustomAgentExecutor, conversation_id: str, content: str, streamer: QueueCallbackHandler):
    print(f"=== ENHANCED TOKEN GENERATOR START ===")
    print("Testing direct agent invocation...")
    try:
        direct_response = agent_executor.agent.invoke({
            "input": content,
            "chat_history": agent_executor.chat_history,
            "agent_scratchpad": []
        })
        print(f"Direct response successful: {type(direct_response)}")
        print(f"Direct response content: {getattr(direct_response, 'content', 'NO CONTENT')}")
        print(f"Direct response tool_calls: {getattr(direct_response, 'tool_calls', 'NO TOOL_CALLS')}")
    except Exception as e:
        print(f"Direct agent invocation failed: {e}")
        yield f"Error: Direct agent invocation failed: {str(e)}"
        return
    
    # Now test streaming
    print("Testing streaming invocation...")
    task = asyncio.create_task(agent_executor.invoke(
        content,
        conversation_id,
        streamer=streamer,
        verbose=True
    ))
    
    token_count = 0
    start_time = asyncio.get_event_loop().time()
    
    try:
        async for token in streamer:
            token_count += 1
            elapsed = asyncio.get_event_loop().time() - start_time
            
            print(f"\n[{elapsed:.2f}s] Token #{token_count}: {repr(token)}")
            
            if token == "<<STEP_END>>":
                yield "</step>"
            elif hasattr(token, 'content') and token.content:
                yield f"<content>{token.content}</content>"
            else:
                yield f"<unknown>{str(token)}</unknown>"
            if token_count > 100:
                print("⚠️  Too many tokens, breaking")
                break
    except Exception as e:
        print(f"Error in streaming: {e}")
        yield f"<error>{str(e)}</error>"
    
    finally:
        try:
            await task
        except Exception as e:
            print(f"Task completion error: {e}")
    
    print(f"=== ENHANCED TOKEN GENERATOR END (Total tokens: {token_count}) ===")