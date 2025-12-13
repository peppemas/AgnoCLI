import asyncio
from textwrap import dedent

from agno.team import Team
from agno.tools.duckduckgo import DuckDuckGoTools
from agno.tools.hackernews import HackerNewsTools

from agnocli.workflows import register_workflow

from agno.agent import Agent
from agno.models.ollama import Ollama
from agno.tools.yfinance import YFinanceTools

# change it if you want to use a different model
OLLAMA_MODEL = "minimax-m2:cloud"
OLLAMA_TEAM_MODEL = "glm-4.6:cloud"

@register_workflow(name="basic", description="Basic flow")
def basic_flow() -> str:
    agent = Agent(
        model=Ollama(id=OLLAMA_MODEL),
        instructions="You are an agent focused on responding in one line. All your responses must be super concise and focused.",
        markdown=True,
    )
    runx = agent.run("How many planets are in the solar system?")
    return runx.content

@register_workflow(name="tools", description="A flow using tools")
def tools_flow() -> str:
    agent = Agent(
        model=Ollama(id=OLLAMA_MODEL),
        tools=[YFinanceTools()],
        instructions=[
            "Use tables to display data.",
            "Only include the table in your response. No other text.",
        ],
        markdown=True,
    )
    agent.print_response("What is the stock price of Unity Technologies?", stream=True)
    return ""

# python.exe -m agnocli run code --arg request="write a simple fibonacci application"
@register_workflow(name="code", description="An agent that writes python code")
def tools_flow(request: str = "create an hello world application") -> str:
    agent = Agent(
        model=Ollama(id=OLLAMA_MODEL),
        instructions=[
            "Write code in python",
            "Add comments and use clean python.",
        ],
        markdown=True,
    )
    agent.print_response(request, stream=True)
    return ""

@register_workflow(name="image", description="Generate prompt images")
def image_flow(request: str = "generate an image of a cat." , style: str = "toon") -> str:
    agent = Agent(
        model=Ollama(id=OLLAMA_MODEL),
        instructions=[
            f"generate a detailed prompt for generating an image using a {style} style",
            "if user ask to generate the image just generate the prompt.",
            "*DO NOT* use tables, list, etc.",
            "*DO NOT* write anything else"
        ],
        markdown=True,
        debug_mode=False,
    )
    agent.print_response(request, stream=True)
    return ""

@register_workflow(name="collaboration", description="An example of collaboration between agents")
def collaboration_flow() -> str:
    reddit_researcher = Agent(
        name="Reddit Researcher",
        role="Research a topic on Reddit",
        model=Ollama(id=OLLAMA_MODEL),
        tools=[DuckDuckGoTools()],
        add_name_to_context=True,
        instructions=dedent("""
        You are a Reddit researcher.
        You will be given a topic to research on Reddit.
        You will need to find the most relevant posts on Reddit.
        """),
    )
    hackernews_researcher = Agent(
        name="HackerNews Researcher",
        model=Ollama(OLLAMA_MODEL),
        role="Research a topic on HackerNews.",
        tools=[HackerNewsTools()],
        add_name_to_context=True,
        instructions=dedent("""
        You are a HackerNews researcher.
        You will be given a topic to research on HackerNews.
        You will need to find the most relevant posts on HackerNews.
        """),
    )
    agent_team = Team(
        name="Discussion Team",
        model=Ollama(OLLAMA_TEAM_MODEL),
        members=[
            reddit_researcher,
            hackernews_researcher,
        ],
        delegate_to_all_members=True,
        instructions=[
            "You are a discussion master.",
            "You have to stop the discussion when you think the team has reached a consensus.",
        ],
        markdown=True,
        show_members_responses=True,
    )
    asyncio.run(
        agent_team.aprint_response(
            input="Start the discussion on the topic: 'What is the best way to learn to code?'",
            stream=True,
        )
    )
    return ""
