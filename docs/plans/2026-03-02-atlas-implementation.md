# A.T.L.A.S. Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Build A.T.L.A.S. (Automated Troubleshooting & Level-1 Assistance System), a Microsoft Teams IT support bot that answers IT questions via a knowledge base, searches the web as fallback, auto-creates Jira tickets for unresolved issues, and learns over time via a human-approved heuristics system.

**Architecture:** FastAPI backend receives Teams messages via Microsoft Bot Framework webhook. A custom NanoClaw-inspired ReAct agent loop (plain Python, no LangChain) handles triage → KB search → web fallback → resolution → ticket creation. Identity context is pulled from Azure AD. Sessions persist in Redis; feedback and logs are stored in SQLite. A soul.md + memory.md pair gives A.T.L.A.S. a persistent identity that improves via human-approved proposals.

**Tech Stack:** Python 3.12, FastAPI, botbuilder-integration-aiohttp, LiteLLM (OpenRouter), ChromaDB, Redis, SQLite, httpx, Docker Compose, Nginx

---

## Prerequisites

Before starting, ensure you have:
- Python 3.12 installed (`python --version`)
- Docker Desktop installed and running (`docker --version`)
- Git initialized in the project root (`git init`)
- A `.env` file copied from `.env.example` with real values filled in (added as you go)

---

## Task 1: Project Scaffolding

**Files:**
- Create: `main.py`
- Create: `config.py`
- Create: `requirements.txt`
- Create: `requirements-dev.txt`
- Create: `.env.example`
- Create: `agent/__init__.py`
- Create: `agent/soul.md`
- Create: `agent/memory.md`
- Create: `integrations/__init__.py`
- Create: `knowledge_base/__init__.py`
- Create: `learning/__init__.py`
- Create: `admin/__init__.py`
- Create: `tests/__init__.py`

### Step 1: Create directory structure

```bash
mkdir -p agent integrations knowledge_base/guides learning admin/static tests
touch agent/__init__.py integrations/__init__.py knowledge_base/__init__.py learning/__init__.py admin/__init__.py tests/__init__.py
```

### Step 2: Create `requirements.txt`

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
botbuilder-integration-aiohttp==4.16.1
litellm==1.57.3
chromadb==0.6.3
httpx==0.28.1
python-dotenv==1.0.1
redis==5.2.1
```

### Step 3: Create `requirements-dev.txt`

```
pytest==8.3.4
pytest-asyncio==0.25.2
pytest-mock==3.14.0
httpx==0.28.1
```

### Step 4: Create `.env.example`

```
# Bot Framework
MICROSOFT_APP_ID=
MICROSOFT_APP_PASSWORD=

# OpenRouter
OPENROUTER_API_KEY=

# Jira
JIRA_BASE_URL=https://yourcompany.atlassian.net
JIRA_EMAIL=
JIRA_API_TOKEN=
JIRA_PROJECT_KEY=IT

# Azure AD / Microsoft Graph
AZURE_TENANT_ID=
AZURE_CLIENT_ID=
AZURE_CLIENT_SECRET=

# Brave Search
BRAVE_SEARCH_API_KEY=

# Redis
REDIS_URL=redis://redis:6379

# Admin Dashboard
ADMIN_USERNAME=admin
ADMIN_PASSWORD=changeme

# App
PORT=8000
LOG_LEVEL=info
ESCALATION_ATTEMPT_THRESHOLD=2
KB_CONFIDENCE_THRESHOLD=0.70
```

### Step 5: Create `config.py`

```python
import os
from dotenv import load_dotenv

load_dotenv()

MICROSOFT_APP_ID = os.getenv("MICROSOFT_APP_ID", "")
MICROSOFT_APP_PASSWORD = os.getenv("MICROSOFT_APP_PASSWORD", "")

OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY", "")

JIRA_BASE_URL = os.getenv("JIRA_BASE_URL", "")
JIRA_EMAIL = os.getenv("JIRA_EMAIL", "")
JIRA_API_TOKEN = os.getenv("JIRA_API_TOKEN", "")
JIRA_PROJECT_KEY = os.getenv("JIRA_PROJECT_KEY", "IT")

AZURE_TENANT_ID = os.getenv("AZURE_TENANT_ID", "")
AZURE_CLIENT_ID = os.getenv("AZURE_CLIENT_ID", "")
AZURE_CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")

BRAVE_SEARCH_API_KEY = os.getenv("BRAVE_SEARCH_API_KEY", "")

REDIS_URL = os.getenv("REDIS_URL", "redis://localhost:6379")

ADMIN_USERNAME = os.getenv("ADMIN_USERNAME", "admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "changeme")

PORT = int(os.getenv("PORT", "8000"))
LOG_LEVEL = os.getenv("LOG_LEVEL", "info")
ESCALATION_ATTEMPT_THRESHOLD = int(os.getenv("ESCALATION_ATTEMPT_THRESHOLD", "2"))
KB_CONFIDENCE_THRESHOLD = float(os.getenv("KB_CONFIDENCE_THRESHOLD", "0.70"))
```

### Step 6: Create `main.py` (minimal skeleton)

```python
import uvicorn
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
import config

app = FastAPI(title="A.T.L.A.S.", version="1.0.0")
app.mount("/admin/static", StaticFiles(directory="admin/static"), name="static")

@app.get("/health")
async def health():
    return {"status": "ok", "name": "A.T.L.A.S."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT,
                log_level=config.LOG_LEVEL, reload=True)
```

### Step 7: Write test for health endpoint

Create `tests/test_main.py`:

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_health_returns_ok():
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"
    assert response.json()["name"] == "A.T.L.A.S."
```

### Step 8: Install dependencies and run test

```bash
pip install -r requirements.txt -r requirements-dev.txt
pytest tests/test_main.py -v
```

Expected: PASS

### Step 9: Create `agent/soul.md`

```markdown
# A.T.L.A.S. — Core Identity

**Full Name:** A.T.L.A.S. — Automated Troubleshooting & Level-1 Assistance System
**Tagline:** The heavy lifter that never drops the ball.

## Who A.T.L.A.S. Is
A.T.L.A.S. is the IT team's tireless first responder — handling the repetitive,
the routine, and the urgent at any hour. Not a generic chatbot, but a specialist
that knows your environment, your users, and your tools.

## Personality
- Supportive and patient: never makes a user feel embarrassed for asking
- Sturdy and reliable: consistent tone regardless of the issue
- Direct but warm: gets to solutions quickly without being robotic
- Transparent: always tells users what it's doing and why

## Core Heuristic
"No user left behind."
A.T.L.A.S. never gives up on a user. If it can't solve the issue, it ensures
a human will. Every conversation ends with either a resolution or a Jira ticket
— never silence.

## Communication Rules
- Use numbered steps for any procedure with more than one action
- Keep messages concise (under 200 words unless a guide requires more)
- Always confirm the user's situation before giving a guide
- End resolved sessions with: "Glad I could help! Was this solution useful? 👍 👎"
- When escalating: explain why, set expectations (SLA), give the ticket ID

## What A.T.L.A.S. Does NOT Do
- Speculate on security incidents (escalate immediately)
- Make promises about when human agents will respond
- Access user data beyond what's needed to solve the issue
- Pretend to know something it doesn't — says "Let me find that" instead
```

### Step 10: Create `agent/memory.md` (empty initially)

```markdown
# A.T.L.A.S. — Operational Memory

This file accumulates heuristics learned from real interactions.
Each entry is approved by an admin before being added.
All changes are tracked in git for full auditability.

---

<!-- Entries will be added here as A.T.L.A.S. learns -->
```

### Step 11: Commit scaffolding

```bash
git add .
git commit -m "feat: project scaffolding — FastAPI skeleton, config, soul.md, requirements"
```

---

## Task 2: Knowledge Base (ChromaDB + Markdown Guides)

**Files:**
- Create: `knowledge_base/store.py`
- Create: `knowledge_base/loader.py`
- Create: `knowledge_base/guides/clear-browser-cookies.md`
- Create: `knowledge_base/guides/chrome-profile-setup.md`
- Create: `knowledge_base/guides/shared-mailbox-access.md`
- Create: `knowledge_base/guides/email-setup-new-device.md`
- Create: `knowledge_base/guides/password-reset.md`
- Test: `tests/test_knowledge_base.py`

### Step 1: Write the failing test

Create `tests/test_knowledge_base.py`:

```python
import pytest
from unittest.mock import patch, MagicMock
from knowledge_base.store import KnowledgeBase

def test_search_returns_results_above_threshold():
    kb = KnowledgeBase(persist_dir=":memory:")
    kb.add_document("clear-cookies", "To clear cookies in Chrome: Settings > Privacy > Clear browsing data > Cookies")
    results = kb.search("how to clear cookies chrome", top_k=3)
    assert len(results) > 0
    assert results[0]["confidence"] > 0.0
    assert "content" in results[0]
    assert "source" in results[0]

def test_search_returns_empty_for_unrelated_query():
    kb = KnowledgeBase(persist_dir=":memory:")
    kb.add_document("clear-cookies", "To clear cookies in Chrome: Settings > Privacy > Clear browsing data")
    results = kb.search("quantum physics equations", top_k=3, min_confidence=0.95)
    assert len(results) == 0
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_knowledge_base.py -v
```

Expected: FAIL — `ModuleNotFoundError: No module named 'knowledge_base.store'`

### Step 3: Implement `knowledge_base/store.py`

```python
import chromadb
from chromadb.config import Settings
from typing import Optional

class KnowledgeBase:
    def __init__(self, persist_dir: str = "./knowledge_base/chroma_db"):
        if persist_dir == ":memory:":
            self._client = chromadb.Client()
        else:
            self._client = chromadb.PersistentClient(path=persist_dir)
        self._collection = self._client.get_or_create_collection(
            name="it_guides",
            metadata={"hnsw:space": "cosine"},
        )

    def add_document(self, doc_id: str, content: str, metadata: Optional[dict] = None) -> None:
        self._collection.upsert(
            ids=[doc_id],
            documents=[content],
            metadatas=[metadata or {"source": doc_id}],
        )

    def search(self, query: str, top_k: int = 3, min_confidence: float = 0.0) -> list[dict]:
        results = self._collection.query(
            query_texts=[query],
            n_results=min(top_k, max(1, self._collection.count())),
        )
        if not results["documents"] or not results["documents"][0]:
            return []
        output = []
        for i, doc in enumerate(results["documents"][0]):
            # ChromaDB cosine distance: 0 = identical, 2 = opposite. Convert to confidence.
            distance = results["distances"][0][i]
            confidence = 1.0 - (distance / 2.0)
            if confidence >= min_confidence:
                output.append({
                    "content": doc,
                    "source": results["metadatas"][0][i].get("source", "unknown"),
                    "confidence": round(confidence, 4),
                })
        return sorted(output, key=lambda x: x["confidence"], reverse=True)

    def count(self) -> int:
        return self._collection.count()
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_knowledge_base.py -v
```

Expected: PASS

### Step 5: Implement `knowledge_base/loader.py`

```python
#!/usr/bin/env python3
"""
CLI to load/reload IT guides from Markdown files into ChromaDB.
Usage: python -m knowledge_base.loader
"""
import os
from pathlib import Path
from knowledge_base.store import KnowledgeBase

GUIDES_DIR = Path(__file__).parent / "guides"

def load_all_guides(persist_dir: str = "./knowledge_base/chroma_db") -> int:
    kb = KnowledgeBase(persist_dir=persist_dir)
    count = 0
    for md_file in GUIDES_DIR.glob("*.md"):
        content = md_file.read_text(encoding="utf-8")
        doc_id = md_file.stem
        kb.add_document(doc_id=doc_id, content=content, metadata={"source": md_file.name})
        print(f"  Loaded: {md_file.name}")
        count += 1
    print(f"\nTotal guides loaded: {count}")
    return count

if __name__ == "__main__":
    print("Loading IT guides into ChromaDB...")
    load_all_guides()
    print("Done.")
```

### Step 6: Create the 5 starter IT guides

**`knowledge_base/guides/clear-browser-cookies.md`:**
```markdown
# How to Clear Browser Cookies

## Chrome (Windows/Mac)
1. Open Chrome and click the three-dot menu (top right)
2. Go to Settings > Privacy and security > Clear browsing data
3. Select "Cookies and other site data" and set time range to "All time"
4. Click "Clear data"
5. Restart Chrome

## Edge (Windows)
1. Open Edge, click the three-dot menu > Settings
2. Go to Privacy, search, and services > Clear browsing data > Choose what to clear
3. Check "Cookies and other site data", set time range to "All time"
4. Click "Clear now"

## Firefox
1. Open Firefox > Settings > Privacy & Security
2. Under Cookies and Site Data, click "Clear Data"
3. Check "Cookies and Site Data", click "Clear"

**Common fix for:** Login loops, "you've been logged out" messages, session errors
```

**`knowledge_base/guides/chrome-profile-setup.md`:**
```markdown
# How to Create a Separate Chrome Profile

Use separate profiles to keep work and personal browsing separate,
or to test with a different account.

## Steps
1. Open Chrome
2. Click your profile avatar (top right corner, circular icon)
3. Click "Add" at the bottom of the profile menu
4. Choose "Continue without an account" (or sign in with a Google account)
5. Give the profile a name (e.g., "Work") and choose an avatar color
6. Click "Done" — Chrome opens a new window for this profile

## Switching Between Profiles
- Click the profile avatar in any Chrome window
- All profiles are listed — click to switch
- Each profile has its own cookies, history, and extensions

## Deleting a Profile
1. Click avatar > gear icon next to the profile
2. Click "Delete" and confirm

**Common use cases:** Separate work/personal accounts, testing web apps with different logins
```

**`knowledge_base/guides/shared-mailbox-access.md`:**
```markdown
# How to Access a Shared Mailbox

## Outlook Desktop (Windows)
### Method 1: Auto-map (if IT has granted access)
1. Close and reopen Outlook — the shared mailbox appears automatically in the left panel
2. If it doesn't appear after 30 minutes, try Method 2

### Method 2: Add manually
1. In Outlook, go to File > Account Settings > Account Settings
2. Double-click your email account
3. Click "More Settings" > "Advanced" tab
4. Under "Open these additional mailboxes", click "Add"
5. Type the shared mailbox name and click OK
6. Close and reopen Outlook

## Outlook on the Web (OWA)
1. Go to outlook.office365.com and sign in
2. Click your profile icon (top right) > "Open another mailbox"
3. Type the shared mailbox email address and click "Open"

## Common Errors
- **"You don't have permission"** → IT needs to grant you access first. Create a ticket.
- **Mailbox not appearing after access granted** → Wait up to 60 minutes, or try Method 2
- **Can't send as shared mailbox** → Need "Send As" permission — contact IT

**Note:** You must be granted access by IT before these steps will work.
```

**`knowledge_base/guides/email-setup-new-device.md`:**
```markdown
# Setting Up Your Work Email on a New Device

## Windows — Outlook Desktop
1. Open Outlook (install from Microsoft 365 if not installed)
2. Enter your work email address and click "Connect"
3. Outlook auto-configures via autodiscover — sign in with your Microsoft 365 credentials
4. Complete MFA if prompted
5. Wait for mailbox to sync (can take 5–15 minutes for large mailboxes)

## Mac — Outlook for Mac
1. Open Outlook for Mac
2. Click "Add Account" and enter your work email
3. Sign in with Microsoft 365 credentials
4. Complete MFA
5. Choose which data to sync (Mail, Calendar, Contacts)

## iPhone / iOS
1. Go to Settings > Mail > Accounts > Add Account
2. Choose "Microsoft Exchange"
3. Enter your work email, then tap "Sign In"
4. Authenticate via Microsoft 365 / MFA
5. Choose what to sync and tap "Save"

## Android
1. Open the Outlook app (install from Play Store if needed)
2. Tap "Add Account" > "Add Email Account"
3. Enter your work email and sign in with Microsoft 365 credentials
4. Complete MFA if prompted

## Troubleshooting
- **MFA not working:** Contact IT — your MFA method may need to be reset
- **"Account not found":** Check that you're using your full work email (name@company.com)
- **Sync not working:** Ensure you're connected to Wi-Fi or have mobile data
```

**`knowledge_base/guides/password-reset.md`:**
```markdown
# How to Reset Your Password

## Self-Service Password Reset (SSPR) — Recommended
1. Go to aka.ms/sspr (Microsoft self-service password reset)
2. Enter your work email address
3. Choose your verification method (email, phone, authenticator app)
4. Follow the prompts to verify your identity
5. Set your new password (must meet complexity requirements)
6. Sign in with the new password

## If SSPR Is Not Set Up or Fails
Contact IT Support to reset your password manually.
When contacting IT, have ready:
- Your full name and employee ID
- Your work email address
- Confirmation that you're the account owner (IT will verify via manager)

## Password Requirements (Standard)
- Minimum 12 characters
- Must include: uppercase, lowercase, number, and special character
- Cannot reuse your last 10 passwords
- Cannot contain your name or username

## Locked Account
If your account is locked (too many wrong attempts):
- Wait 15 minutes and try again, OR
- Use SSPR at aka.ms/sspr to unlock immediately, OR
- Contact IT if neither option works

## After Reset
- Update saved passwords in your browser and password manager
- Re-authenticate apps (Outlook, Teams, OneDrive) with the new password
```

### Step 7: Run loader and verify

```bash
python -m knowledge_base.loader
```

Expected output:
```
Loading IT guides into ChromaDB...
  Loaded: clear-browser-cookies.md
  Loaded: chrome-profile-setup.md
  Loaded: shared-mailbox-access.md
  Loaded: email-setup-new-device.md
  Loaded: password-reset.md

Total guides loaded: 5
Done.
```

### Step 8: Commit

```bash
git add .
git commit -m "feat: knowledge base — ChromaDB store, loader CLI, 5 starter IT guides"
```

---

## Task 3: Session Memory (Redis-backed)

**Files:**
- Create: `agent/memory.py`
- Test: `tests/test_agent_memory.py`

### Step 1: Write the failing test

Create `tests/test_agent_memory.py`:

```python
import pytest
from unittest.mock import MagicMock, patch
from agent.memory import SessionMemory

def test_get_returns_empty_list_for_new_session():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mem = SessionMemory(redis_client=mock_redis)
    result = mem.get("session-123")
    assert result == []

def test_save_and_get_messages():
    import json
    mock_redis = MagicMock()
    stored = {}
    mock_redis.set.side_effect = lambda k, v, ex=None: stored.update({k: v})
    mock_redis.get.side_effect = lambda k: stored.get(k)

    mem = SessionMemory(redis_client=mock_redis)
    messages = [{"role": "user", "content": "hello"}]
    mem.save("session-123", messages)
    result = mem.get("session-123")
    assert result == messages

def test_clear_removes_session():
    mock_redis = MagicMock()
    mem = SessionMemory(redis_client=mock_redis)
    mem.clear("session-123")
    mock_redis.delete.assert_called_once_with("atlas:session:session-123")
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_agent_memory.py -v
```

Expected: FAIL

### Step 3: Implement `agent/memory.py`

```python
import json
from typing import Optional
import redis as redis_lib
import config

SESSION_TTL_SECONDS = 3600  # 1 hour

class SessionMemory:
    def __init__(self, redis_client=None):
        if redis_client is not None:
            self._redis = redis_client
        else:
            self._redis = redis_lib.from_url(config.REDIS_URL, decode_responses=True)

    def _key(self, session_id: str) -> str:
        return f"atlas:session:{session_id}"

    def get(self, session_id: str) -> list[dict]:
        raw = self._redis.get(self._key(session_id))
        if raw is None:
            return []
        return json.loads(raw)

    def save(self, session_id: str, messages: list[dict]) -> None:
        self._redis.set(self._key(session_id), json.dumps(messages), ex=SESSION_TTL_SECONDS)

    def append(self, session_id: str, role: str, content: str) -> list[dict]:
        messages = self.get(session_id)
        messages.append({"role": role, "content": content})
        self.save(session_id, messages)
        return messages

    def clear(self, session_id: str) -> None:
        self._redis.delete(self._key(session_id))
```

### Step 4: Run test to verify it passes

```bash
pytest tests/test_agent_memory.py -v
```

Expected: PASS

### Step 5: Commit

```bash
git add agent/memory.py tests/test_agent_memory.py
git commit -m "feat: Redis-backed session memory"
```

---

## Task 4: Tool Registry

**Files:**
- Create: `agent/tools.py`
- Test: `tests/test_tools.py`

### Step 1: Write the failing test

Create `tests/test_tools.py`:

```python
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from agent.tools import ToolRegistry, TOOL_DEFINITIONS

def test_tool_definitions_have_required_fields():
    for tool in TOOL_DEFINITIONS:
        assert "type" in tool
        assert tool["type"] == "function"
        assert "function" in tool
        assert "name" in tool["function"]
        assert "description" in tool["function"]
        assert "parameters" in tool["function"]

def test_tool_registry_lists_expected_tools():
    registry = ToolRegistry.__new__(ToolRegistry)
    names = [t["function"]["name"] for t in TOOL_DEFINITIONS]
    assert "search_knowledge_base" in names
    assert "search_web" in names
    assert "create_jira_ticket" in names
    assert "get_user_info" in names
    assert "escalate_to_human" in names

@pytest.mark.asyncio
async def test_dispatch_unknown_tool_returns_error():
    registry = ToolRegistry(kb=MagicMock(), jira=MagicMock(),
                             azure_ad=MagicMock(), brave=MagicMock())
    result = await registry.dispatch("nonexistent_tool", {}, user_id="u1", session_id="s1")
    assert "error" in result.lower()
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_tools.py -v
```

Expected: FAIL

### Step 3: Implement `agent/tools.py`

```python
import json
from typing import Any
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
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_tools.py -v
```

Expected: PASS

### Step 5: Commit

```bash
git add agent/tools.py tests/test_tools.py
git commit -m "feat: tool registry with 5 tools — KB, web search, user info, Jira, escalation"
```

---

## Task 5: The A.T.L.A.S. Agent Loop

**Files:**
- Create: `agent/loop.py`
- Test: `tests/test_agent_loop.py`

### Step 1: Write the failing test

Create `tests/test_agent_loop.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from agent.loop import AtlasAgent

@pytest.fixture
def mock_tools():
    tools = MagicMock()
    tools.dispatch = AsyncMock(return_value='{"found": true, "results": [{"content": "Clear cookies: Settings > Privacy", "source": "clear-cookies", "confidence": 0.85}]}')
    return tools

@pytest.fixture
def mock_memory():
    mem = MagicMock()
    mem.get.return_value = []
    mem.save = MagicMock()
    return mem

@pytest.mark.asyncio
async def test_agent_returns_string_response(mock_tools, mock_memory):
    with patch("agent.loop.litellm.acompletion") as mock_llm:
        mock_llm.return_value = MagicMock(
            choices=[MagicMock(message=MagicMock(
                content="Here's how to clear your cookies...",
                tool_calls=None,
            ))]
        )
        agent = AtlasAgent(tools=mock_tools, memory=mock_memory)
        response = await agent.respond(
            session_id="s1", user_id="u1",
            user_message="How do I clear cookies?"
        )
        assert isinstance(response, str)
        assert len(response) > 0

@pytest.mark.asyncio
async def test_agent_calls_tool_when_llm_requests_it(mock_tools, mock_memory):
    import json
    with patch("agent.loop.litellm.acompletion") as mock_llm:
        tool_call = MagicMock()
        tool_call.function.name = "search_knowledge_base"
        tool_call.function.arguments = json.dumps({"query": "clear cookies"})
        tool_call.id = "call_123"

        # First call: LLM requests tool use
        mock_llm.side_effect = [
            MagicMock(choices=[MagicMock(message=MagicMock(
                content=None, tool_calls=[tool_call]
            ))]),
            # Second call: LLM gives final answer
            MagicMock(choices=[MagicMock(message=MagicMock(
                content="Here are the steps to clear cookies...",
                tool_calls=None,
            ))]),
        ]
        agent = AtlasAgent(tools=mock_tools, memory=mock_memory)
        response = await agent.respond(
            session_id="s1", user_id="u1",
            user_message="Clear my cookies"
        )
        mock_tools.dispatch.assert_called_once_with(
            "search_knowledge_base", {"query": "clear cookies"},
            user_id="u1", session_id="s1"
        )
        assert isinstance(response, str)
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_agent_loop.py -v
```

Expected: FAIL

### Step 3: Implement `agent/loop.py`

```python
import json
from pathlib import Path
import litellm
from agent.tools import ToolRegistry, TOOL_DEFINITIONS
from agent.memory import SessionMemory
import config

SOUL_PATH = Path(__file__).parent / "soul.md"
MEMORY_PATH = Path(__file__).parent / "memory.md"

# Model routing: use cheaper model by default, upgrade for complex cases
ROUTING_MODEL = "openrouter/google/gemini-flash-1.5"
REASONING_MODEL = "openrouter/anthropic/claude-haiku-4-5-20251001"
MAX_TOOL_ITERATIONS = 6


def _build_system_prompt() -> str:
    soul = SOUL_PATH.read_text(encoding="utf-8") if SOUL_PATH.exists() else ""
    memory = MEMORY_PATH.read_text(encoding="utf-8") if MEMORY_PATH.exists() else ""
    return f"{soul}\n\n## Operational Memory\n{memory}"


class AtlasAgent:
    def __init__(self, tools: ToolRegistry, memory: SessionMemory):
        self._tools = tools
        self._memory = memory
        self._system_prompt = _build_system_prompt()

    async def respond(self, session_id: str, user_id: str, user_message: str) -> str:
        messages = self._memory.get(session_id)

        # Add system prompt only on first message
        if not messages:
            messages = [{"role": "system", "content": self._system_prompt}]

        messages.append({"role": "user", "content": user_message})

        for _ in range(MAX_TOOL_ITERATIONS):
            response = await litellm.acompletion(
                model=REASONING_MODEL,
                messages=messages,
                tools=TOOL_DEFINITIONS,
                api_key=config.OPENROUTER_API_KEY,
                api_base="https://openrouter.ai/api/v1",
            )
            msg = response.choices[0].message

            if not msg.tool_calls:
                # Final answer
                final_text = msg.content or ""
                messages.append({"role": "assistant", "content": final_text})
                self._memory.save(session_id, messages)
                return final_text

            # Process tool calls
            messages.append({"role": "assistant", "content": msg.content,
                              "tool_calls": [tc.model_dump() for tc in msg.tool_calls]})

            for tool_call in msg.tool_calls:
                tool_name = tool_call.function.name
                tool_args = json.loads(tool_call.function.arguments)
                result = await self._tools.dispatch(
                    tool_name, tool_args, user_id=user_id, session_id=session_id
                )
                messages.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": result,
                })

        # Fallback if max iterations hit
        fallback = "I've tried several approaches but couldn't resolve this. Let me create a ticket for you."
        messages.append({"role": "assistant", "content": fallback})
        self._memory.save(session_id, messages)
        return fallback

    def reload_soul(self) -> None:
        """Reload soul.md and memory.md — called after admin approves learning proposals."""
        self._system_prompt = _build_system_prompt()
```

### Step 4: Run tests to verify they pass

```bash
pytest tests/test_agent_loop.py -v
```

Expected: PASS

### Step 5: Commit

```bash
git add agent/loop.py tests/test_agent_loop.py
git commit -m "feat: A.T.L.A.S. ReAct agent loop — tool use, memory, soul.md system prompt"
```

---

## Task 6: Integrations — Jira, Azure AD, Brave Search

**Files:**
- Create: `integrations/jira.py`
- Create: `integrations/azure_ad.py`
- Create: `integrations/brave.py`
- Test: `tests/test_integrations.py`

### Step 1: Write the failing tests

Create `tests/test_integrations.py`:

```python
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
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.post.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        client = JiraClient(base_url="https://test.atlassian.net",
                             email="test@co.com", api_token="tok",
                             project_key="IT")
        result = await client.create_ticket(
            summary="Test issue", description="Details", priority="Medium",
            reporter_info={"displayName": "Alice", "mail": "alice@co.com", "department": "IT"}
        )
        data = json.loads(result)
        assert data["ticket_id"] == "IT-123"

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
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        # Mock token acquisition
        with patch("integrations.azure_ad.AzureADClient._get_access_token",
                   new=AsyncMock(return_value="fake-token")):
            client = AzureADClient(tenant_id="t", client_id="c", client_secret="s")
            result = await client.get_user("user-id-123")
            data = json.loads(result)
            assert data["displayName"] == "Alice Smith"

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
        mock_client = AsyncMock()
        mock_client.__aenter__.return_value.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        client = BraveSearchClient(api_key="test-key")
        result = await client.search("clear cookies chrome")
        data = json.loads(result)
        assert data["results"][0]["title"] == "Clear cookies Chrome"
```

### Step 2: Run tests to verify they fail

```bash
pytest tests/test_integrations.py -v
```

Expected: FAIL

### Step 3: Implement `integrations/jira.py`

```python
import json
import httpx
import config

class JiraClient:
    def __init__(self, base_url: str = None, email: str = None,
                 api_token: str = None, project_key: str = None):
        self._base_url = base_url or config.JIRA_BASE_URL
        self._email = email or config.JIRA_EMAIL
        self._api_token = api_token or config.JIRA_API_TOKEN
        self._project_key = project_key or config.JIRA_PROJECT_KEY
        self._auth = (self._email, self._api_token)

    async def create_ticket(self, summary: str, description: str,
                             priority: str, reporter_info: dict | str) -> str:
        if isinstance(reporter_info, str):
            reporter_info = json.loads(reporter_info)

        name = reporter_info.get("displayName", "Unknown")
        email = reporter_info.get("mail", "Unknown")
        dept = reporter_info.get("department", "Unknown")

        full_description = (
            f"**Reported by:** {name} ({email}) — {dept}\n\n"
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
```

### Step 4: Implement `integrations/azure_ad.py`

```python
import json
import httpx
import config

class AzureADClient:
    def __init__(self, tenant_id: str = None, client_id: str = None,
                 client_secret: str = None):
        self._tenant_id = tenant_id or config.AZURE_TENANT_ID
        self._client_id = client_id or config.AZURE_CLIENT_ID
        self._client_secret = client_secret or config.AZURE_CLIENT_SECRET
        self._token_url = f"https://login.microsoftonline.com/{self._tenant_id}/oauth2/v2.0/token"

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
                f"https://graph.microsoft.com/v1.0/users/{user_id}",
                headers={"Authorization": f"Bearer {token}"},
                params={"$select": "displayName,mail,department,jobTitle,id"},
            )
            resp.raise_for_status()
            return json.dumps(resp.json())
```

### Step 5: Implement `integrations/brave.py`

```python
import json
import httpx
import config

class BraveSearchClient:
    def __init__(self, api_key: str = None):
        self._api_key = api_key or config.BRAVE_SEARCH_API_KEY

    async def search(self, query: str, count: int = 3) -> str:
        async with httpx.AsyncClient() as client:
            resp = await client.get(
                "https://api.search.brave.com/res/v1/web/search",
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
                {"title": r["title"], "url": r["url"], "description": r.get("description", "")}
                for r in data.get("web", {}).get("results", [])
            ]
            return json.dumps({"results": results, "query": query})
```

### Step 6: Run tests to verify they pass

```bash
pytest tests/test_integrations.py -v
```

Expected: PASS

### Step 7: Commit

```bash
git add integrations/ tests/test_integrations.py
git commit -m "feat: Jira, Azure AD Graph, and Brave Search integrations"
```

---

## Task 7: Teams Bot Framework Webhook

**Files:**
- Create: `integrations/teams.py`
- Modify: `main.py` (add /api/messages route)
- Test: `tests/test_teams.py`

### Step 1: Write the failing test

Create `tests/test_teams.py`:

```python
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

def test_messages_endpoint_exists():
    from main import app
    client = TestClient(app)
    # Without valid Bot Framework auth, expect 401 or 200 (not 404)
    response = client.post("/api/messages", json={})
    assert response.status_code != 404
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_teams.py -v
```

Expected: FAIL (404)

### Step 3: Implement `integrations/teams.py`

```python
from botbuilder.core import ActivityHandler, TurnContext
from botbuilder.schema import Activity

class AtlasTeamsBot(ActivityHandler):
    def __init__(self, agent, memory):
        self._agent = agent
        self._memory = memory

    async def on_message_activity(self, turn_context: TurnContext):
        user_id = turn_context.activity.from_property.id
        session_id = turn_context.activity.conversation.id
        user_message = turn_context.activity.text or ""

        if not user_message.strip():
            return

        # Show typing indicator
        await turn_context.send_activity(Activity(type="typing"))

        response_text = await self._agent.respond(
            session_id=session_id,
            user_id=user_id,
            user_message=user_message,
        )

        await turn_context.send_activity(response_text)

    async def on_members_added_activity(self, members_added, turn_context: TurnContext):
        for member in members_added:
            if member.id != turn_context.activity.recipient.id:
                await turn_context.send_activity(
                    "👋 Hi! I'm **A.T.L.A.S.** — your IT support assistant.\n\n"
                    "I can help with common IT issues like:\n"
                    "- Clearing browser cookies\n"
                    "- Setting up email on a new device\n"
                    "- Accessing shared mailboxes\n"
                    "- Password resets\n\n"
                    "Just describe your issue and I'll guide you through it!"
                )
```

### Step 4: Update `main.py` to wire up the bot

```python
import uvicorn
from fastapi import FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from botbuilder.core import BotFrameworkAdapterSettings, BotFrameworkAdapter
from botbuilder.schema import Activity
from knowledge_base.store import KnowledgeBase
from agent.memory import SessionMemory
from agent.tools import ToolRegistry
from agent.loop import AtlasAgent
from integrations.teams import AtlasTeamsBot
from integrations.jira import JiraClient
from integrations.azure_ad import AzureADClient
from integrations.brave import BraveSearchClient
import config

app = FastAPI(title="A.T.L.A.S.", version="1.0.0")
app.mount("/admin/static", StaticFiles(directory="admin/static"), name="static")

# Initialize components
kb = KnowledgeBase()
memory = SessionMemory()
jira = JiraClient()
azure_ad = AzureADClient()
brave = BraveSearchClient()
tools = ToolRegistry(kb=kb, jira=jira, azure_ad=azure_ad, brave=brave)
agent = AtlasAgent(tools=tools, memory=memory)

# Bot Framework adapter
adapter_settings = BotFrameworkAdapterSettings(
    app_id=config.MICROSOFT_APP_ID,
    app_password=config.MICROSOFT_APP_PASSWORD,
)
adapter = BotFrameworkAdapter(adapter_settings)
bot = AtlasTeamsBot(agent=agent, memory=memory)

@app.post("/api/messages")
async def messages(request: Request):
    body = await request.json()
    activity = Activity().deserialize(body)
    auth_header = request.headers.get("Authorization", "")
    response = Response()
    await adapter.process_activity(activity, auth_header, bot.on_turn)
    return response

@app.get("/health")
async def health():
    return {"status": "ok", "name": "A.T.L.A.S."}

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=config.PORT,
                log_level=config.LOG_LEVEL, reload=True)
```

### Step 5: Run all tests

```bash
pytest tests/ -v
```

Expected: All PASS

### Step 6: Commit

```bash
git add integrations/teams.py main.py tests/test_teams.py
git commit -m "feat: Teams Bot Framework webhook and bot handler"
```

---

## Task 8: Learning System (Feedback + memory.md Proposals)

**Files:**
- Create: `learning/feedback_store.py`
- Create: `learning/processor.py`
- Test: `tests/test_learning.py`

### Step 1: Write the failing test

Create `tests/test_learning.py`:

```python
import pytest
import sqlite3
import tempfile
import os
from learning.feedback_store import FeedbackStore

def test_record_feedback_stores_entry():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = FeedbackStore(db_path=db_path)
        store.record(session_id="s1", user_id="u1", rating=1,
                     issue_summary="Couldn't clear cookies", resolved=True)
        entries = store.get_all()
        assert len(entries) == 1
        assert entries[0]["session_id"] == "s1"
        assert entries[0]["rating"] == 1
        assert entries[0]["resolved"] == 1
    finally:
        os.unlink(db_path)

def test_get_negative_feedback_filters_correctly():
    with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
        db_path = f.name
    try:
        store = FeedbackStore(db_path=db_path)
        store.record("s1", "u1", rating=1, issue_summary="OK", resolved=True)
        store.record("s2", "u2", rating=-1, issue_summary="Bad", resolved=False)
        negatives = store.get_negative_feedback()
        assert len(negatives) == 1
        assert negatives[0]["session_id"] == "s2"
    finally:
        os.unlink(db_path)
```

### Step 2: Run test to verify it fails

```bash
pytest tests/test_learning.py -v
```

Expected: FAIL

### Step 3: Implement `learning/feedback_store.py`

```python
import sqlite3
from datetime import datetime

CREATE_TABLE = """
CREATE TABLE IF NOT EXISTS feedback (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    session_id TEXT NOT NULL,
    user_id TEXT NOT NULL,
    rating INTEGER NOT NULL,        -- 1 = thumbs up, -1 = thumbs down
    issue_summary TEXT,
    resolved INTEGER DEFAULT 0,     -- 1 = resolved, 0 = not resolved
    created_at TEXT DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS learning_proposals (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    proposed_heuristic TEXT NOT NULL,
    source_session_ids TEXT,        -- JSON list of sessions that triggered this
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    created_at TEXT DEFAULT (datetime('now')),
    reviewed_at TEXT
);
"""

class FeedbackStore:
    def __init__(self, db_path: str = "./learning/feedback.db"):
        self._db_path = db_path
        self._init_db()

    def _conn(self):
        conn = sqlite3.connect(self._db_path)
        conn.row_factory = sqlite3.Row
        return conn

    def _init_db(self):
        with self._conn() as conn:
            conn.executescript(CREATE_TABLE)

    def record(self, session_id: str, user_id: str, rating: int,
               issue_summary: str = "", resolved: bool = False) -> None:
        with self._conn() as conn:
            conn.execute(
                "INSERT INTO feedback (session_id, user_id, rating, issue_summary, resolved) VALUES (?, ?, ?, ?, ?)",
                (session_id, user_id, rating, issue_summary, int(resolved)),
            )

    def get_all(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute("SELECT * FROM feedback ORDER BY created_at DESC").fetchall()
            return [dict(r) for r in rows]

    def get_negative_feedback(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM feedback WHERE rating = -1 ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def add_proposal(self, heuristic: str, session_ids: list[str]) -> int:
        import json
        with self._conn() as conn:
            cur = conn.execute(
                "INSERT INTO learning_proposals (proposed_heuristic, source_session_ids) VALUES (?, ?)",
                (heuristic, json.dumps(session_ids)),
            )
            return cur.lastrowid

    def get_pending_proposals(self) -> list[dict]:
        with self._conn() as conn:
            rows = conn.execute(
                "SELECT * FROM learning_proposals WHERE status = 'pending' ORDER BY created_at DESC"
            ).fetchall()
            return [dict(r) for r in rows]

    def update_proposal_status(self, proposal_id: int, status: str) -> None:
        with self._conn() as conn:
            conn.execute(
                "UPDATE learning_proposals SET status = ?, reviewed_at = datetime('now') WHERE id = ?",
                (status, proposal_id),
            )
```

### Step 4: Implement `learning/processor.py`

```python
"""
Nightly learning processor.
Analyzes negative feedback and proposes memory.md additions.
Run via cron: 0 2 * * * cd /app && python -m learning.processor
"""
import json
from pathlib import Path
from learning.feedback_store import FeedbackStore

MEMORY_PATH = Path("agent/memory.md")

def run(feedback_db: str = "./learning/feedback.db",
        min_negative_threshold: int = 3) -> int:
    """Analyze feedback and create proposals. Returns number of proposals created."""
    store = FeedbackStore(db_path=feedback_db)
    negatives = store.get_negative_feedback()

    if len(negatives) < min_negative_threshold:
        print(f"Only {len(negatives)} negative feedback entries. Threshold is {min_negative_threshold}. Skipping.")
        return 0

    # Group by issue summary similarity (simple keyword grouping for v1)
    from collections import defaultdict
    groups = defaultdict(list)
    for entry in negatives:
        # Use first 3 words as group key (simple clustering for v1)
        key = " ".join((entry["issue_summary"] or "unknown").lower().split()[:3])
        groups[key].append(entry)

    proposals_created = 0
    for group_key, entries in groups.items():
        if len(entries) < 2:
            continue
        session_ids = [e["session_id"] for e in entries]
        heuristic = (
            f"Pattern detected: Multiple users reported unresolved issues related to '{group_key}'. "
            f"Consider adding or updating the knowledge base guide for this topic. "
            f"({len(entries)} negative feedback entries)"
        )
        store.add_proposal(heuristic=heuristic, session_ids=session_ids)
        print(f"  Proposal created for pattern: '{group_key}' ({len(entries)} entries)")
        proposals_created += 1

    return proposals_created

if __name__ == "__main__":
    print("Running A.T.L.A.S. learning processor...")
    count = run()
    print(f"Done. {count} proposal(s) created.")
```

### Step 5: Run tests to verify they pass

```bash
pytest tests/test_learning.py -v
```

Expected: PASS

### Step 6: Commit

```bash
git add learning/ tests/test_learning.py
git commit -m "feat: feedback store (SQLite) and nightly learning processor"
```

---

## Task 9: Admin Dashboard

**Files:**
- Create: `admin/routes.py`
- Create: `admin/static/index.html`
- Create: `admin/static/guides.html`
- Create: `admin/static/logs.html`
- Create: `admin/static/learning.html`
- Modify: `main.py` (add admin routes)

### Step 1: Implement `admin/routes.py`

```python
import secrets
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi.responses import HTMLResponse, JSONResponse
from learning.feedback_store import FeedbackStore
from knowledge_base.loader import load_all_guides
import config

router = APIRouter(prefix="/admin")
security = HTTPBasic()


def require_auth(credentials: HTTPBasicCredentials = Depends(security)):
    correct_username = secrets.compare_digest(credentials.username, config.ADMIN_USERNAME)
    correct_password = secrets.compare_digest(credentials.password, config.ADMIN_PASSWORD)
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def admin_home(username: str = Depends(require_auth)):
    return (Path("admin/static/index.html")).read_text()


@router.get("/api/status")
async def api_status(username: str = Depends(require_auth)):
    store = FeedbackStore()
    return {
        "feedback_count": len(store.get_all()),
        "pending_proposals": len(store.get_pending_proposals()),
    }


@router.get("/api/logs")
async def api_logs(username: str = Depends(require_auth)):
    store = FeedbackStore()
    return store.get_all()


@router.get("/api/proposals")
async def api_proposals(username: str = Depends(require_auth)):
    store = FeedbackStore()
    return store.get_pending_proposals()


@router.post("/api/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: int, username: str = Depends(require_auth)):
    from agent.loop import AtlasAgent
    store = FeedbackStore()
    proposals = store.get_pending_proposals()
    proposal = next((p for p in proposals if p["id"] == proposal_id), None)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found")

    # Append to memory.md
    memory_path = Path("agent/memory.md")
    current = memory_path.read_text(encoding="utf-8")
    entry = f"\n## Heuristic (approved {__import__('datetime').date.today()})\n{proposal['proposed_heuristic']}\n"
    memory_path.write_text(current + entry, encoding="utf-8")

    store.update_proposal_status(proposal_id, "approved")
    return {"status": "approved", "memory_updated": True}


@router.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: int, username: str = Depends(require_auth)):
    store = FeedbackStore()
    store.update_proposal_status(proposal_id, "rejected")
    return {"status": "rejected"}


@router.post("/api/guides/reload")
async def reload_guides(username: str = Depends(require_auth)):
    count = load_all_guides()
    return {"guides_loaded": count}
```

### Step 2: Create `admin/static/index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>A.T.L.A.S. Admin</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; background: #f5f5f5; color: #333; }
    nav { background: #0078d4; color: white; padding: 12px 24px; display: flex; gap: 20px; align-items: center; }
    nav a { color: white; text-decoration: none; font-weight: 500; }
    .container { max-width: 1000px; margin: 32px auto; padding: 0 16px; }
    .card { background: white; border-radius: 8px; padding: 24px; margin-bottom: 16px; box-shadow: 0 1px 3px rgba(0,0,0,0.1); }
    .stat { font-size: 2rem; font-weight: 700; color: #0078d4; }
    .grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(200px, 1fr)); gap: 16px; }
    h1 { font-size: 1.5rem; }
  </style>
</head>
<body>
  <nav>
    <strong>A.T.L.A.S. Admin</strong>
    <a href="/admin/">Dashboard</a>
    <a href="/admin/static/guides.html">Guides</a>
    <a href="/admin/static/logs.html">Logs</a>
    <a href="/admin/static/learning.html">Learning</a>
  </nav>
  <div class="container">
    <h1>Dashboard</h1>
    <div class="grid" id="stats">Loading...</div>
  </div>
  <script>
    fetch('/admin/api/status').then(r => r.json()).then(data => {
      document.getElementById('stats').innerHTML = `
        <div class="card"><div class="stat">${data.feedback_count}</div><p>Total Feedback</p></div>
        <div class="card"><div class="stat">${data.pending_proposals}</div><p>Pending Learning Proposals</p></div>
      `;
    });
  </script>
</body>
</html>
```

### Step 3: Wire admin routes into `main.py`

Add these lines to `main.py` after the existing imports:

```python
from admin.routes import router as admin_router
app.include_router(admin_router)
```

### Step 4: Create placeholder pages for guides, logs, learning

Create `admin/static/guides.html`, `admin/static/logs.html`, `admin/static/learning.html` — each following the same nav + card structure as `index.html`, with fetch calls to `/admin/api/logs`, `/admin/api/proposals`, etc. (You'll flesh these out fully in a polish pass.)

### Step 5: Run all tests

```bash
pytest tests/ -v
```

Expected: All PASS

### Step 6: Commit

```bash
git add admin/ main.py
git commit -m "feat: admin dashboard with HTTP Basic Auth — status, logs, learning proposals"
```

---

## Task 10: Docker Compose + Nginx Deployment

**Files:**
- Create: `Dockerfile`
- Create: `docker-compose.yml`
- Create: `nginx/nginx.conf`
- Create: `.dockerignore`

### Step 1: Create `Dockerfile`

```dockerfile
FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Create ChromaDB persistence directory
RUN mkdir -p knowledge_base/chroma_db learning

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "info"]
```

### Step 2: Create `.dockerignore`

```
__pycache__/
*.pyc
*.pyo
.env
.git
tests/
requirements-dev.txt
knowledge_base/chroma_db/
learning/feedback.db
```

### Step 3: Create `docker-compose.yml`

```yaml
version: "3.9"

services:
  app:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - kb_data:/app/knowledge_base/chroma_db
      - learning_data:/app/learning
      - agent_data:/app/agent
    depends_on:
      - redis
    expose:
      - "8000"

  redis:
    image: redis:7-alpine
    restart: unless-stopped
    volumes:
      - redis_data:/data
    command: redis-server --appendonly yes

  nginx:
    image: nginx:alpine
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/conf.d/default.conf:ro
      - /etc/letsencrypt:/etc/letsencrypt:ro
    depends_on:
      - app

volumes:
  kb_data:
  learning_data:
  agent_data:
  redis_data:
```

### Step 4: Create `nginx/nginx.conf`

```nginx
server {
    listen 80;
    server_name your-domain.com;
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;

    location / {
        proxy_pass http://app:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

### Step 5: Build and test locally

```bash
# Copy and fill .env
cp .env.example .env
# Edit .env with real values

# Build and start
docker-compose up --build

# Verify health endpoint
curl http://localhost:8080/health
# Expected: {"status": "ok", "name": "A.T.L.A.S."}

# Load guides into the container
docker-compose exec app python -m knowledge_base.loader
```

### Step 6: Commit

```bash
git add Dockerfile docker-compose.yml nginx/ .dockerignore
git commit -m "feat: Docker Compose deployment — app + redis + nginx"
```

---

## Task 11: Azure Bot Service Registration (Manual Steps)

> These are manual configuration steps in Azure portal, not code.

### Step 1: Register the bot in Azure

1. Go to [portal.azure.com](https://portal.azure.com)
2. Create resource → search "Azure Bot"
3. Fill in:
   - Bot handle: `atlas-bot`
   - Subscription: your subscription
   - Resource group: `atlas-rg`
   - Pricing tier: F0 (free) for dev, S1 for production
   - App type: Multi-tenant
4. Click Review + Create

### Step 2: Get App ID and Password

1. In the bot resource → Configuration
2. Note the **Microsoft App ID** → add to `.env` as `MICROSOFT_APP_ID`
3. Click "Manage" next to App ID → Certificates & secrets → New client secret
4. Copy the secret value → add to `.env` as `MICROSOFT_APP_PASSWORD`

### Step 3: Set the messaging endpoint

1. In bot resource → Configuration
2. Set Messaging endpoint: `https://your-domain.com/api/messages`
3. Save

### Step 4: Add Microsoft Teams channel

1. In bot resource → Channels → Add a channel → Microsoft Teams
2. Agree to Terms of Service → Save

### Step 5: Test in Bot Framework Emulator (local)

1. Download Bot Framework Emulator: [github.com/microsoft/BotFramework-Emulator](https://github.com/microsoft/BotFramework-Emulator)
2. Connect to: `http://localhost:8000/api/messages`
3. Send a message → verify A.T.L.A.S. responds

---

## Task 12: Cron for Nightly Learning Processor

> Configure cron on the droplet (or in Docker)

### Option A: Host cron (simpler)

SSH into your droplet and add:

```bash
crontab -e
# Add:
0 2 * * * docker exec atlas-app-1 python -m learning.processor >> /var/log/atlas-learning.log 2>&1
```

### Option B: Docker-based cron service

Add to `docker-compose.yml`:

```yaml
  cron:
    build: .
    restart: unless-stopped
    env_file: .env
    volumes:
      - learning_data:/app/learning
      - agent_data:/app/agent
    command: sh -c "while true; do sleep 86400; python -m learning.processor; done"
    depends_on:
      - app
```

---

## Verification Checklist

Run through each of these before considering the system production-ready:

- [ ] `pytest tests/ -v` — all tests pass
- [ ] `docker-compose up --build` — no errors on startup
- [ ] `curl http://localhost:8000/health` → `{"status": "ok", "name": "A.T.L.A.S."}`
- [ ] `python -m knowledge_base.loader` — 5 guides load successfully
- [ ] Bot Framework Emulator: send "how do I clear cookies?" → A.T.L.A.S. responds with guide
- [ ] Bot Framework Emulator: simulate 2 failed attempts → Jira ticket created (check Jira)
- [ ] Admin dashboard: `http://localhost:8000/admin/` with credentials → loads correctly
- [ ] Admin dashboard `/api/proposals` — returns JSON array
- [ ] Approve a proposal → `agent/memory.md` updated, new heuristic visible
- [ ] `python -m learning.processor` — runs without error
- [ ] Deploy to droplet, set DNS, run Certbot for SSL, test Teams channel end-to-end

---

## Droplet Deployment Checklist

```bash
# SSH into DigitalOcean droplet
ssh root@your-droplet-ip

# Install Docker
curl -fsSL https://get.docker.com | sh
apt install docker-compose-plugin -y

# Clone repo and configure
git clone https://github.com/yourname/atlas.git /opt/atlas
cd /opt/atlas
cp .env.example .env
nano .env  # fill in all values

# SSL certificate (replace with your domain)
apt install certbot -y
certbot certonly --standalone -d your-domain.com

# Update nginx.conf with your domain
nano nginx/nginx.conf

# Start
docker-compose up -d

# Load guides
docker-compose exec app python -m knowledge_base.loader

# Check logs
docker-compose logs -f app
```
