# this file contains tools for our Agent to use.
import asyncio
from langchain_core.tools import tool
from dotenv import load_dotenv
import aiohttp
load_dotenv()
import os


from pydantic import BaseModel
class Article(BaseModel):
    """
    Used for parsing serpapi results for articles.
    This is used to extract the title, source, link, and snippet from the
    serpapi results for articles.
    """
    title: str
    source: str
    link: str
    snippet: str

    @classmethod
    def from_serpapi_result(cls, result: dict) -> "Article":
        return cls(
            title=result["title"],
            source=result["source"],
            link=result["link"],
            snippet=result["snippet"],
        )
        
        
@tool
async def add(x: float, y: float) -> float:
    """Add 'x' and 'y'."""
    return x + y

@tool
async def multiply(x: float, y: float) -> float:
    """Multiply 'x' and 'y'."""
    return x * y

@tool
async def exponential(x: float, y: float) -> float:
    """Raise 'x' to the power of 'y'."""
    return x ** y

@tool
async def subtract(x: float, y: float) -> float:
    """Subtract 'x' from 'y'."""
    return y - x

@tool
async def serpapi(query: str) -> list[Article]:
    """Use this tool to search the web."""
    params = {
        "api_key":os.getenv("SERPAPI_API_KEY"),
        "engine": "google",
        "q": query,
    }
    async with aiohttp.ClientSession() as session:
        async with session.get(
            "https://serpapi.com/search",
            params=params
        ) as response:
            results = await response.json()
    return [Article.from_serpapi_result(result) for result in results["organic_results"]]



@tool
async def final_answer(answer: str, tools_used: list[str]) -> dict[str, str | list[str]]:
    """Use this tool to provide a final answer to the user."""
    return {"answer": answer, "tools_used": tools_used}



