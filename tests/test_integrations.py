import pytest
import json
from unittest.mock import AsyncMock, MagicMock, patch
from integrations.jira import JiraClient
from integrations.azure_ad import AzureADClient
from integrations.brave import BraveSearchClient

@pytest.mark.asyncio
async def test_jira_create_ticket_returns_ticket_id():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_resp = MagicMock()
        mock_resp.status_code = 201
        mock_resp.json.return_value = {"key": "IT-123", "id": "10001"}
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        client = JiraClient(base_url="https://test.atlassian.net",
                             email="test@co.com", api_token="tok",
                             project_key="IT")
        result = await client.create_ticket(
            summary="Test issue", description="Details", priority="Medium",
            reporter_info=json.dumps({"displayName": "Alice", "mail": "alice@co.com", "department": "IT"})
        )
        data = json.loads(result)
        assert data["ticket_id"] == "IT-123"
        assert "url" in data

@pytest.mark.asyncio
async def test_azure_ad_get_user_returns_profile():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "displayName": "Alice Smith",
            "mail": "alice@co.com",
            "department": "Finance",
            "jobTitle": "Analyst",
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        with patch("integrations.azure_ad.AzureADClient._get_access_token",
                   new=AsyncMock(return_value="fake-token")):
            client = AzureADClient(tenant_id="t", client_id="c", client_secret="s")
            result = await client.get_user("user-id-123")
            data = json.loads(result)
            assert data["displayName"] == "Alice Smith"
            assert data["mail"] == "alice@co.com"

@pytest.mark.asyncio
async def test_brave_search_returns_results():
    with patch("httpx.AsyncClient") as mock_client_cls:
        mock_resp = MagicMock()
        mock_resp.status_code = 200
        mock_resp.json.return_value = {
            "web": {"results": [
                {"title": "Clear cookies Chrome", "url": "https://support.google.com/x",
                 "description": "How to clear cookies in Chrome browser"}
            ]}
        }
        mock_resp.raise_for_status = MagicMock()
        mock_client = MagicMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.get = AsyncMock(return_value=mock_resp)
        mock_client_cls.return_value = mock_client

        client = BraveSearchClient(api_key="test-key")
        result = await client.search("clear cookies chrome")
        data = json.loads(result)
        assert data["results"][0]["title"] == "Clear cookies Chrome"
        assert "url" in data["results"][0]
