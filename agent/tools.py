import json
from knowledge_base.store import KnowledgeBase
import config

TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "search_knowledge_base",
            "description": "Search the internal IT knowledge base for guides and solutions. Use this first for any IT support question.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query based on the user's issue and triage answers"},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Search the web (Brave Search) for IT solutions when the knowledge base has no answer. Use as fallback only.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Search query. Prefer queries targeting Microsoft support docs."},
                },
                "required": ["query"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "get_user_info",
            "description": "Get the user's profile from Azure AD: name, email, department, job title. Use to personalize responses and pre-fill tickets.",
            "parameters": {
                "type": "object",
                "properties": {
                    "user_id": {"type": "string", "description": "The Teams/Azure AD user ID"},
                },
                "required": ["user_id"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "create_jira_ticket",
            "description": "Create a Jira Service Management ticket when the issue cannot be resolved. Include all context collected so far.",
            "parameters": {
                "type": "object",
                "properties": {
                    "summary": {"type": "string", "description": "One-line ticket summary"},
                    "description": {"type": "string", "description": "Full description including steps attempted and triage info"},
                    "priority": {"type": "string", "enum": ["Low", "Medium", "High", "Critical"], "description": "Issue priority"},
                },
                "required": ["summary", "description", "priority"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "escalate_to_human",
            "description": "Notify an L1 IT agent in Teams that a user needs immediate human assistance.",
            "parameters": {
                "type": "object",
                "properties": {
                    "reason": {"type": "string", "description": "Why human escalation is needed"},
                    "ticket_id": {"type": "string", "description": "The Jira ticket ID if one was created"},
                },
                "required": ["reason"],
            },
        },
    },
]


class ToolRegistry:
    def __init__(self, kb: KnowledgeBase, jira, azure_ad, brave):
        self._kb = kb
        self._jira = jira
        self._azure_ad = azure_ad
        self._brave = brave

    async def dispatch(self, name: str, args: dict, user_id: str, session_id: str) -> str:
        handlers = {
            "search_knowledge_base": self._search_kb,
            "search_web": self._search_web,
            "get_user_info": self._get_user_info,
            "create_jira_ticket": self._create_jira_ticket,
            "escalate_to_human": self._escalate_to_human,
        }
        handler = handlers.get(name)
        if handler is None:
            return f"error: unknown tool '{name}'"
        return await handler(args, user_id=user_id, session_id=session_id)

    async def _search_kb(self, args: dict, **kwargs) -> str:
        results = self._kb.search(args["query"], top_k=3,
                                   min_confidence=config.KB_CONFIDENCE_THRESHOLD)
        if not results:
            return json.dumps({"found": False, "message": "No relevant guides found in knowledge base."})
        return json.dumps({"found": True, "results": results})

    async def _search_web(self, args: dict, **kwargs) -> str:
        return await self._brave.search(args["query"])

    async def _get_user_info(self, args: dict, **kwargs) -> str:
        return await self._azure_ad.get_user(args["user_id"])

    async def _create_jira_ticket(self, args: dict, user_id: str, **kwargs) -> str:
        user_info = await self._azure_ad.get_user(user_id)
        return await self._jira.create_ticket(
            summary=args["summary"],
            description=args["description"],
            priority=args["priority"],
            reporter_info=user_info,
        )

    async def _escalate_to_human(self, args: dict, **kwargs) -> str:
        return json.dumps({
            "escalated": True,
            "message": f"L1 agent notified. Reason: {args['reason']}",
            "ticket_id": args.get("ticket_id", "N/A"),
        })
