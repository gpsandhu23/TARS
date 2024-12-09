import asyncio
from typing import Annotated, Type

from langchain.tools import BaseTool
from langchain_community.tools import YouTubeSearchTool
from langchain_community.tools.tavily_search import TavilySearchResults
from pydantic import BaseModel, Field


class MultiplyInput(BaseModel):
    a: Annotated[float, Field(description="The first number to multiply")]
    b: Annotated[float, Field(description="The second number to multiply")]


class MultiplyTool(BaseTool):
    name: str = "multiply"
    description: str = "Multiply two numbers together"
    args_schema: Type[BaseModel] = MultiplyInput

    def _run(self, a: float, b: float) -> float:
        """Synchronously multiply two numbers."""
        return a * b

    async def _arun(self, a: float, b: float) -> float:
        """Asynchronously multiply two numbers."""
        return await asyncio.to_thread(self._run, a, b)


multiply_tool = MultiplyTool()


tools = [TavilySearchResults(max_results=1), YouTubeSearchTool(max_results=3)]
