from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import chat, compare, data, rep, rules

app = FastAPI(title="יועץ הרכב של שטראוס", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (data, compare, chat, rep, rules):
    app.include_router(module.router)


@app.get("/api/health")
def health():
    return {"ok": True}
