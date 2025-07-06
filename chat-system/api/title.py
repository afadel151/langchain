from langchain_huggingface import ChatHuggingFace, HuggingFaceEndpoint
from langchain.chat_models import init_chat_model
chat_model = init_chat_model("gemini-2.0-flash", model_provider="google_genai")

from langchain.prompts import SystemMessagePromptTemplate, HumanMessagePromptTemplate

system_prompt = SystemMessagePromptTemplate.from_template(
    "you are a prompt title generator"
)

user_prompt = HumanMessagePromptTemplate.from_template(
    """You are tasked with generating a maximum 4 words title about this prompt so i use it as a conversation title  
    ----
    {content}
    """,
    input_variables=['content']
)

from langchain.prompts import ChatPromptTemplate
prompt = ChatPromptTemplate.from_messages([system_prompt,user_prompt])

chain = (
    {"content" : lambda x: x["content"]}
    | prompt
    | chat_model
    |{"title": lambda x: x.content}
)