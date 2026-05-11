# Finance Compass Backend

## 🚀 빠른 시작

### 1. .env 파일 생성
```bash
cp .env.example .env
```

### 2. .env 파일 편집
```
GEMINI_API_KEY=여기에_Gemini_API_키_입력
NGROK_TOKEN=여기에_ngrok_토큰_입력
```

### 3. 패키지 설치
```bash
pip install -r requirements.txt
```

### 4. 서버 실행
```bash
python start.py
```

완료! 서버가 시작되면:
- **로컬**: http://localhost:8000
- **공개 URL**: ngrok이 자동으로 생성 (터미널에 출력됨)
- **API 문서**: http://localhost:8000/docs

---

## 📡 API 엔드포인트

### 영수증 인식
```
POST /api/transactions/analyze-receipt
{
  "image_base64": "...",
  "currency": "USD",
  "user_id": "user123"
}
```

### 은행 알림 인식
```
POST /api/transactions/analyze-bank-notification
{
  "notification_text": "스타벅스에서 5,500원 결제",
  "user_id": "user123"
}
```

### 메뉴판 분석
```
POST /api/menu/analyze
{
  "image_base64": "...",
  "currency": "USD"
}
```

### PDF 보고서
```
POST /api/transactions/generate-report
{
  "user_id": "user123",
  "start_date": "2024-01-01",
  "end_date": "2024-01-31"
}
```

### 환율 조회
```
GET /api/rates/
GET /api/rates/USD
```

### 지갑 연결
```
POST /api/wallets/connect
{
  "user_id": "user123",
  "wallet_seed": "sXXXXX...",
  "wallet_name": "My Wallet"
}
```

---

## ⚙️ 데이터베이스
PostgreSQL 불필요 - SQLite 자동 생성 (`finance_compass.db`)
