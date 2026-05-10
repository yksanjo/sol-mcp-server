"""Transaction tools — query Solana transaction history."""

from __future__ import annotations

from datetime import datetime

from mcp.types import Tool, TextContent
from ..clients.solana_rpc import SolanaRPCClient


def get_tool() -> Tool:
    return Tool(
        name="sol_get_transactions",
        description="Get recent transaction history for a Solana wallet address",
        inputSchema={
            "type": "object",
            "properties": {
                "address": {
                    "type": "string",
                    "description": "Solana wallet address (base58)",
                },
                "limit": {
                    "type": "integer",
                    "description": "Number of transactions to return (default: 10, max: 50)",
                    "default": 10,
                },
            },
            "required": ["address"],
        },
    )


async def handler(arguments: dict) -> list[TextContent]:
    address = arguments["address"]
    limit = min(arguments.get("limit", 10), 50)

    with SolanaRPCClient() as client:
        txns = client.get_recent_transactions(address, limit)

        if not txns:
            return [TextContent(type="text", text=f"No transactions found for {address}")]

        result = f"📋 Recent Transactions for {address}\n\n"
        for txn in txns:
            block_time = txn.get("block_time", 0)
            time_str = datetime.fromtimestamp(block_time).strftime("%Y-%m-%d %H:%M:%S") if block_time else "Unknown"
            status = "✅" if txn.get("success") else "❌"
            sig = txn.get("signature", "")[:12]
            fee = txn.get("fee", 0)
            result += f"  {status} {sig}... | {time_str} | Fee: {fee:.6f} SOL\n"

        return [TextContent(type="text", text=result)]
