# Finance Compass Backend

유학생 재정 관리 및 XRPL 블록체인 연동 FastAPI 백엔드 서버

## 🚀 주요 기능

### 1. Gemini AI 연동
- **결제 텍스트 분석**: 결제 알림을 자동으로 분석하여 상호명, 금액, 카테고리 추출
- **영수증 OCR**: 영수증 이미지를 인식하여 자동 분류
- **신뢰도 점수**: 분류 결과의 정확도를 0-1 사이의 점수로 반환

### 2. XRPL 블록체인 연동
- **지출 기록**: 분류된 지출 내역을 XRPL 네트워크에 트랜잭션으로 기록
- **Memo 필드**: 지출 정보를 JSON 형식으로 XRPL Memo에 저장
- **트랜잭션 추적**: XRPL 블록체인에 기록된 트랜잭션 조회 및 검증

### 3. 데이터베이스
- **PostgreSQL**: 사용자, 거래, 예산 정보 저장
- **관계형 모델**: 사용자-거래-예산 간의 관계 설정
- **XRPL 연동**: 블록체인 트랜잭션 정보 저장

### 4. REST API
- **분류 API** (`/classify`): 결제 내역 자동 분류
- **기록 API** (`/record`): 거래 기록 및 XRPL 저장
- **조회 API** (`/transactions`): 거래 내역 조회
- **예산 API** (`/budgets`): 예산 설정 및 상태 조회
- **XRPL API** (`/xrpl/*`): 블록체인 트랜잭션 조회

## 📁 프로젝트 구조

```
backend/
├── main.py                 # FastAPI 메인 애플리케이션
├── config.py              # 환경 설정 관리
├── models.py              # SQLAlchemy ORM 모델
├── schemas.py             # Pydantic 스키마 (요청/응답)
├── database.py            # 데이터베이스 연결 및 세션
├── gemini_service.py      # Gemini AI 연동 모듈
├── xrpl_service.py        # XRPL 블록체인 연동 모듈
├── requirements.txt       # Python 의존성
└── README.md             # 이 파일
```

## 🔧 설치 및 실행

### 1. 환경 설정

```bash
# 가상 환경 생성
python -m venv venv
source venv/bin/activate  # Linux/Mac
# 또는
venv\Scripts\activate  # Windows

# 의존성 설치
pip install -r requirements.txt
```

### 2. 환경 변수 설정

`.env` 파일을 생성하고 다음 정보를 입력합니다:

```env
# 데이터베이스
DATABASE_URL=postgresql://user:password@localhost:5432/finance_compass

# Gemini AI
GEMINI_API_KEY=your_gemini_api_key_here

# XRPL
XRPL_NETWORK_URL=https://s.altnet.rippletest.net:51234
XRPL_WALLET_SEED=your_xrpl_wallet_seed_here
XRPL_ACCOUNT_ADDRESS=your_xrpl_account_address_here

# 서버
DEBUG=True
SECRET_KEY=your_secret_key_for_jwt_here
```

### 3. 데이터베이스 초기화

```bash
# PostgreSQL 설치 및 실행
# 데이터베이스 생성
createdb finance_compass

# 테이블 생성은 애플리케이션 시작 시 자동으로 수행됩니다
```

### 4. 서버 실행

```bash
python main.py
# 또는
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

서버는 `http://localhost:8000`에서 실행됩니다.

## 📚 API 명세

### 분류 API

**요청:**
```bash
POST /classify
Content-Type: application/json

{
  "text": "[신한카드] 스타벅스 ₩5,500 승인"
}
```

**응답:**
```json
{
  "merchant": "스타벅스",
  "amount": 5500,
  "currency": "KRW",
  "category": "food",
  "confidence": 0.95,
  "description": "커피 음료",
  "raw_analysis": "AI 분석 결과..."
}
```

### 거래 기록 API

**요청:**
```bash
POST /record
Content-Type: application/json

{
  "merchant": "스타벅스",
  "amount": 5500,
  "currency": "KRW",
  "category": "food",
  "transaction_date": "2026-05-06T14:30:00",
  "description": "아메리카노",
  "record_on_blockchain": true
}
```

**응답:**
```json
{
  "transaction_id": 1,
  "merchant": "스타벅스",
  "amount": 5500,
  "category": "food",
  "xrpl_tx_hash": "E3FE6EA3D48F0C2B639448020EA4F03D4F4F8FFDB243A852A0F59177921B4879",
  "xrpl_memo": "{\"type\": \"expense\", \"merchant\": \"스타벅스\", ...}",
  "is_recorded_on_blockchain": true,
  "message": "거래가 기록되었습니다 (ID: 1)"
}
```

### 거래 조회 API

**요청:**
```bash
GET /transactions?skip=0&limit=20&category=food
```

**응답:**
```json
{
  "total": 42,
  "items": [
    {
      "id": 1,
      "user_id": 1,
      "merchant": "스타벅스",
      "amount": 5500,
      "currency": "KRW",
      "category": "food",
      "description": "아메리카노",
      "transaction_date": "2026-05-06T14:30:00",
      "created_at": "2026-05-06T14:35:00",
      "xrpl_tx_hash": "E3FE...",
      "is_recorded_on_blockchain": true,
      "confidence": 0.95
    }
  ]
}
```

### 예산 설정 API

**요청:**
```bash
POST /budgets
Content-Type: application/json

{
  "category": "food",
  "amount": 500000,
  "currency": "KRW",
  "month_year": "2026-05"
}
```

**응답:**
```json
{
  "id": 1,
  "category": "food",
  "amount": 500000,
  "currency": "KRW",
  "month_year": "2026-05",
  "created_at": "2026-05-06T14:35:00"
}
```

### 예산 상태 조회 API

**요청:**
```bash
GET /budgets/2026-05
```

**응답:**
```json
[
  {
    "category": "food",
    "budget_amount": 500000,
    "spent_amount": 18300,
    "remaining_amount": 481700,
    "percentage_used": 3.66,
    "status": "under"
  },
  {
    "category": "transport",
    "budget_amount": 100000,
    "spent_amount": 9250,
    "remaining_amount": 90750,
    "percentage_used": 9.25,
    "status": "under"
  }
]
```

### XRPL 트랜잭션 조회 API

**요청:**
```bash
GET /xrpl/transactions/E3FE6EA3D48F0C2B639448020EA4F03D4F4F8FFDB243A852A0F59177921B4879
```

**응답:**
```json
{
  "success": true,
  "status": "confirmed",
  "ledger_index": 12345678,
  "timestamp": "2026-05-06T14:35:00",
  "hash": "E3FE6EA3D48F0C2B639448020EA4F03D4F4F8FFDB243A852A0F59177921B4879",
  "account": "rN7n7otQDd6FczFgLdlqtyMVrn3Rqq5Qx",
  "destination": "rN7n7otQDd6FczFgLdlqtyMVrn3Rqq5Qx",
  "amount": "1000"
}
```

## 🔐 보안

### API 키 관리
- Gemini API 키와 XRPL 지갑 시드는 환경 변수로 관리됩니다
- `.env` 파일은 `.gitignore`에 포함되어야 합니다
- 프로덕션 환경에서는 AWS Secrets Manager, HashiCorp Vault 등을 사용하세요

### XRPL 지갑 보안
- 테스트넷에서는 테스트 계정을 사용하세요
- 메인넷 사용 시 하드웨어 지갑 또는 안전한 키 관리 솔루션을 사용하세요
- 지갑 시드는 절대 코드에 하드코딩하면 안 됩니다

## 📊 데이터 흐름

```
프론트엔드 (React Native)
    ↓
[분류 요청] → Gemini AI 분석 → 분류 결과 반환
    ↓
[기록 요청] → 데이터베이스 저장 → XRPL 트랜잭션 생성
    ↓
XRPL 블록체인 (Memo에 지출 정보 저장)
    ↓
[조회 요청] → 데이터베이스 쿼리 → JSON 응답
    ↓
프론트엔드 (Chart.js 시각화)
```

## 🧪 테스트

```bash
# 헬스 체크
curl http://localhost:8000/health

# 분류 테스트
curl -X POST http://localhost:8000/classify \
  -H "Content-Type: application/json" \
  -d '{"text": "[신한카드] 스타벅스 ₩5,500 승인"}'

# API 문서
http://localhost:8000/docs (Swagger UI)
http://localhost:8000/redoc (ReDoc)
```

## 🚀 배포

### Docker 배포

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Heroku 배포

```bash
heroku create finance-compass-backend
git push heroku main
heroku config:set DATABASE_URL=postgresql://...
heroku config:set GEMINI_API_KEY=...
heroku config:set XRPL_WALLET_SEED=...
```

## 📝 라이선스

MIT License

## 👥 기여

Pull Request를 환영합니다!

## 📞 지원

문제가 발생하면 GitHub Issues에 보고해주세요.
