from typing import Annotated
from dotenv import load_dotenv
load_dotenv()
from langchain_tavily import TavilySearch
from langchain_core.messages import ToolMessage
from langchain_core.tools import InjectedToolCallId, tool
from typing_extensions import TypedDict
from langchain.chat_models import init_chat_model
from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langgraph.prebuilt import ToolNode, tools_condition
from langgraph.types import Command, interrupt
from langgraph.types import Interrupt
class State(TypedDict):
    messages: Annotated[list, add_messages]
    name: str
    birthday: str

llm = init_chat_model(model_provider="google-genai",model="gemini-2.0-flash")
@tool
def human_assistance(
    name: str, birthday: str, tool_call_id: Annotated[str, InjectedToolCallId]
) -> str:
    """Request assistance from a human."""
    human_response = interrupt(
        {
            "question": "Is this correct?",
            "name": name,
            "birthday": birthday,
        },
    )
    if human_response.get("correct", "").lower().startswith("y"):
        verified_name = name
        verified_birthday = birthday
        response = "Correct"
    else:
        verified_name = human_response.get("name", name)
        verified_birthday = human_response.get("birthday", birthday)
        response = f"Made a correction: {human_response}"

    state_update = {
        "name": verified_name,
        "birthday": verified_birthday,
        "messages": [ToolMessage(response, tool_call_id=tool_call_id)],
    }
    return Command(update=state_update)


tool = TavilySearch(max_results=2)
tools = [tool, human_assistance]
llm_with_tools = llm.bind_tools(tools)

def chatbot(state: State):
    message = llm_with_tools.invoke(state["messages"])
    assert(len(message.tool_calls) <= 1)
    return {"messages": [message]}

graph_builder = StateGraph(State)
graph_builder.add_node("chatbot", chatbot)

tool_node = ToolNode(tools=tools)
graph_builder.add_node("tools", tool_node)

graph_builder.add_conditional_edges(
    "chatbot",
    tools_condition,
)
graph_builder.add_edge("tools", "chatbot")
graph_builder.add_edge(START, "chatbot")

memory = MemorySaver()
graph = graph_builder.compile(checkpointer=memory)

def stream_graph_updates(user_input: str):
    for event in graph.stream({"messages": [{"role": "user", "content": user_input}]}):
        for value in event.values():
            print("Assistant:", value["messages"][-1].content)
            
            
            
config = {"configurable": {"thread_id": "1"}}
user_input = (
    "Can you look up when LangGraph was released? "
    "When you have the answer, use the human_assistance tool for review."
)
events = graph.stream(
    {"messages": [{"role": "user", "content": user_input}]},
    config,
    stream_mode="values",
)


for step in events:
    for key, value in step.items():
        # 👇 Catch interrupt event
        if isinstance(value, Interrupt):
            print("\n⚠️ INTERRUPT: Human assistance requested!")
            print("Prompt:", value.args.get("question"))
            print("Name:", value.args.get("name"))
            print("Birthday:", value.args.get("birthday"))

            # Ask human via CLI (you can change this to UI, etc.)
            correct = input("Is this info correct? (yes/no): ").strip().lower()
            if correct.startswith("y"):
                human_input = {"correct": "yes"}
            else:
                human_input = {
                    "correct": "no",
                    "name": input("Enter correct name: "),
                    "birthday": input("Enter correct birthday: ")
                }

            # Resume the graph with human input
            print("\n▶ Resuming graph with human response...\n")
            resumed_state = graph.invoke(human_input, config)
            resumed_state["messages"][-1].pretty_print()
            break  # You can exit here or handle more steps if needed

        else:
            # Standard message output
            print('value')
            print(value)