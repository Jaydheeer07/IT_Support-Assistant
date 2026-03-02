import json
import httpx
import config

class BraveSearchClient:
    _BASE_URL = "https://api.search.brave.com/res/v1/web/search"

    def __init__(self, api_key: str = None):
        self._api_key = api_key or config.BRAVE_SEARCH_API_KEY

    async def search(self, query: str, count: int = 3) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                self._BASE_URL,
                headers={
                    "Accept": "application/json",
                    "Accept-Encoding": "gzip",
                    "X-Subscription-Token": self._api_key,
                },
                params={"q": query, "count": count},
            )
            resp.raise_for_status()
            data = resp.json()
            results = [
                {
                    "title": r.get("title", ""),
                    "url": r.get("url", ""),
                    "description": r.get("description", ""),
                }
                for r in data.get("web", {}).get("results", [])
            ]
            return json.dumps({"results": results, "query": query})
