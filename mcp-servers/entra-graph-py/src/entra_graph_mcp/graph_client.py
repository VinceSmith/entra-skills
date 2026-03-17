"""Microsoft Graph client factory.

Creates an authenticated GraphServiceClient using DefaultAzureCredential.
"""

from __future__ import annotations

from azure.identity import DefaultAzureCredential
from msgraph import GraphServiceClient

_credential: DefaultAzureCredential | None = None
_client: GraphServiceClient | None = None


def get_credential() -> DefaultAzureCredential:
    """Return a reusable DefaultAzureCredential instance."""
    global _credential
    if _credential is None:
        _credential = DefaultAzureCredential()
    return _credential


def get_graph_client() -> GraphServiceClient:
    """Return a reusable GraphServiceClient instance."""
    global _client
    if _client is None:
        _client = GraphServiceClient(get_credential())
    return _client
