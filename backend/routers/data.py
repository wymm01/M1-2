from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import Optional
from datetime import date as date_type
from statistics import mean
from backend.firebase_config import get_firestore_client

router = APIRouter(prefix="/api/data", tags=["환율 데이터"])
db = get_firestore_client()
COLLECTION = "data"


class ExchangeRateItem(BaseModel):
    date: date_type
    value: float
    memo: Optional[str] = None


# ✅ 1. 데이터 추가
@router.post("/")
def create_data(item: ExchangeRateItem):
    doc_ref = db.collection(COLLECTION).document()
    data = item.model_dump(mode="json")
    doc_ref.set(data)
    return {"id": doc_ref.id, **data}


# ✅ 2. 전체 데이터 조회
@router.get("/")
def get_all_data():
    docs = db.collection(COLLECTION).stream()
    result = [{"id": doc.id, **doc.to_dict()} for doc in docs]
    return {"count": len(result), "data": result}


# ✅ 3. 요약 정보 (반드시 {id} 라우트보다 위에 선언!)
@router.get("/summary")
def get_summary():
    docs = list(db.collection(COLLECTION).stream())
    values = [doc.to_dict()["value"] for doc in docs]
    dates = sorted([doc.to_dict()["date"] for doc in docs])

    if not values:
        return {"count": 0, "message": "데이터가 없습니다."}

    trend = "유지"
    if len(values) >= 2:
        recent, prev = values[-1], values[-2]
        trend = "상승" if recent > prev else "하락" if recent < prev else "유지"

    return {
        "count": len(values),
        "period": {"start": dates[0], "end": dates[-1]},
        "average": round(mean(values), 2),
        "max": max(values),
        "min": min(values),
        "recent_trend": trend,
    }


# ✅ 4. 데이터 수정
@router.put("/{item_id}")
def update_data(item_id: str, item: ExchangeRateItem):
    doc_ref = db.collection(COLLECTION).document(item_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    doc_ref.update(item.model_dump(mode="json"))
    return {"id": item_id, **item.model_dump(mode="json")}


# ✅ 5. 데이터 삭제
@router.delete("/{item_id}")
def delete_data(item_id: str):
    doc_ref = db.collection(COLLECTION).document(item_id)
    if not doc_ref.get().exists:
        raise HTTPException(status_code=404, detail="데이터를 찾을 수 없습니다.")
    doc_ref.delete()
    return {"id": item_id, "deleted": True}