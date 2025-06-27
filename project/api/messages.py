import asyncio
import json
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import ToolMessage, AIMessage
class QueueCallbackHandler:
    def __init__(self):
        self.queue = asyncio.Queue()
        self.run_inline = True
        self.ignore_chain = False
        self.raise_error = False
        self.ignore_chat_model = False
        self.ignore_llm = False
        self.chain_depth = 0
        self.last_input_hash = None
    async def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            item = await self.queue.get()
            return item
        except:
            raise StopAsyncIteration

    def on_chat_model_start(self, serialized, messages, **kwargs):
        chat_model_name = serialized.get('name', 'unknown') if serialized is not None else 'unknown'
        print(f"💬 Chat Model Start: {chat_model_name}")

    def on_llm_start(self, serialized, prompts, **kwargs):
        llm_name = serialized.get('name', 'unknown') if serialized is not None else 'unknown'
        print(f"🔵 LLM Start: {llm_name}")

    def on_llm_new_token(self, token, **kwargs):
        print(f"🟡 LLM Token: {repr(token)}")
        asyncio.create_task(self.queue.put(token))

    def on_llm_end(self, response, **kwargs):
        print(f"🟢 LLM End: {type(response)}")
        if hasattr(response, 'generations') and response.generations:
            for generation_list in response.generations:
                for generation in generation_list:
                    if hasattr(generation, 'message'):
                        print(f"🔧 Found message with tool calls: {generation.message.tool_calls}")
                        asyncio.create_task(self.queue.put(generation.message))

    def on_tool_start(self, serialized, input_str, **kwargs):
        tool_name = serialized.get('name', 'unknown') if serialized is not None else 'unknown'
        print(f"🔨 Tool Start: {tool_name}")
        asyncio.create_task(self.queue.put(f"<step><step_name>{tool_name}</step_name>"))

    def on_tool_end(self, output, **kwargs):
        print(f"✅ Tool End: {type(output)}")
        asyncio.create_task(self.queue.put(str(output)))

    def on_chain_start(self, serialized, inputs, **kwargs):
        input_hash = hash(json.dumps(inputs, sort_keys=True))
        if self.last_input_hash == input_hash:
            return
        self.last_input_hash = input_hash
        print(f"⛓️ Chain Start: {serialized.get('name', 'unknown') if serialized else 'unknown'}, inputs={inputs}")

    def on_chain_end(self, outputs, **kwargs):
        print(f"{'  ' * self.chain_depth}🏁 Chain End: outputs={outputs}")
        self.chain_depth = max(0, self.chain_depth - 1)

    def on_agent_action(self, action, **kwargs):
        print(f"🤖 Agent Action: {action.tool}")
        asyncio.create_task(self.queue.put(f"<agent_action>{action.tool}</agent_action>"))

    def on_agent_finish(self, finish, **kwargs):
        print(f"🎯 Agent Finish: {finish.return_values}")
        asyncio.create_task(self.queue.put(f"<final_answer>{finish.return_values}</final_answer>"))
