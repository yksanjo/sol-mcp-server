"""Solana RPC client — direct interaction with Solana nodes."""

from __future__ import annotations

import json
from typing import Any

import httpx


class SolanaRPCClient:
    """Client for interacting with Solana RPC nodes.

    Handles account queries, balance checks, token accounts,
    transaction data, and program interactions.
    """

    def __init__(
        self,
        rpc_endpoint: str = "https://api.mainnet-beta.solana.com",
        timeout: float = 30.0,
    ):
        self.rpc_endpoint = rpc_endpoint
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def _call(self, method: str, params: list[Any] | None = None) -> dict[str, Any]:
        """Make a JSON-RPC call to the Solana node."""
        payload = {
            "jsonrpc": "2.0",
            "id": 1,
            "method": method,
            "params": params or [],
        }
        resp = self._client.post(
            self.rpc_endpoint,
            json=payload,
            headers={"Content-Type": "application/json"},
        )
        resp.raise_for_status()
        data = resp.json()
        if "error" in data:
            raise Exception(f"Solana RPC error: {data['error']}")
        return data["result"]

    def get_balance(self, address: str) -> int:
        """Get SOL balance in lamports for an address.

        Args:
            address: Solana public key (base58)

        Returns:
            Balance in lamports (1 SOL = 1_000_000_000 lamports)
        """
        return self._call("getBalance", [address])

    def get_balance_sol(self, address: str) -> float:
        """Get SOL balance in SOL (not lamports)."""
        result = self.get_balance(address)
        if isinstance(result, dict):
            return result.get("value", 0) / 1_000_000_000
        return result / 1_000_000_000

    def get_token_accounts_by_owner(
        self, owner: str
    ) -> list[dict[str, Any]]:
        """Get all token accounts owned by an address.

        Args:
            owner: Solana public key

        Returns:
            List of token account data with mint, balance, and decimals.
        """
        result = self._call(
            "getTokenAccountsByOwner",
            [
                owner,
                {"programId": "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"},
                {"encoding": "jsonParsed"},
            ],
        )
        return result.get("value", [])

    def get_token_balances(
        self, owner: str
    ) -> list[dict[str, Any]]:
        """Get all token balances for an owner with human-readable amounts.

        Returns:
            List of {mint, symbol, amount, decimals, ui_amount}
        """
        accounts = self.get_token_accounts_by_owner(owner)
        balances = []
        for acc in accounts:
            account_data = acc.get("account", {}).get("data", {}).get("parsed", {}).get("info", {})
            token_amount = account_data.get("tokenAmount", {})
            mint = account_data.get("mint", "")
            amount = int(token_amount.get("amount", "0"))
            decimals = token_amount.get("decimals", 0)
            ui_amount = token_amount.get("uiAmount", 0)

            balances.append({
                "mint": mint,
                "amount": amount,
                "decimals": decimals,
                "ui_amount": ui_amount,
                "address": acc.get("pubkey", ""),
            })
        return balances

    def get_signatures_for_address(
        self, address: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent transaction signatures for an address."""
        return self._call(
            "getSignaturesForAddress",
            [address, {"limit": limit}],
        )

    def get_transaction(
        self, signature: str
    ) -> dict[str, Any] | None:
        """Get detailed transaction data for a signature."""
        try:
            return self._call(
                "getTransaction",
                [signature, {"encoding": "jsonParsed", "maxSupportedTransactionVersion": 0}],
            )
        except Exception:
            return None

    def get_recent_transactions(
        self, address: str, limit: int = 10
    ) -> list[dict[str, Any]]:
        """Get recent transactions with details for an address."""
        sigs = self.get_signatures_for_address(address, limit)
        txns = []
        for sig_info in sigs:
            sig = sig_info.get("signature", "")
            txn = self.get_transaction(sig)
            if txn:
                txns.append({
                    "signature": sig,
                    "slot": txn.get("slot", 0),
                    "block_time": txn.get("blockTime", 0),
                    "success": not txn.get("meta", {}).get("err"),
                    "fee": txn.get("meta", {}).get("fee", 0) / 1_000_000_000,
                    "signer": txn.get("transaction", {}).get("message", {}).get("accountKeys", [{}])[0].get("pubkey", ""),
                })
        return txns

    def get_token_supply(self, mint: str) -> dict[str, Any]:
        """Get the total supply of a token."""
        return self._call("getTokenSupply", [mint])

    def get_latest_blockhash(self) -> str:
        """Get the latest blockhash."""
        result = self._call("getLatestBlockhash")
        return result.get("value", {}).get("blockhash", "")

    def get_fee_for_message(self, message: str) -> int:
        """Get fee for a transaction message."""
        return self._call("getFeeForMessage", [message])

    def get_recent_prioritization_fees(self) -> list[dict[str, Any]]:
        """Get recent prioritization fees."""
        return self._call("getRecentPrioritizationFees")

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
