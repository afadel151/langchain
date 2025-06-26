from agent import CustomAgentExecutor
from messages import QueueCallbackHandler
import asyncio
# streaming function

async def token_generator(agent_executor: CustomAgentExecutor, conversation_id: str ,content: str, streamer: QueueCallbackHandler):
    print(f"Starting token generation for conversation {conversation_id} ")
    task = asyncio.create_task(agent_executor.invoke(
        content,
        conversation_id,
        streamer=streamer,
        verbose=True  # set to True to see verbose output in console
    ))
    # initialize various components to stream
    async for token in streamer:
        try:
            if token == "<<STEP_END>>":
                # send end of step token
                yield "</step>"
            elif tool_calls := token.message.additional_kwargs.get("tool_calls"):
                if tool_name := tool_calls[0]["function"]["name"]:
                    # send start of step token followed by step name tokens
                    yield f"<step><step_name>{tool_name}</step_name>"
                if tool_args := tool_calls[0]["function"]["arguments"]:
                    # tool args are streamed directly, ensure it's properly encoded
                    yield tool_args
        except Exception as e:
            print(f"Error streaming token: {e}")
            continue
    await task