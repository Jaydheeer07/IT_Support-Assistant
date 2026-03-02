import json
import httpx
import config

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"

class AzureADClient:
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None):
        self._tenant_id = tenant_id or config.AZURE_TENANT_ID
        self._client_id = client_id or config.AZURE_CLIENT_ID
        self._client_secret = client_secret or config.AZURE_CLIENT_SECRET
        self._token_url = (
            f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"
        )

    async def _get_access_token(self) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.post(self._token_url, data={
                "grant_type": "client_credentials",
                "client_id": self._client_id,
                "client_secret": self._client_secret,
                "scope": "https://graph.microsoft.com/.default",
            })
            resp.raise_for_status()
            return resp.json()["access_token"]

    async def get_user(self, user_id: str) -> str:
        token = await self._get_access_token()
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                f"{GRAPH_API_BASE}/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"$select": "displayName,mail,department,jobTitle,id"},
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
