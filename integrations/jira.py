import json
import httpx
import config

class JiraClient:
    def __init__(self, base_url: str = None, email: str = None,
                 api_token: str = None, project_key: str = None):
        self._base_url = (base_url or config.JIRA_BASE_URL).rstrip("/")
        self._email = email or config.JIRA_EMAIL
        self._api_token = api_token or config.JIRA_API_TOKEN
        self._project_key = project_key or config.JIRA_PROJECT_KEY
        self._auth = (self._email, self._api_token)

    async def create_ticket(self, summary: str, description: str,
                             priority: str, reporter_info: dict | str) -> str:
        if isinstance(reporter_info, str):
            try:
                reporter_info = json.loads(reporter_info)
            except (json.JSONDecodeError, ValueError):
                reporter_info = {}

        name = reporter_info.get("displayName", "Unknown")
        email = reporter_info.get("mail", "Unknown")
        dept = reporter_info.get("department", "Unknown")

        full_description = (
            f"Reported by: {name} ({email}) — {dept}\n\n"
            f"{description}"
        )

        payload = {
            "fields": {
                "project": {"key": self._project_key},
                "summary": summary,
                "description": {
                    "version": 1,
                    "type": "doc",
                    "content": [{"type": "paragraph", "content": [
                        {"type": "text", "text": full_description}
                    ]}],
                },
                "issuetype": {"name": "Service Request"},
                "priority": {"name": priority},
            }
        }

        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/rest/api/3/issue",
                auth=self._auth,
                json=payload,
                headers={"Accept": "application/json"},
            )
            resp.raise_for_status()
            data = resp.json()
            ticket_id = data["key"]
            return json.dumps({
                "ticket_id": ticket_id,
                "url": f"{self._base_url}/browse/{ticket_id}",
                "message": f"Ticket {ticket_id} created successfully.",
            })
