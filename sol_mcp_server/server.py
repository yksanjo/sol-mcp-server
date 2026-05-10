"""Sol MCP Server — The most comprehensive MCP server for Solana.

Run with:
    uvx sol-mcp-server
    # or
    python -m sol_mcp_server.server
"""

import asyncio
from mcp.server import Server
from mcp.server.models import InitializationOptions
from mcp.types import Tool, TextContent

from .tools import balances, transactions, prices, wallet


# Define all tools
TOOLS: list[Tool] = [
    # Balances
    balances.get_tool(),
    balances.get_tokens_tool(),
    # Transactions
    transactions.get_tool(),
    # Prices & Swaps
    prices.get_price_tool(),
    prices.get_quote_tool(),
    prices.get_search_tool(),
    # Wallet Analysis
    wallet.get_analyze_tool(),
    wallet.get_gas_tool(),
]

# Map tool names to handlers
HANDLERS = {
    "sol_get_balance": balances.handle_balance,
    "sol_get_token_accounts": balances.handle_tokens,
    "sol_get_transactions": transactions.handler,
    "sol_get_token_price": prices.handle_price,
    "sol_get_swap_quote": prices.handle_quote,
    "sol_search_token": prices.handle_search,
    "sol_analyze_wallet": wallet.handle_analyze,
    "sol_get_gas_price": wallet.handle_gas,
}


async def main():
    server = Server("sol-mcp-server")

    @server.list_tools()
    async def list_tools() -> list[Tool]:
        return TOOLS

    @server.call_tool()
    async def call_tool(name: str, arguments: dict) -> list[TextContent]:
        handler = HANDLERS.get(name)
        if not handler:
            raise ValueError(f"Unknown tool: {name}")
        return await handler(arguments)

    async with server.run() as running:
        await running.wait_for_shutdown()


if __name__ == "__main__":
    asyncio.run(main())
