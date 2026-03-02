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
