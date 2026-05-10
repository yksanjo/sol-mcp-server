"""Price tools — token prices and market data via Jupiter."""

from __future__ import annotations

from mcp.types import Tool, TextContent
from ..clients.jupiter import JupiterClient


def get_price_tool() -> Tool:
    return Tool(
        name="sol_get_token_price",
        description="Get the current USD price of a Solana token by mint address or symbol",
        inputSchema={
            "type": "object",
            "properties": {
                "token": {
                    "type": "string",
                    "description": "Token mint address or symbol (e.g., 'So11111111111111111111111111111111111111112' for SOL, 'BONK', 'USDC')",
                }
            },
            "required": ["token"],
        },
    )


def get_quote_tool() -> Tool:
    return Tool(
        name="sol_get_swap_quote",
        description="Get a swap quote between two tokens on Solana via Jupiter",
        inputSchema={
            "type": "object",
            "properties": {
                "input_token": {
                    "type": "string",
                    "description": "Input token mint address (e.g., 'So11111111111111111111111111111111111111112' for SOL)",
                },
                "output_token": {
                    "type": "string",
                    "description": "Output token mint address",
                },
                "amount": {
                    "type": "number",
                    "description": "Amount of input token to swap (in SOL or token units)",
                },
                "slippage": {
                    "type": "number",
                    "description": "Slippage tolerance in percent (default: 0.5)",
                    "default": 0.5,
                },
            },
            "required": ["input_token", "output_token", "amount"],
        },
    )


def get_search_tool() -> Tool:
    return Tool(
        name="sol_search_token",
        description="Search for a Solana token by symbol or name (e.g., 'SOL', 'USDC', 'BONK', 'JUP')",
        inputSchema={
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Token symbol or name to search for",
                }
            },
            "required": ["query"],
        },
    )


async def handle_price(arguments: dict) -> list[TextContent]:
    token = arguments["token"]

    with JupiterClient() as client:
        # Check if it's a symbol or mint address
        if len(token) < 30:
            # It's a symbol — search for it
            results = client.search_token(token)
            if not results:
                return [TextContent(type="text", text=f"❌ Token '{token}' not found. Try using a mint address.")]

            # Get price for the first result
            mint = results[0]["mint"]
            symbol = results[0]["symbol"]
            name = results[0]["name"]
            price = client.get_token_price(mint)

            if price:
                return [TextContent(type="text", text=f"💵 {name} ({symbol}): ${price:.6f}\n   Mint: {mint}")]
            else:
                return [TextContent(type="text", text=f"ℹ️  {name} ({symbol}) found but no price data available.\n   Mint: {mint}")]
        else:
            # It's a mint address
            price = client.get_token_price(token)
            if price:
                return [TextContent(type="text", text=f"💵 Token Price: ${price:.6f}\n   Mint: {token}")]
            else:
                return [TextContent(type="text", text=f"❌ No price data for mint: {token}")]


async def handle_quote(arguments: dict) -> list[TextContent]:
    input_token = arguments["input_token"]
    output_token = arguments["output_token"]
    amount = arguments["amount"]
    slippage = arguments.get("slippage", 0.5)
    slippage_bps = int(slippage * 100)

    with JupiterClient() as client:
        # Convert SOL amount to lamports if input is SOL mint
        if input_token == "So11111111111111111111111111111111111111112":
            amount_lamports = int(amount * 1_000_000_000)
        else:
            amount_lamports = int(amount * 1_000_000)  # rough estimate for other tokens

        quote = client.get_quote(input_token, output_token, amount_lamports, slippage_bps)

        if not quote:
            return [TextContent(type="text", text="❌ Could not get a quote. Check token addresses and try again.")]

        in_amount = float(quote.get("inAmount", 0)) / 1_000_000_000
        out_amount = float(quote.get("outAmount", 0)) / 1_000_000_000
        price_impact = float(quote.get("priceImpactPct", 0))
        routes = len(quote.get("routePlan", []))

        result = f"🔄 Swap Quote\n\n"
        result += f"  Input:  {amount} SOL ({in_amount:.6f})\n"
        result += f"  Output: {out_amount:.6f}\n"
        result += f"  Price Impact: {price_impact:.2f}%\n"
        result += f"  Routes: {routes}\n"
        result += f"  Slippage: {slippage}%\n"

        return [TextContent(type="text", text=result)]


async def handle_search(arguments: dict) -> list[TextContent]:
    query = arguments["query"]

    with JupiterClient() as client:
        results = client.search_token(query)

        if not results:
            return [TextContent(type="text", text=f"❌ No tokens found matching '{query}'")]

        result = f"🔍 Token Search Results for '{query}'\n\n"
        for r in results[:10]:
            result += f"  • {r['symbol']:8s} | {r['name']:30s} | {r['mint'][:16]}...\n"

        return [TextContent(type="text", text=result)]
