import argparse
import asyncio
import json
import math
import os
from pathlib import Path


MCP_SERVER_URL = "http://127.0.0.1:9000/mcp"


async def check_tools(url: str) -> None:
    from fastmcp import Client

    expected = (
        "cpuName",
        "availableRoot",
        "sizeRoot",
        "kernelVersion",
        "availableRAM",
        "tasks",
        "systemLoad",
    )
    byte_tools = ("availableRoot", "sizeRoot", "availableRAM")
    values = {}
    async with Client(url) as client:
        tools = {tool.name: tool.description for tool in await client.list_tools()}
        for name in expected:
            assert tools.get(name), f"Ferramenta ausente ou sem descrição: {name}"

        for name in expected:
            values[name] = (await client.call_tool(name, {})).data

    for name in ("cpuName", "kernelVersion"):
        assert isinstance(values[name], str) and values[name].strip(), name
    for name in byte_tools:
        size = values[name]
        assert isinstance(size, dict) and set(size) == {"bytes"}, name
        assert type(size["bytes"]) is int and size["bytes"] >= 0, name
    assert values["sizeRoot"]["bytes"] > 0, "sizeRoot"
    assert values["availableRoot"]["bytes"] <= values["sizeRoot"]["bytes"], "availableRoot"
    assert type(values["tasks"]) is int and values["tasks"] > 0, "tasks"
    load = values["systemLoad"]
    assert isinstance(load, dict) and set(load) == {"min_1", "min_5", "min_15"}, "systemLoad"
    assert all(
        type(value) in (int, float) and math.isfinite(value) and value >= 0
        for value in load.values()
    ), "systemLoad"

    for name, value in values.items():
        if name in byte_tools:
            print(f"{name}: {value['bytes'] / 1_000_000_000:.2f} GB")
        else:
            print(f"{name}: {json.dumps(value, ensure_ascii=False)}")
    print("As sete ferramentas MCP passaram na verificação.")


async def create_mcp_agent(url: str = MCP_SERVER_URL):
    from dotenv import load_dotenv
    from langchain.agents import create_agent
    from langchain_mcp_adapters.client import MultiServerMCPClient
    from langchain_openrouter import ChatOpenRouter

    load_dotenv(Path(__file__).with_name(".env"))
    model = ChatOpenRouter(
        model=os.getenv("OPENROUTER_MODEL", "openrouter/free"),
    )

    client = MultiServerMCPClient(
        {
            "service": {
                "url": url,
                "transport": "streamable_http",
            }
        }
    )
    tools = await client.get_tools()

    return create_agent(
        model=model,
        tools=tools,
        system_prompt=(
            "You are a helpful assistant with access to tools provided by an MCP "
            "server. Select and use the appropriate tools whenever they are useful "
            "for answering the user's request."
        ),
    )


async def start(url: str = MCP_SERVER_URL):
    from langchain_core.messages import HumanMessage

    agent = await create_mcp_agent(url)
    messages = []

    print("Type a message. Use 'quit' to stop.")

    while True:
        try:
            user_input = input("> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            break

        if user_input.lower() == "quit":
            break

        if not user_input:
            continue

        messages.append(HumanMessage(content=user_input))
        result = await agent.ainvoke({"messages": messages})
        messages = result["messages"]

        print(messages[-1].content)


def main():
    parser = argparse.ArgumentParser(description="Cliente do servidor MCP de monitoramento.")
    parser.add_argument("--url", default=MCP_SERVER_URL, help="URL do servidor MCP.")
    parser.add_argument("--check", action="store_true", help="Testa diretamente as sete ferramentas.")
    args = parser.parse_args()
    asyncio.run(check_tools(args.url) if args.check else start(args.url))


if __name__ == "__main__":
    main()
