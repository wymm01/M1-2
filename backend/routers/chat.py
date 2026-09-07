from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime
import os
from google import genai
from google.genai import types
from backend.firebase_config import get_firestore_client
from backend.routers.data import get_summary  # summary 함수 재사용

router = APIRouter(prefix="/api/chat", tags=["AI 챗봇"])
db = get_firestore_client()
CONVERSATION_COLLECTION = "conversations"

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))
MODEL_NAME = "gemini-3.6-flash"


class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None


def build_system_prompt(summary: dict) -> str:
    if summary.get("count", 0) == 0:
        return "당신은 환율 데이터를 안내하는 AI 비서입니다. 아직 저장된 데이터가 없다고 안내하세요."

    return (
        "당신은 사용자의 USD 환율 데이터를 알고 있는 AI 비서입니다. "
        "아래 데이터 요약을 참고해서 사용자 질문에 답변하세요.\n\n"
        f"- 데이터 개수: {summary['count']}개\n"
        f"- 기간: {summary['period']['start']} ~ {summary['period']['end']}\n"
        f"- 평균: {summary['average']}\n"
        f"- 최고: {summary['max']}\n"
        f"- 최저: {summary['min']}\n"
        f"- 최근 추세: {summary['recent_trend']}\n\n"
        "위 데이터 범위를 벗어나는 질문에는 모른다고 솔직히 답하세요."
    )


@router.post("/")
def chat(request: ChatRequest):
    # 1. 데이터 요약 조회
    summary = get_summary()
    system_prompt = build_system_prompt(summary)

    # 기존 대화 이어가기 or 새 대화
    if request.conversation_id:
        doc_ref = db.collection(CONVERSATION_COLLECTION).document(request.conversation_id)
        doc = doc_ref.get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail="대화를 찾을 수 없습니다.")
        history = doc.to_dict().get("messages", [])
    else:
        doc_ref = db.collection(CONVERSATION_COLLECTION).document()
        history = []

    # Gemini는 role이 "user"/"model" (OpenAI의 "assistant" 대신 "model")
    contents = []
    for m in history:
        role = "model" if m["role"] == "assistant" else "user"
        contents.append(types.Content(role=role, parts=[types.Part.from_text(text=m["content"])]))
    contents.append(types.Content(role="user", parts=[types.Part.from_text(text=request.message)]))

    # 2~3. 시스템 프롬프트 삽입 + Gemini 호출
    try:
        response = client.models.generate_content(
            model=MODEL_NAME,
            contents=contents,
            config=types.GenerateContentConfig(
                system_instruction=system_prompt,
                max_output_tokens=1024,
                thinking_config=types.ThinkingConfig(thinking_level="low"),
            ),
        )
    except Exception as e:
        raise HTTPException(status_code=502, detail=f"Gemini 호출 실패: {str(e)}")

    ai_reply = response.text

    # 4. 대화 내용 자동 저장 (role은 기존 프로젝트 스키마와 통일: user/assistant)
    updated_messages = history + [
        {"role": "user", "content": request.message},
        {"role": "assistant", "content": ai_reply},
    ]

    if request.conversation_id:
        doc_ref.update({"messages": updated_messages})
    else:
        doc_ref.set({
            "title": request.message[:30],
            "messages": updated_messages,
            "created_at": datetime.utcnow().isoformat(),
        })

    return {
        "conversation_id": doc_ref.id,
        "reply": ai_reply,
        "summary_used": summary,
    }