from pathlib import Path
import uvicorn
from aiohttp import web
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles

from knowledge_base.store import KnowledgeBase
from agent.memory import SessionMemory
from agent.tools import ToolRegistry
from agent.loop import AtlasAgent
from integrations.teams import AtlasTeamsBot
from integrations.jira import JiraClient
from integrations.azure_ad import AzureADClient
from integrations.brave import BraveSearchClient
from admin.routes import router as admin_router
import config

BASE_DIR = Path(__file__).resolve().parent

app = FastAPI(title="A.T.L.A.S.", version="1.0.0")
app.mount(
    "/admin/static",
    StaticFiles(directory=str(BASE_DIR / "admin" / "static")),
    name="static",
)
app.include_router(admin_router)

# --- Component wiring ---
kb = KnowledgeBase()
memory = SessionMemory()
jira = JiraClient()
azure_ad = AzureADClient()
brave = BraveSearchClient()
tools = ToolRegistry(kb=kb, jira=jira, azure_ad=azure_ad, brave=brave)
agent = AtlasAgent(tools=tools, memory=memory)

# --- Bot Framework adapter ---
adapter_settings = BotFrameworkAdapterSettings(
    app_id=config.MICROSOFT_APP_ID,
    app_password=config.MICROSOFT_APP_PASSWORD,
)
adapter = BotFrameworkAdapter(adapter_settings)
bot = AtlasTeamsBot(agent=agent, memory=memory)


@app.post("/api/messages")
async def messages(request: Request):
    try:
        body = await request.json()
        activity = Activity().deserialize(body)
        auth_header = request.headers.get("Authorization", "")
        invoke_response = await adapter.process_activity(activity, auth_header, bot.on_turn)
        if invoke_response:
            return Response(
                content=str(invoke_response.body),
                status_code=invoke_response.status,
                media_type="application/json",
            )
        return Response(status_code=200)
    except Exception as exc:
        return Response(
            content=f'{{"error": "{type(exc).__name__}"}}',
            status_code=500,
            media_type="application/json",
        )


@app.get("/health")
async def health():
    return {"status": "ok", "name": "A.T.L.A.S."}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=config.PORT,
        log_level=config.LOG_LEVEL,
        reload=config.RELOAD,
    )
