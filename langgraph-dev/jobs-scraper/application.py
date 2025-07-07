from langgraph.graph import StateGraph, END
from agents.job_discovery import JobDiscoveryAgent

builder = StateGraph(dict)

builder.add_node("job_discovery", JobDiscoveryAgent())

builder.set_entry_point("job_discovery")
builder.add_edge("job_discovery", END)

graph = builder.compile()

from IPython.display import Image, display
from PIL import Image
import io
import tempfile
import os
graph_png_bytes = graph.get_graph().draw_mermaid_png()

# Save to a temporary file and open
temp_file = tempfile.NamedTemporaryFile(suffix=".png", delete=False)
temp_file.write(graph_png_bytes)
temp_file.close()

# Open with Pillow (displays in a window)
img = Image.open(temp_file.name)
img.show()

# Optionally delete the temp file later
os.unlink(temp_file.name)