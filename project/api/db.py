from pymongo import MongoClient
from bson.objectid import ObjectId


client = MongoClient("mongodb://localhost:27017/")
db = client["chat_db"]
conversations = db["conversations"]



def create_conversation(title="New Conversation"):
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



