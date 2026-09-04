# Load libraries
import sys
import os
from dotenv import load_dotenv
import asyncio

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_agent
from langchain.messages import HumanMessage
from langchain_mcp_adapters.client import MultiServerMCPClient

# Now this will correctly pull from your local scripts folder
from agent_script import prompts

load_dotenv()

# # Airbnb MCP Prompt
# AIRBNB_PROMPT = """
# You are a travel planning assistant.

# Instructions:
# - Seaech Airbnb listings immediately when user asks for accommodations
# - Use defaults: adults=2, no dates if not specified
# - Present top 5 results with link: https://www.airbnb.com/rooms/{listing_id}
# - Be proactive, don't ask for details unless search fails
# """

# Set the GEMINI_API_KEY environment variable from the .env file
GEMINI_API_KEY = os.environ["GEMINI_API_KEY"] = os.getenv("GEMINI_API_KEY")


# Set UTF-8 encoding for Windows console
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding='utf-8')

model = ChatGoogleGenerativeAI(
    model="gemini-2.5-flash",
    api_key=GEMINI_API_KEY,
    temperature=0.2,
    max_output_tokens=1024,
    top_p=0.95,
    top_k=40,
    stop=None,
)

async def get_mcp_tools():
    client = MultiServerMCPClient({ 
        "airbnb": { 
            "command": "npx", 
            "args": ["-y", "@openbnb/mcp-server-airbnb", "--ignore-robots-txt"], 
            "transport": "stdio" 
        }
    })

    mcp_tools = await client.get_tools()

    print("number of tools loaded: ", len(mcp_tools))
    print("available tools: ", [tool.name for tool in mcp_tools])

    return mcp_tools

async def hotel_search():
    tools = await get_mcp_tools()

    hotel_agent = create_agent(
        model=model,
        tools=tools,
        system_prompt=AIRBNB_PROMPT
    )

    # Keep conversation history so the agent has context across turns
    conversation_history = []

    print("\nHotel search assistant. Type 'quit' or 'exit' to stop.\n")

    query = input("What would you like to search for? ")

    while query.lower() not in ("quit", "exit"):
        conversation_history.append(HumanMessage(content=query))

        result = await hotel_agent.ainvoke({"messages": conversation_history})

        # Keep the full updated message list so the agent remembers prior turns
        conversation_history = result["messages"]

        response = conversation_history[-1].content

        print("\n============ Output ============\n")
        print(response)
        print("\n=================================\n")

        query = input("What would you like to do next? ")

    print("Goodbye!")


if __name__ == "__main__":
    asyncio.run(hotel_search())






