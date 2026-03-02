import secrets
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from learning.feedback_store import FeedbackStore
from knowledge_base.loader import load_all_guides
import config

router = APIRouter(prefix="/admin")
security = HTTPBasic()
STATIC_DIR = Path(__file__).resolve().parent / "static"


def require_auth(credentials: HTTPBasicCredentials = Depends(security)) -> str:
    correct_username = secrets.compare_digest(
        credentials.username.encode(), config.ADMIN_USERNAME.encode()
    )
    correct_password = secrets.compare_digest(
        credentials.password.encode(), config.ADMIN_PASSWORD.encode()
    )
    if not (correct_username and correct_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
            headers={"WWW-Authenticate": "Basic"},
        )
    return credentials.username


@router.get("/", response_class=HTMLResponse)
async def admin_home(_: str = Depends(require_auth)):
    return (STATIC_DIR / "index.html").read_text(encoding="utf-8")


@router.get("/guides", response_class=HTMLResponse)
async def admin_guides(_: str = Depends(require_auth)):
    return (STATIC_DIR / "guides.html").read_text(encoding="utf-8")


@router.get("/logs", response_class=HTMLResponse)
async def admin_logs(_: str = Depends(require_auth)):
    return (STATIC_DIR / "logs.html").read_text(encoding="utf-8")


@router.get("/learning", response_class=HTMLResponse)
async def admin_learning(_: str = Depends(require_auth)):
    return (STATIC_DIR / "learning.html").read_text(encoding="utf-8")


# --- API endpoints ---

@router.get("/api/status")
async def api_status(_: str = Depends(require_auth)):
    store = FeedbackStore()
    return {
        "app": "A.T.L.A.S.",
        "version": "1.0.0",
        "feedback_count": len(store.get_all()),
        "pending_proposals": len(store.get_pending_proposals()),
    }


@router.get("/api/logs")
async def api_logs(_: str = Depends(require_auth)):
    store = FeedbackStore()
    return store.get_all()


@router.get("/api/proposals")
async def api_proposals(_: str = Depends(require_auth)):
    store = FeedbackStore()
    return store.get_pending_proposals()


@router.post("/api/proposals/{proposal_id}/approve")
async def approve_proposal(proposal_id: int, _: str = Depends(require_auth)):
    store = FeedbackStore()
    proposals = store.get_pending_proposals()
    proposal = next((p for p in proposals if p["id"] == proposal_id), None)
    if not proposal:
        raise HTTPException(status_code=404, detail="Proposal not found or already reviewed")

    # Append heuristic to memory.md
    memory_path = Path(__file__).resolve().parent.parent / "agent" / "memory.md"
    import datetime
    today = datetime.date.today().isoformat()
    entry = f"\n## Heuristic (approved {today})\n{proposal['proposed_heuristic']}\n"
    current_content = memory_path.read_text(encoding="utf-8") if memory_path.exists() else ""
    memory_path.write_text(current_content + entry, encoding="utf-8")

    store.update_proposal_status(proposal_id, "approved")
    return {"status": "approved", "memory_updated": True, "proposal_id": proposal_id}


@router.post("/api/proposals/{proposal_id}/reject")
async def reject_proposal(proposal_id: int, _: str = Depends(require_auth)):
    store = FeedbackStore()
    store.update_proposal_status(proposal_id, "rejected")
    return {"status": "rejected", "proposal_id": proposal_id}


@router.post("/api/guides/reload")
async def reload_guides(_: str = Depends(require_auth)):
    count = load_all_guides()
    return {"guides_loaded": count}
