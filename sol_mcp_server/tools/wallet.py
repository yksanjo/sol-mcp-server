"""Wallet analysis tools — comprehensive wallet insights."""

from __future__ import annotations

from datetime import datetime

from mcp.types import Tool, TextContent
from ..clients.solana_rpc import SolanaRPCClient
from ..clients.jupiter import JupiterClient


def get_analyze_tool() -> Tool:
    return Tool(
        name="sol_analyze_wallet",
        description="Get a comprehensive analysis of a Solana wallet — SOL balance, token holdings, transaction history, and estimated value",
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


def get_gas_tool() -> Tool:
    return Tool(
        name="sol_get_gas_price",
        description="Get current Solana network gas fees (priority fees and recent fee data)",
        inputSchema={
            "type": "object",
            "properties": {},
        },
    )


async def handle_analyze(arguments: dict) -> list[TextContent]:
    address = arguments["address"]

    with SolanaRPCClient() as client:
        sol_balance = client.get_balance_sol(address)
        tokens = client.get_token_balances(address)
        txns = client.get_recent_transactions(address, 5)

        # Try to get SOL price
        sol_price = None
        try:
            with JupiterClient() as jup:
                sol_price = jup.get_token_price("So11111111111111111111111111111111111111112")
        except Exception:
            pass

        usd_value = sol_balance * sol_price if sol_price else 0

        result = f"📊 Wallet Analysis: {address}\n"
        result += "━" * 40 + "\n\n"

        result += f"💰 SOL Balance: {sol_balance:.6f} SOL"
        if sol_price:
            result += f" (${usd_value:,.2f} USD)"
        result += "\n"

        result += f"🪙 Token Holdings: {len(tokens)} tokens\n\n"

        if tokens:
            result += "Top Tokens:\n"
            # Sort by UI amount descending
            sorted_tokens = sorted(tokens, key=lambda t: t.get("ui_amount", 0), reverse=True)
            for t in sorted_tokens[:10]:
                ui_amount = t.get("ui_amount", 0)
                mint = t.get("mint", "")[:12]
                if ui_amount > 0:
                    result += f"  • {ui_amount:>12.6f} (mint: {mint}...)\n"

        result += f"\n📋 Recent Transactions ({len(txns)}):\n"
        for txn in txns:
            block_time = txn.get("block_time", 0)
            time_str = datetime.fromtimestamp(block_time).strftime("%m/%d %H:%M") if block_time else "?"
            status = "✅" if txn.get("success") else "❌"
            sig = txn.get("signature", "")[:8]
            result += f"  {status} {sig}... | {time_str}\n"

        return [TextContent(type="text", text=result)]


async def handle_gas(arguments: dict) -> list[TextContent]:
    with SolanaRPCClient() as client:
        try:
            fees = client.get_recent_prioritization_fees()
            if fees:
                recent = fees[:5]
                avg_fee = sum(f.get("prioritizationFee", 0) for f in recent) / len(recent)
                max_fee = max(f.get("prioritizationFee", 0) for f in recent)

                result = "⛽ Solana Network Fees\n\n"
                result += f"  Current Priority Fee (avg): {avg_fee:.0f} microlamports\n"
                result += f"  Current Priority Fee (max): {max_fee:.0f} microlamports\n"
                result += f"  Estimated TX Cost: ~{(avg_fee + 5000) / 1_000_000:.6f} SOL\n"
                result += f"  Estimated TX Cost: ~${(avg_fee + 5000) / 1_000_000 * 150:.4f} USD (at $150/SOL)\n"
            else:
                result = "⛽ Solana Network Fees\n\n  Base fee: 0.000005 SOL\n"
        except Exception:
            result = "⛽ Solana Network Fees\n\n  Base fee: 0.000005 SOL\n"

        return [TextContent(type="text", text=result)]
