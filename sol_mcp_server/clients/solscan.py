"""Solscan API client — enhanced Solana blockchain data."""

from __future__ import annotations

from typing import Any

import httpx


class SolscanClient:
    """Client for Solscan API — enhanced blockchain data for Solana.

    Provides transaction details, token info, account history,
    and market data that complements the basic RPC.
    """

    def __init__(
        self,
        api_endpoint: str = "https://api.solscan.io",
        timeout: float = 30.0,
    ):
        self.api_endpoint = api_endpoint
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def get_account_transactions(
        self, address: str, limit: int = 10, offset: int = 0
    ) -> list[dict[str, Any]]:
        """Get transaction history for an account.

        Args:
            address: Solana public key
            limit: Number of transactions (max 50)
            offset: Pagination offset

        Returns:
            List of transactions with details.
        """
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/account/transactions",
                params={
                    "address": address,
                    "limit": min(limit, 50),
                    "offset": offset,
                },
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception:
            return []

    def get_account_token_balances(
        self, address: str
    ) -> list[dict[str, Any]]:
        """Get all token balances for an account with metadata.

        Includes token symbol, name, logo, and USD value.
        """
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/account/tokens",
                params={"address": address},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception:
            return []

    def get_token_info(self, token_mint: str) -> dict[str, Any] | None:
        """Get detailed info about a token.

        Args:
            token_mint: Token mint address

        Returns:
            Token info with name, symbol, supply, holders, etc.
        """
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/token/meta",
                params={"token": token_mint},
            )
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception:
            return None

    def get_token_market_data(self, token_mint: str) -> dict[str, Any] | None:
        """Get market data for a token (price, volume, liquidity)."""
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/token/market",
                params={"token": token_mint},
            )
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception:
            return None

    def get_account_info(self, address: str) -> dict[str, Any] | None:
        """Get detailed account info including SOL balance and token count."""
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/account",
                params={"address": address},
            )
            resp.raise_for_status()
            return resp.json().get("data")
        except Exception:
            return None

    def search_account(self, query: str) -> list[dict[str, Any]]:
        """Search for accounts by address or name."""
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/account/search",
                params={"q": query},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception:
            return []

    def get_recent_transactions(
        self, limit: int = 20
    ) -> list[dict[str, Any]]:
        """Get recent transactions across the network."""
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/block/last",
                params={"limit": min(limit, 50)},
            )
            resp.raise_for_status()
            data = resp.json()
            return data.get("data", [])
        except Exception:
            return []

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
