import asyncio


async def debug_agent_invoke(agent_executor, input_text, conversation_id):
    """Debug version that doesn't use streaming"""
    print(f"\n=== DEBUG: Testing agent without streaming ===")
    try:
        response = agent_executor.agent.invoke({
            "input": input_text,
            "chat_history": agent_executor.chat_history,
            "agent_scratchpad": []
        })
        
        print(f"Direct agent response: {response}")
        print(f"Response type: {type(response)}")
        
        if hasattr(response, 'tool_calls'):
            print(f"Tool calls: {response.tool_calls}")
        if hasattr(response, 'content'):
            print(f"Content: {response.content}")
        return response
    except Exception as e:
        print(f"Error in direct agent invoke: {e}")
        import traceback
        traceback.print_exc()
        return None
    
    
    
class DebugQueueCallbackHandler:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.finished = False
    
    def __aiter__(self):
        return self
    
    async def __anext__(self):
        if self.finished and self.queue.empty():
            raise StopAsyncIteration
        
        try:
            item = await asyncio.wait_for(self.queue.get(), timeout=1.0)
            print(f"DEBUG QueueHandler: Got item {repr(item)}")
            return item
        except asyncio.TimeoutError:
            if self.finished:
                raise StopAsyncIteration
            return "<<HEARTBEAT>>"
    
    def on_llm_start(self, serialized, prompts, **kwargs):
        print(f"DEBUG: LLM Start - Prompts: {prompts}")
    
    def on_llm_new_token(self, token, **kwargs):
        print(f"DEBUG: LLM New Token: {repr(token)}")
        asyncio.create_task(self.queue.put(token))
    
    def on_llm_end(self, response, **kwargs):
        print(f"DEBUG: LLM End - Response: {response}")
        if hasattr(response, 'generations') and response.generations:
            for gen in response.generations:
                for g in gen:
                    if hasattr(g, 'message') and hasattr(g.message, 'tool_calls'):
                        print(f"DEBUG: Found tool calls in LLM response: {g.message.tool_calls}")
                        asyncio.create_task(self.queue.put(g.message))
    
    def on_tool_start(self, serialized, input_str, **kwargs):
        print(f"DEBUG: Tool Start - {serialized} with input: {input_str}")
        asyncio.create_task(self.queue.put("<<STEP_END>>"))
    
    def on_tool_end(self, output, **kwargs):
        print(f"DEBUG: Tool End - Output: {output}")
    
    def on_tool_error(self, error, **kwargs):
        print(f"DEBUG: Tool Error: {error}")
    
    def on_chain_start(self, serialized, inputs, **kwargs):
        print(f"DEBUG: Chain Start - {serialized}")
    
    def on_chain_end(self, outputs, **kwargs):
        print(f"DEBUG: Chain End - {outputs}")
    
    def on_agent_action(self, action, **kwargs):
        print(f"DEBUG: Agent Action - {action}")
    
    def on_agent_finish(self, finish, **kwargs):
        print(f"DEBUG: Agent Finish - {finish}")
        self.finished = True