from langchain.chat_models import init_chat_model
from dotenv import load_dotenv 
load_dotenv()

import asyncio
import aiohttp


from langchain.callbacks.base import AsyncCallbackHandler
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage, ToolMessage
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import ConfigurableField
from langchain_core.tools import tool

llm = init_chat_model("gemini-2.0-flash", model_provider="google_genai")