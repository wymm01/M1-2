from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from backend.routers import data, conversations, chat

app = FastAPI(title="환율 AI 비서")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(data.router)
app.include_router(conversations.router)
app.include_router(chat.router)


@app.get("/")
def root():
    return {"message": "환율 AI 비서 백엔드가 실행 중입니다."}


@app.get("/api/health")
def health():
    return {"status": "ok"}