import json
import asyncio
from langchain_core.messages import AIMessage

from agent import CustomAgentExecutor
from messages import QueueCallbackHandler

async def token_generator(agent_executor: CustomAgentExecutor, conversation_id: str, content: str, streamer: QueueCallbackHandler):
    print(f"=== Starting token generation for conversation {conversation_id} ===")
    task = asyncio.create_task(agent_executor.invoke(
        content,
        conversation_id,
        streamer=streamer,
        verbose=True
    ))
    print("task created  now listening for tokens ")
    current_step_name = None
    step_buffer = ""
    token_count = 0
    try:
        while not task.done():
            try:
                token = await asyncio.wait_for(streamer.queue.get(), timeout=1.0)
                token_count += 1
                print(f"\n--- Token #{token_count} ---")
                print(f"Received: {repr(token)}")
                if token == "<<STEP_END>>":
                    print("Step end detected")
                    if current_step_name and step_buffer:
                        yield step_buffer
                        yield "</step>"
                        step_buffer = ""
                    current_step_name = None
                elif isinstance(token, AIMessage) and token.tool_calls:
                    print(f"Processing tool call message: {token.tool_calls}")
                    for tool_call in token.tool_calls:
                        tool_name = tool_call.get("name", "unknown")
                        tool_args = tool_call.get("args", {})
                        print(f"Tool: {tool_name}, Args: {tool_args}")
                        current_step_name = tool_name
                        step_start = f"<step><step_name>{tool_name}</step_name>"
                        print(f"Yielding: {repr(step_start)}")
                        yield step_start
                        if tool_args:
                            args_json = json.dumps(tool_args, ensure_ascii=False)
                            step_buffer = args_json
                            print(f"Buffering args: {repr(args_json)}")
                            yield args_json
                elif isinstance(token, str):
                    print(f"String token: {repr(token)}")
                    if current_step_name:
                        step_buffer += token
                    yield token
                
                else:
                    token_str = str(token)
                    print(f"Unknown token: {repr(token_str)}")
                    if current_step_name:
                        step_buffer += token_str
                    yield token_str
            except asyncio.TimeoutError:
                if task.done():
                    print("Task completed, breaking from token loop")
                    break
                else:
                    print("Timeout waiting for token, continuing...")
                    continue
                    
    except Exception as e:
        print(f"❌ Error in token generator: {e}")
        import traceback
        traceback.print_exc()
    
    finally:
        if not task.done():
            print("Waiting for task to complete...")
            try:
                result = await asyncio.wait_for(task, timeout=5.0)
                print(f"Task completed with result: {result}")
            except asyncio.TimeoutError:
                print("Task completion timeout")
                task.cancel()
        if current_step_name and step_buffer:
            yield step_buffer
            yield "</step>"
        
        print(f"=== Token generation completed. Total tokens: {token_count} ===")