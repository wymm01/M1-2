import requests
from datetime import date, timedelta
from firebase_config import get_firestore_client

COLLECTION = "data"


def fetch_recent_rates(target_count: int = 200):
    """최근 target_count 영업일치 USD->KRW 환율을 Frankfurter API에서 가져온다."""
    end_date = date.today()
    # 영업일만 오므로 여유있게 더 넉넉한 기간을 요청한다 (주말/공휴일 제외분 보정)
    start_date = end_date - timedelta(days=int(target_count * 1.6) + 10)

    url = f"https://api.frankfurter.app/{start_date}..{end_date}?from=USD&to=KRW"
    res = requests.get(url, timeout=10)
    res.raise_for_status()
    rates = res.json()["rates"]  # {"2026-01-02": {"KRW": 1320.5}, ...}

    sorted_dates = sorted(rates.keys())
    recent_dates = sorted_dates[-target_count:]  # 최근 target_count개만 사용

    return [
        {"date": d, "value": round(rates[d]["KRW"], 2), "memo": None}
        for d in recent_dates
    ]


def clear_collection(db):
    """기존 data 컬렉션을 비운다 (2024년 샘플 데이터 제거)."""
    docs = db.collection(COLLECTION).stream()
    count = 0
    for doc in docs:
        doc.reference.delete()
        count += 1
    print(f"기존 데이터 {count}개 삭제 완료")


def seed():
    db = get_firestore_client()

    clear_collection(db)

    items = fetch_recent_rates(200)
    print(f"Frankfurter API에서 {len(items)}개 데이터 수신 완료")

    for item in items:
        db.collection(COLLECTION).add(item)

    print(f"Firestore에 {len(items)}개 데이터 업로드 완료")
    print(f"기간: {items[0]['date']} ~ {items[-1]['date']}")


if __name__ == "__main__":
    seed()