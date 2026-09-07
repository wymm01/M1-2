# -*- coding: utf-8 -*-
# backend/seed_data.py
import os
import json
import random
from datetime import datetime, timedelta
from firebase_config import get_firestore_client

def generate_usd_krw_data(num_points=200):
    """
    미국 달러 환율(USD/KRW) 시계열 데이터 200개 생성
    2024-01-01부터 시작하는 일별 데이터
    """
    data_points = []
    
    # 실제 환율과 유사한 시작값 설정
    base_rate = 1320.0
    current_rate = base_rate
    start_date = datetime(2024, 1, 1)
    
    for i in range(num_points):
        # 랜덤 변동폭 (-8 ~ +8원)
        change = random.uniform(-8, 8)
        # 트렌드 반영 (완만한 상승 후 하락)
        if i < 100:
            trend = 0.3
        else:
            trend = -0.2
        
        current_rate = round(current_rate + change + trend, 2)
        # 현실적인 범위 유지 (1250 ~ 1450)
        current_rate = max(1250.0, min(1450.0, current_rate))
        
        date = start_date + timedelta(days=i)
        
        data_points.append({
            "date": date.strftime("%Y-%m-%d"),
            "value": current_rate,
            "memo": f"USD/KRW 환율 {date.strftime('%Y-%m-%d')}"
        })
    
    return data_points


def seed_firestore():
    """Firestore의 data 컬렉션에 환율 데이터 200개 업로드"""
    db = get_firestore_client()
    collection_ref = db.collection("data")
    
    # 기존 데이터 확인
    existing = list(collection_ref.limit(1).stream())
    if existing:
        print("⚠️  이미 데이터가 존재합니다. 업로드를 건너뜁니다.")
        print("   기존 데이터를 삭제하고 싶으면 Firestore 콘솔에서 직접 삭제하세요.")
        return
    
    print("📊 환율 데이터 200개 생성 중...")
    data_points = generate_usd_krw_data(200)
    
    print("🔥 Firestore에 업로드 중...")
    for i, point in enumerate(data_points):
        collection_ref.add(point)
        if (i + 1) % 20 == 0:
            print(f"   {i + 1}/200 완료...")
    
    print("✅ 200개 데이터 업로드 완료!")
    
    # 업로드 결과 확인
    total = len(list(collection_ref.stream()))
    print(f"📌 Firestore 'data' 컬렉션 총 문서 수: {total}개")


if __name__ == "__main__":
    seed_firestore()