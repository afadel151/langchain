from dotenv import load_dotenv 
load_dotenv()
import json

from db import get_conversation, create_conversation, add_message, list_conversations
import asyncio
from langchain_mistralai import ChatMistralAI

from messages import QueueCallbackHandler
import getpass
import os
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import ConfigurableField
from langchain.chat_models import init_chat_model
from agent_tools import add, subtract, multiply, exponential, final_answer, serpapi 
tools = [add, subtract, multiply, exponential, final_answer, serpapi]
name2tool = {tool.name: tool.coroutine for tool in tools}
if "MISTRAL_API_KEY" not in os.environ:
    os.environ["MISTRAL_API_KEY"] = getpass.getpass("Enter your Mistral API key: ")
llm = ChatMistralAI(
        model="mistral-large-latest",
        temperature=0,
        max_retries=2,
    ).configurable_fields(
    callbacks=ConfigurableField(
        id="callbacks",
        name="callbacks",
        description="A list of callbacks to use for streaming",
    )
)
    
llm2 = init_chat_model("gemini-2.0-flash", model_provider="google_genai").configurable_fields(
    callbacks=ConfigurableField(
        id="callbacks",
        name="callbacks",
        description="A list of callbacks to use for streaming",
    )
)

# tool_call = llm.bind_tools(tools).invoke("Explain RAG to me")
# print(tool_call.additional_kwargs["tool_calls"][0]["function"]["arguments"])
# async def tool_exec_content():
#     tool_func = name2tool[tool_call.additional_kwargs["tool_calls"][0]["function"]["name"]]
#     tool_args = json.loads(tool_call.additional_kwargs["tool_calls"][0]["function"]["arguments"])
#     tool_exec_content = await tool_func(**tool_args)
#     return tool_exec_content
# print(asyncio.run(tool_exec_content()))
# print(tool_exec_content)
prompt = ChatPromptTemplate.from_messages([
    ("system", (
        "You're a helpful assistant. When answering a user's question "
        "you should first use one of the tools provided. After using a "
        "tool the tool output will be provided back to you. When you have "
        "all the information you need, you MUST use the final_answer tool "
        "to provide a final answer to the user. Use tools to answer the "
        "user's CURRENT question, not previous questions."
    )),
    MessagesPlaceholder(variable_name="chat_history"),
    ("human", "{input}"),
    MessagesPlaceholder(variable_name="agent_scratchpad"),
])

async def execute_tool(tool_call, name2tool) -> ToolMessage:
    print(f"Starting tool: {tool_call}")
    tool_name = tool_call.tool_calls[0]["name"]
    print(f"Tool name: {tool_name}")
    tool_args = json.loads(tool_call.tool_calls[0]["args"])
    print(f"Tool args: {tool_args}")
    tool_out = await name2tool[tool_name](**tool_args)
    print(f"Tool output: {tool_out}")
    print(f"Finished tool: {tool_call}")
    return ToolMessage(
        content=f"{tool_out}",
        tool_call_id=tool_call['tool_call_id']
    )

class CustomAgentExecutor:
    def __init__(self, max_iterations: int = 5):
        self.chat_history: list[BaseMessage] = []
        self.max_iterations = max_iterations
        self.agent = (
            {
                "input": lambda x: x["input"],
                "chat_history": lambda x: x["chat_history"],
                "agent_scratchpad": lambda x: x.get("agent_scratchpad", [])
            }
            | prompt
            | llm2.bind_tools(tools, tool_choice="any")
        )
    async def invoke(self, input: str,conversation_id: str, streamer: QueueCallbackHandler, verbose: bool = False) -> dict:
        count = 0
        final_answer: str | None = None
        agent_scratchpad: list[AIMessage | ToolMessage ] = []
        async def stream(query: str) -> list[AIMessage]:
            response =  self.agent.with_config(
                callbacks=[streamer]
            )
            # print(f"Streaming response for query: {query}")
            # print(f"Response: {response}")
            outputs = []
            # start streaming
            async for token in response.astream({
                "input": query,
                "chat_history": self.chat_history,
                "agent_scratchpad": agent_scratchpad
            }):
                print(f"Received token: {token}")
                tool_calls = token.tool_calls
                print(f"\nTool calls in token: {tool_calls}")
                if tool_calls:
                    # first check if we have a tool call id - this indicates a new tool
                    if tool_calls[0]["id"]:
                        outputs.append(token)
                        print('Outputs',outputs)
                    else:
                        outputs[-1] += token
                return [
                    AIMessage(
                        content=x.content,
                        tool_calls=x.tool_calls,
                        tool_call_id=x.tool_calls[0]["id"]
                    ) for x in outputs
                ]   
        while count < self.max_iterations:
            # print(f"Iteration {count + 1}")
            #invoke a step for the agent to generate a tool call
            tool_calls = await stream(query=input)
            print(f"Tool calls generated: {tool_calls}")
            for t_call in tool_calls:
                print(f"Tool call ID: {t_call}")
                pass
            # gather tool execution coroutines
            tool_obs = await asyncio.gather(
                *[execute_tool(tool_call,name2tool) for tool_call in tool_calls]
            )
            print(f"Tool observations: {tool_obs}")
            # append tool calls and tool observations to the scratchpad in order
            id2tool_obs = {tool_call.tool_call_id: tool_obs for tool_call, tool_obs in zip(tool_calls, tool_obs)}
            # print(f"ID to tool observations mapping: {id2tool_obs}")
            for tool_call in tool_calls:
                agent_scratchpad.extend([
                    tool_call,
                    id2tool_obs[tool_call.tool_call_id]
                ])
            count += 1
            # if the tool call is the final answer tool, we stop
            found_final_answer = False
            for tool_call in tool_calls:
                if tool_call.tool_calls[0]["name"] == "final_answer":
                    print("Found final answer tool call")
                    final_answer_call = tool_call.tool_calls[0]
                    final_answer = final_answer_call["args"]["answer"]
                    found_final_answer = True
                    add_message(conversation_id, "user", input)
                    add_message(conversation_id, "assistant", final_answer)
                    break
            # Only break the loop if we found a final answer
            if found_final_answer:
                break
                
        # add the final output to the chat history, we only add the "answer" field
        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=final_answer or "No answer found")
        ])
        return final_answer_call if final_answer else {"answer": "No answer found", "tools_used": []}
    
    
agent = CustomAgentExecutor()  