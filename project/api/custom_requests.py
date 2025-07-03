from pydantic import BaseModel


class InvokeRequest(BaseModel):
    content: str
    conversation_id: str
class CreateConversationRequest(BaseModel):
    title: str = "New Conversation"
    
class GetConversationRequest(BaseModel):
    conversation_id: str
    
class CreateTitleRequest(BaseModel):
    content : str