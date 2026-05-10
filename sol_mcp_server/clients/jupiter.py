"""Jupiter API client — token prices, swap quotes, and DEX data on Solana."""

from __future__ import annotations

from typing import Any

import httpx


class JupiterClient:
    """Client for Jupiter Aggregator API on Solana.

    Provides token prices, swap quotes, and DEX routing.
    Jupiter is the leading DEX aggregator on Solana.
    """

    def __init__(
        self,
        api_endpoint: str = "https://quote-api.jup.ag/v6",
        price_endpoint: str = "https://price.jup.ag/v6",
        timeout: float = 30.0,
    ):
        self.api_endpoint = api_endpoint
        self.price_endpoint = price_endpoint
        self.timeout = timeout
        self._client = httpx.Client(timeout=timeout)

    def get_token_price(self, token_mint: str) -> float | None:
        """Get the current USD price of a token by mint address.

        Args:
            token_mint: Solana token mint address

        Returns:
            Price in USD, or None if not found.
        """
        try:
            resp = self._client.get(
                f"{self.price_endpoint}/price",
                params={"ids": token_mint},
            )
            resp.raise_for_status()
            data = resp.json()
            token_data = data.get("data", {}).get(token_mint, {})
            price = token_data.get("price")
            return float(price) if price else None
        except Exception:
            return None

    def get_prices(self, token_mints: list[str]) -> dict[str, float]:
        """Get prices for multiple tokens at once."""
        ids = ",".join(token_mints)
        try:
            resp = self._client.get(
                f"{self.price_endpoint}/price",
                params={"ids": ids},
            )
            resp.raise_for_status()
            data = resp.json().get("data", {})
            return {
                mint: float(info.get("price", 0))
                for mint, info in data.items()
                if info.get("price")
            }
        except Exception:
            return {}

    def get_quote(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int = 50,
    ) -> dict[str, Any] | None:
        """Get a swap quote between two tokens.

        Args:
            input_mint: Source token mint address
            output_mint: Target token mint address
            amount: Amount in smallest units (lamports for SOL, decimals for tokens)
            slippage_bps: Slippage tolerance in basis points (50 = 0.5%)

        Returns:
            Quote with routes, price impact, and expected output.
        """
        params = {
            "inputMint": input_mint,
            "outputMint": output_mint,
            "amount": str(amount),
            "slippageBps": slippage_bps,
        }
        try:
            resp = self._client.get(
                f"{self.api_endpoint}/quote",
                params=params,
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return None

    def get_quote_simple(
        self,
        input_mint: str,
        output_mint: str,
        amount_sol: float,
        slippage_bps: int = 50,
    ) -> dict[str, Any] | None:
        """Get a swap quote using SOL amounts (converts to lamports).

        Args:
            input_mint: Source token mint (So11111111111111111111111111111111111111112 for SOL)
            output_mint: Target token mint
            amount_sol: Amount in SOL (will be converted to lamports)
            slippage_bps: Slippage tolerance in basis points

        Returns:
            Quote with expected output and price impact.
        """
        amount_lamports = int(amount_sol * 1_000_000_000)
        return self.get_quote(input_mint, output_mint, amount_lamports, slippage_bps)

    def get_token_list(self) -> list[dict[str, Any]]:
        """Get the list of tokens supported by Jupiter."""
        try:
            resp = self._client.get(
                "https://token.jup.ag/strict",
            )
            resp.raise_for_status()
            return resp.json()
        except Exception:
            return []

    def search_token(self, query: str) -> list[dict[str, Any]]:
        """Search for a token by symbol or name.

        Args:
            query: Token symbol (e.g., 'SOL', 'USDC', 'BONK')

        Returns:
            List of matching tokens with mint, symbol, name, decimals.
        """
        tokens = self.get_token_list()
        query = query.lower()
        results = []
        for token in tokens:
            symbol = token.get("symbol", "").lower()
            name = token.get("name", "").lower()
            if query in symbol or query in name:
                results.append({
                    "mint": token.get("address", ""),
                    "symbol": token.get("symbol", ""),
                    "name": token.get("name", ""),
                    "decimals": token.get("decimals", 0),
                    "logo": token.get("logoURI", ""),
                })
        return results[:10]

    def close(self):
        self._client.close()

    def __enter__(self):
        return self

    def __exit__(self, *args):
        self.close()
