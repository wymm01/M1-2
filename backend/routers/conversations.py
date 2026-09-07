from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
from backend.firebase_config import get_firestore_client

router = APIRouter(prefix="/api/conversations", tags=["대화 기록"])
db = get_firestore_client()
COLLECTION = "conversations"


class Message(BaseModel):
    role: str          # "user" 또는 "assistant"
    content: str


class ConversationCreate(BaseModel):
    title: Optional[str] = None
    messages: List[Message]


# ✅ 1. 대화 저장
@router.post("/")
def create_conversation(conversation: ConversationCreate):
    doc_ref = db.collection(COLLECTION).document()
    data = conversation.model_dump(mode="json")
    data["created_at"] = datetime.utcnow().isoformat()
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


# ✅ 2. 대화 목록 조회 (messages는 제외하고 title/개수 정도만 반환 - 목록은 가볍게)
@router.get("/")
def get_all_conversations():
    docs = db.collection(COLLECTION).stream()
    result = []
    for doc in docs:
        d = doc.to_dict()
        result.append({
            "id": doc.id,
            "title": d.get("title"),
            "message_count": len(d.get("messages", [])),
            "created_at": d.get("created_at"),
        })
    return {"count": len(result), "conversations": result}


# ✅ 3. 특정 대화 전체 조회 (불러오기용 - messages 포함)
@router.get("/{conversation_id}")
def get_conversation(conversation_id: str):
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    doc = doc_ref.get()
    if not doc.exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    return {"id": doc.id, **doc.to_dict()}


# ✅ 4. 대화 삭제
@router.delete("/{conversation_id}")
def delete_conversation(conversation_id: str):
    doc_ref = db.collection(COLLECTION).document(conversation_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"id": conversation_id, "deleted": True}