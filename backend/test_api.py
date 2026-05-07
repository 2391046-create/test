"""
API 테스트 스크립트
"""
import requests
import json
from datetime import datetime

BASE_URL = "http://localhost:8000"


def test_health():
    """헬스 체크 테스트"""
    print("🏥 헬스 체크 테스트...")
    response = requests.get(f"{BASE_URL}/health")
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}\n")
    assert response.status_code == 200


def test_classify_text():
    """텍스트 분류 테스트"""
    print("📝 텍스트 분류 테스트...")
    payload = {
        "text": "[신한카드] 스타벅스 ₩5,500 승인"
    }
    response = requests.post(f"{BASE_URL}/classify", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    assert response.status_code == 200
    assert result["merchant"] is not None
    assert result["amount"] > 0
    assert result["category"] in [
        "food", "transport", "housing", "study", 
        "shopping", "health", "transfer", "other"
    ]
    
    return result


def test_record_transaction(classified_result):
    """거래 기록 테스트"""
    print("💾 거래 기록 테스트...")
    payload = {
        "merchant": classified_result["merchant"],
        "amount": classified_result["amount"],
        "currency": classified_result["currency"],
        "category": classified_result["category"],
        "transaction_date": datetime.utcnow().isoformat(),
        "description": classified_result.get("description"),
        "record_on_blockchain": True
    }
    response = requests.post(f"{BASE_URL}/record", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    assert response.status_code == 200
    assert result["transaction_id"] is not None
    
    return result


def test_get_transactions():
    """거래 조회 테스트"""
    print("📋 거래 조회 테스트...")
    response = requests.get(f"{BASE_URL}/transactions?skip=0&limit=10")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    assert response.status_code == 200
    assert "total" in result
    assert "items" in result


def test_create_budget():
    """예산 설정 테스트"""
    print("💰 예산 설정 테스트...")
    payload = {
        "category": "food",
        "amount": 500000,
        "currency": "KRW",
        "month_year": "2026-05"
    }
    response = requests.post(f"{BASE_URL}/budgets", json=payload)
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    assert response.status_code == 200
    assert result["category"] == "food"
    assert result["amount"] == 500000


def test_get_budget_status():
    """예산 상태 조회 테스트"""
    print("📊 예산 상태 조회 테스트...")
    response = requests.get(f"{BASE_URL}/budgets/2026-05")
    print(f"Status: {response.status_code}")
    result = response.json()
    print(f"Response: {json.dumps(result, indent=2, ensure_ascii=False)}\n")
    
    assert response.status_code == 200
    assert isinstance(result, list)


def test_swagger_docs():
    """Swagger 문서 테스트"""
    print("📚 Swagger 문서 테스트...")
    response = requests.get(f"{BASE_URL}/docs")
    print(f"Status: {response.status_code}")
    assert response.status_code == 200
    print("✅ Swagger UI 접근 가능\n")


def run_all_tests():
    """모든 테스트 실행"""
    print("=" * 60)
    print("Finance Compass Backend API 테스트 시작")
    print("=" * 60 + "\n")
    
    try:
        # 기본 테스트
        test_health()
        test_swagger_docs()
        
        # 분류 및 기록 테스트
        classified = test_classify_text()
        recorded = test_record_transaction(classified)
        
        # 조회 테스트
        test_get_transactions()
        
        # 예산 테스트
        test_create_budget()
        test_get_budget_status()
        
        print("=" * 60)
        print("✅ 모든 테스트 통과!")
        print("=" * 60)
        
    except AssertionError as e:
        print(f"\n❌ 테스트 실패: {str(e)}")
    except requests.exceptions.ConnectionError:
        print("\n❌ 서버에 연결할 수 없습니다.")
        print("서버가 실행 중인지 확인하세요: python main.py")
    except Exception as e:
        print(f"\n❌ 예상치 못한 오류: {str(e)}")


if __name__ == "__main__":
    run_all_tests()
