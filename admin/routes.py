from fastapi import APIRouter
router = APIRouter(prefix="/admin")

@router.get("/")
async def admin_placeholder():
    return {"message": "Admin dashboard coming soon"}
