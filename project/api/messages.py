import asyncio
from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import ToolMessage, AIMessage


class QueueCallbackHandler(AsyncCallbackHandler):
    def __init__(self, queue: asyncio.Queue):
        self.queue = queue
        self.final_answer_seen = False

    async def __aiter__(self):
        while True:
            if self.queue.empty():
                await asyncio.sleep(0.1)
                continue
            token_or_done = await self.queue.get()
            if token_or_done == "<<DONE>>":
                return
            if token_or_done:
                yield token_or_done

    async def on_llm_new_token(self, *args, **kwargs) -> None:
        chunk = kwargs.get("chunk")
        if (
            chunk
            and chunk.message.additional_kwargs.get("tool_calls")
            and chunk.message.additional_kwargs["tool_calls"][0]["function"]["name"] == "final_answer"
        ):
            self.final_answer_seen = True
        self.queue.put_nowait(kwargs.get("chunk"))

    async def on_llm_end(self, *args, **kwargs) -> None:
        if self.final_answer_seen:
            self.queue.put_nowait("<<DONE>>")
        else:
            self.queue.put_nowait("<<STEP_END>>")


async def execute_tool(tool_call: AIMessage, name2tool: dict) -> ToolMessage:
    tool_name = tool_call.tool_calls[0]["name"]
    tool_args = tool_call.tool_calls[0]["args"]
    tool_out = await name2tool[tool_name](**tool_args)
    return ToolMessage(
        content=f"{tool_out}",
        tool_call_id=tool_call.tool_calls[0]["id"]
    )


