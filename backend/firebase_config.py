import os
import json
import firebase_admin
from firebase_admin import credentials, firestore
from dotenv import load_dotenv

load_dotenv()


def get_firestore_client():
    if not firebase_admin._apps:
        service_account_json = os.getenv("FIREBASE_SERVICE_ACCOUNT_JSON")

        if not service_account_json:
            raise ValueError("FIREBASE_SERVICE_ACCOUNT_JSON이 설정되지 않았습니다.")

        # 상대경로 → 절대경로 변환 ⭐
        if not os.path.isabs(service_account_json):
            # firebase_config.py 위치: backend/
            # JSON 파일 위치: 환율AI비서/ (루트)
            base_dir = os.path.dirname(os.path.abspath(__file__))  # backend 폴더
            root_dir = os.path.dirname(base_dir)                   # 루트 폴더
            filename = service_account_json.lstrip('./')            # 파일명만 추출
            service_account_json = os.path.join(root_dir, filename)

        # 환경변수가 파일 경로인지 확인
        if os.path.exists(service_account_json):
            cred = credentials.Certificate(service_account_json)
        else:
            # 환경변수가 JSON 문자열인 경우
            service_account_info = json.loads(service_account_json)
            cred = credentials.Certificate(service_account_info)

        firebase_admin.initialize_app(cred)

    return firestore.client()