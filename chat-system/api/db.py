from pymongo import MongoClient
from bson.objectid import ObjectId
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from datetime import datetime
from dotenv import load_dotenv 
import os
load_dotenv()


class DatabaseConnection():
    def __init__(self):
        self.client = MongoClient(os.environ["MONGODB_URI"])
        self.conversations = self.client["chat_db"]["conversations"]
    
    def create_conversation(self,title: str) -> str:
        """Create a new conversation"""
        try:
            conversation = {
                "title": title,
                "messages": [],  # Array of Q&A pairs
                "created_at": datetime.utcnow(),
                "updated_at": datetime.utcnow()
            }
            
            result = self.conversations.insert_one(conversation)
            return str(result.inserted_id)
        
        except Exception as e:
            print(f"Error creating conversation: {e}")
            return None

    def serialize_conversation(self,conv):
        conv["_id"] = str(conv["_id"])
        return conv
    def add_message(self,conversation_id: str, qa_pair: dict):
        """Add a Q&A pair to a conversation"""
        try:
            result = self.conversations.update_one(
                {"_id": ObjectId(conversation_id)},
                {"$push": {"messages": qa_pair}, "$set": {"updated_at": datetime.utcnow()}}
            )
            
            if result.modified_count == 0:
                print(f"Warning: No conversation found with ID {conversation_id}")
                return False
                
            print(f"Successfully added Q&A pair to conversation {conversation_id}")
            return True
            
        except Exception as e:
            print(f"Error adding Q&A pair to conversation {conversation_id}: {e}")
            return False
        

    def get_conversation(self,conversation_id: str) -> dict:
        """Get a conversation by ID"""
        try:
            conversation = self.conversations.find_one({"_id": ObjectId(conversation_id)})
            if conversation:
                # Convert ObjectId to string for JSON serialization
                conversation["_id"] = str(conversation["_id"])
                return conversation
            return None
        except Exception as e:
            print(f"Error retrieving conversation {conversation_id}: {e}")
            return None

    def list_conversations(self) -> list:
        """List all conversations"""
        try:
            conversations = list(self.conversations.find({},{
                "title": 1,
                "updated_at" : 1,
                "created_at" : 1,
            }).sort("updated_at",-1))
            for conv in conversations:
                conv["_id"] = str(conv["_id"])
                
            return conversations
        except Exception as e:
            print(f"Error listing conversations: {e}")
            return []

    def load_history(self,conversation_id: str):
        conv = self.get_conversation(conversation_id)
        history = []
        for msg in conv["messages"]:
            if msg["role"] == "user":
                history.append(HumanMessage(content=msg["content"]))
            elif msg["role"] == "assistant":
                history.append(AIMessage(content=msg["content"]))
        return history
    def search_conversations_by_tool(self,tool_name: str) -> list:
        """Find conversations that used a specific tool"""
        try:
            conversations = list(self.conversations.find({
                "messages.response.tools_used.name": tool_name
            }))
            for conv in conversations:
                conv["_id"] = str(conv["_id"])
            return conversations
            
        except Exception as e:
            print(f"Error searching conversations by tool: {e}")
            return []
    def get_conversation_stats(self,conversation_id: str) -> dict:
        """Get statistics about a conversation"""
        try:
            pipeline = [
                {"$match": {"_id": ObjectId(conversation_id)}},
                {"$unwind": "$messages"},
                {"$group": {
                    "_id": "$_id",
                    "total_questions": {"$sum": 1},
                    "tools_used": {"$push": "$messages.response.tools_used"},
                    "avg_steps_per_question": {"$avg": {"$size": "$messages.response.steps"}}
                }}
            ]
            result = list(self.conversations.aggregate(pipeline))
            return result[0] if result else {}
            
        except Exception as e:
            print(f"Error getting conversation stats: {e}")
            return {}