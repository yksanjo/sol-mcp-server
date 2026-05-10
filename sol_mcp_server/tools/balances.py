"""Balance tools — check SOL and token balances."""

from __future__ import annotations

from mcp.types import Tool, TextContent
from ..clients.solana_rpc import SolanaRPCClient


def get_tool() -> Tool:
    return Tool(
        name="sol_get_balance",
        description="Get SOL and token balances for a Solana wallet address",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Solana wallet address (base58)",
                }
            },
            "required": ["address"],
        },
    )


def get_tokens_tool() -> Tool:
    return Tool(
        name="sol_get_token_accounts",
        description="Get all token holdings for a Solana wallet address",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Solana wallet address (base58)",
                }
            },
            "required": ["address"],
        },
    )


async def handle_balance(arguments: dict) -> list[TextContent]:
    address = arguments["address"]
    with SolanaRPCClient() as client:
        sol_balance = client.get_balance_sol(address)
        result = f"💰 SOL Balance: {sol_balance:.6f} SOL\n"
        result += f"   Address: {address}\n"
        return [TextContent(type="text", text=result)]


async def handle_tokens(arguments: dict) -> list[TextContent]:
    address = arguments["address"]
    with SolanaRPCClient() as client:
        tokens = client.get_token_balances(address)
        if not tokens:
            return [TextContent(type="text", text=f"No token holdings found for {address}")]

        result = f"🪙 Token Holdings for {address}\n\n"
        for t in tokens[:20]:
            ui_amount = t.get("ui_amount", 0)
            mint = t.get("mint", "")[:12]
            result += f"  • {ui_amount:>12.6f} (mint: {mint}...)\n"

        if len(tokens) > 20:
            result += f"\n... and {len(tokens) - 20} more tokens"

        return [TextContent(type="text", text=result)]
