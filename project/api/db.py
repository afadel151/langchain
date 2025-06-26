from pymongo import MongoClient
from bson.objectid import ObjectId
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage

client = MongoClient("mongodb://root:root@localhost:27017/")
db = client["chat_db"]
conversations = db["conversations"]



def create_conversation(title="New Conversation"):
    """Creates a new conversation in the database with the given title.
    
    Returns:
        str: The string representation of the inserted conversation's ObjectId.
    """
    result = conversations.insert_one({
        "title": title,
        "messages": []
    })
    return str(result.inserted_id)


def add_message(conversation_id: str, role: str, content: str, **kwargs):
    msg = {"role": role, "content": content} | kwargs
    conversations.update_one(
        {"_id": ObjectId(conversation_id)},
        {"$push": {"messages": msg}}
    )
def get_conversation(conversation_id: str):
    return conversations.find_one({"_id": ObjectId(conversation_id)})

def list_conversations():
    return list(conversations.find({}, {"messages": 0}))



def load_history(conversation_id: str):
    conv = get_conversation(conversation_id)
    history = []
    for msg in conv["messages"]:
        if msg["role"] == "user":
            history.append(HumanMessage(content=msg["content"]))
        elif msg["role"] == "assistant":
            history.append(AIMessage(content=msg["content"]))
        # You can also handle tool messages here if needed
    return history


