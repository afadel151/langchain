from langgraph.graph import StateGraph, END
from agents.job_discovery import JobDiscoveryAgent

builder = StateGraph(dict)

builder.add_node("job_discovery", JobDiscoveryAgent())

builder.set_entry_point("job_discovery")
builder.add_edge("job_discovery", END)

graph = builder.compile()

result = graph.invoke({"query": "Python Developer", "location": "Remote"})
print(result["jobs"])