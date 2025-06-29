from dotenv import load_dotenv 
load_dotenv()
from db import DatabaseConnection
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
    # Extract the first tool call from the AIMessage
    tool_call_data = tool_call.tool_calls[0]
    tool_name = tool_call_data["name"]
    print(f"Tool name: {tool_name}")
    tool_args = tool_call_data["args"]
    print(f"Tool args: {tool_args}")
    tool_out = await name2tool[tool_name](**tool_args)
    print(f"Tool output: {tool_out}")
    print(f"Finished tool: {tool_call}")
    print("Returning ToolMessage")
    return ToolMessage(
            content=f"{tool_out}",
            tool_call_id=tool_call_data["id"]
        )
    
database = DatabaseConnection()
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
    
    async def invoke(self, input: str, conversation_id: str, streamer: QueueCallbackHandler, verbose: bool = False) -> dict:
        print(f"\n=== CustomAgentExecutor.invoke called ===")
        print(f"Input: {input}")
        print(f"Conversation ID: {conversation_id}")
        
        count = 0
        final_answer: str | None = None
        agent_scratchpad: list[AIMessage | ToolMessage] = []
        tools_used = []  # Track tools used for message storage
        steps = []  # Track all steps for Vue component
        
        while count < self.max_iterations:
            print(f"\n=== Iteration {count + 1}/{self.max_iterations} ===")
            
            try:
                # Generate tool calls using streaming
                print("Generating agent response...")
                
                # Use the agent with streaming callbacks
                response = await self.agent.with_config(
                    callbacks=[streamer]
                ).ainvoke({
                    "input": input,
                    "chat_history": self.chat_history,
                    "agent_scratchpad": agent_scratchpad
                })
                
                print(f"Agent response received: {type(response)}")
                print(f"Response tool calls: {getattr(response, 'tool_calls', 'NO TOOL_CALLS')}")
                
                # Convert response to list for compatibility with existing code
                tool_calls = [response] if response.tool_calls else []
                
                if not tool_calls:
                    print("⚠️  No tool calls generated!")
                    break
                
                print(f"Processing {len(tool_calls)} tool calls...")
                
                # Signal that we're starting tool execution
                await streamer.queue.put("<<STEP_END>>")
                
                # Execute tools
                tool_obs = await asyncio.gather(
                    *[execute_tool(tool_call, name2tool) for tool_call in tool_calls]
                )
                
                print(f"Tool execution completed. Observations: {len(tool_obs)}")
                
                # Update agent scratchpad
                id2tool_obs = {tool_ob.tool_call_id: tool_ob for tool_ob in tool_obs}
                
                for tool_call in tool_calls:
                    for tc in tool_call.tool_calls:
                        tool_call_id = tc["id"]
                        agent_scratchpad.extend([
                            tool_call,
                            id2tool_obs[tool_call_id]
                        ])
                        
                        # Track tools used (excluding final_answer for tools_used list)
                        tool_name = tc["name"]
                        tool_args = tc["args"]
                        tool_output = id2tool_obs[tool_call_id].content
                        
                        # Add step for Vue component (includes all tools)
                        step = {
                            "name": tool_name,
                            "result": {**tool_args, "output": tool_output}
                        }
                        steps.append(step)
                        
                        if tool_name != "final_answer":
                            tools_used.append({
                                "name": tool_name,
                                "args": tool_args,
                                "output": tool_output
                            })
                
                count += 1
                
                # Check for final answer
                found_final_answer = False
                for tool_call in tool_calls:
                    for tc in tool_call.tool_calls:
                        if tc["name"] == "final_answer":
                            print("✓ Found final answer tool call")
                            final_answer = tc["args"]["answer"]
                            print(f"Final answer: {final_answer}")
                            found_final_answer = True
                            break
                    if found_final_answer:
                        break
                
                if found_final_answer:
                    break
                    
            except Exception as e:
                print(f"❌ Error in iteration {count + 1}: {e}")
                import traceback
                traceback.print_exc()
                break
        
        # Signal completion
        await streamer.queue.put("<<STEP_END>>")
        
        # Store messages in the desired format (Q&A pairs)
        try:
            # Create Q&A pair object
            qa_pair = {
                "question": input,
                "response": {
                    "answer": final_answer or "No answer found",
                    "tools_used": tools_used,
                    "steps": steps
                }
            }
            
            # Add the Q&A pair to the conversation
            database.add_message(conversation_id, qa_pair)
            
            print(f"Q&A pair stored successfully for conversation {conversation_id}")
        except Exception as e:
            print(f"Error storing Q&A pair: {e}")
        
        # Update chat history
        self.chat_history.extend([
            HumanMessage(content=input),
            AIMessage(content=final_answer or "No answer found")
        ])
        
        result = {"answer": final_answer or "No answer found", "tools_used": tools_used, "steps": steps}
        print(f"=== CustomAgentExecutor.invoke completed. Result: {result} ===")
        return result


agent = CustomAgentExecutor()