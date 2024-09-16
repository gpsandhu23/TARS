from langchain_community.tools.tavily_search import TavilySearchResults
from langchain_community.tools import YouTubeSearchTool


# Add custom langchain tool to multiply two numbers
from langchain.tools import BaseTool
from pydantic import BaseModel, Field
from typing import Type


class MultiplyInput(BaseModel):
    a: float = Field(..., description="The first number to multiply")
    b: float = Field(..., description="The second number to multiply")


class MultiplyTool(BaseTool):
    name: str = Field(default="multiply")
    description: str = Field(default="Multiply two numbers together")
    args_schema: Type[BaseModel] = Field(default=MultiplyInput)

    def _run(self, a: float, b: float) -> float:
        return a * b

    def _arun(self, a: float, b: float) -> float:
        return self._run(a, b)


multiply_tool = MultiplyTool()



tools = [TavilySearchResults(max_results=1), multiply_tool, YouTubeSearchTool(max_results=3)]